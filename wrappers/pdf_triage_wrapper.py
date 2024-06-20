import openai
import pymupdf
from autogen import register_function
from autogen.agentchat import ChatResult, ConversableAgent, UserProxyAgent
from functools import partial
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from typing import Dict, List, Optional


class PdfTriageWrapper(object):

    def __init__(self, config_list: List[Dict], pdf_path: Optional[str]) -> None:
        self.pdf_path = pdf_path

        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            system_message="You are a human user. When you are satisfied with the answer, reply with TERMINATE.",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
        )
        self.pdf_parser = ConversableAgent(
            name="pdf_parser",
            system_message="""
            You can use the following functions to help you generate the answer:
            
            1. fetch_page(page_number) to retrieve the contents of a page from the PDF.
            2. fetch_section(section) to retrieve the contents of a section from the PDF.
            3. retrieve(query) to answer a general question about the PDF contents.
            """,
            human_input_mode="NEVER",
            is_termination_msg=self.is_termination_message,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
        )

        openai.api_key = config_list[0]["api_key"]
        openai.api_version = config_list[0]["model"]

        vector_index = self.get_vector_index(pdf_path)

        register_function(
            partial(self.fetch_page, pdf_path=pdf_path),
            caller=self.pdf_parser,
            executor=self.user_proxy,
            name="fetch_page",
            description="Execute fetch_page(page_number) to retrieve the contents of a page.",
        )
        register_function(
            partial(self.fetch_section, vector_index=vector_index),
            caller=self.pdf_parser,
            executor=self.user_proxy,
            name="fetch_section",
            description="Execute fetch_section(section) to retrieve the contents of a section.",
        )
        register_function(
            partial(self.retrieve, vector_index=vector_index),
            caller=self.pdf_parser,
            executor=self.user_proxy,
            name="retrieve",
            description="Execute retrieve(query) to retrieve an answer for a given query.",
        )

    @staticmethod
    def is_termination_message(message: Dict) -> bool:
        return "TERMINATE" in message['content']

    @staticmethod
    def get_vector_index(pdf_path: Optional[str]) -> VectorStoreIndex:
        index_documents = SimpleDirectoryReader(
            input_files=([pdf_path] if pdf_path is not None else [])
        ).load_data()
        return VectorStoreIndex.from_documents(index_documents)

    @staticmethod
    def fetch_page(pdf_path: Optional[str], page_number: int) -> str:
        if pdf_path is None:
            return ""

        document = pymupdf.open(pdf_path)
        page = document.load_page(page_number - 1)
        return page.get_text()

    @staticmethod
    def query_index(vector_index: VectorStoreIndex, query: str) -> str:
        query_engine = vector_index.as_query_engine()
        response = query_engine.query(query)
        return str(response)

    @staticmethod
    def fetch_section(vector_index: VectorStoreIndex, section: str) -> str:
        return PdfTriageWrapper.query_index(
            vector_index,
            f"Get me the contexts of the section {section}.",
        )

    @staticmethod
    def retrieve(vector_index: VectorStoreIndex, query: str) -> str:
        return PdfTriageWrapper.query_index(
            vector_index,
            f"Provide the most relevant context for the following query: \"{query}\"",
        )

    def initiate_chat(self, user_prompt: str) -> ChatResult:
        self.pdf_parser.reset()

        prompt = user_prompt if self.pdf_path is None else f"""
            Using the attached PDF, answer the following question:

            {user_prompt}
            """

        return self.user_proxy.initiate_chat(
            self.pdf_parser,
            message=prompt,
        )

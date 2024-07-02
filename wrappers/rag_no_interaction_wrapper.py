import chromadb
from autogen.agentchat import ChatResult
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from typing import Dict, List


class RagNoInteractionWrapper(object):
    CORPUS_FILE = "https://huggingface.co/datasets/thinkall/NaturalQuestionsQA/resolve/main/corpus.txt"

    CUSTOM_PROMPT = """You're a retrieve augmented chatbot. You answer user's questions based on your own knowledge and the
    context provided by the user.
    If you can't answer the question with or without the current context, you should reply exactly `I don’t know`.
    You must give as short an answer as possible.

    User's question is: {input_question}

    Context is: {input_context}
    """

    def __init__(self, config_list: List[Dict], corpus_file=CORPUS_FILE) -> None:
        self.assistant = RetrieveAssistantAgent(
            name="assistant",
            system_message="You are a helpful assistant.",
            llm_config={
                "seed": 42,
                "config_list": config_list,
            },
        )
        self.rag_proxy_agent = RetrieveUserProxyAgent(
            name="rag_proxy_agent",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            retrieve_config={
                "task": "qa",
                "docs_path": corpus_file,
                "chunk_token_size": 2000,
                "model": config_list[0]["model"],
                "client": chromadb.PersistentClient(path="/tmp/chromadb"),
                "collection_name": "natural-questions",
                "chunk_mode": "one_line",
                "embedding_model": "all-MiniLM-L6-v2",
                "get_or_create": True,
                "customized_prompt": self.CUSTOM_PROMPT,
            },
        )

    def retrieve(self, question: str) -> ChatResult:
        self.assistant.reset()
        return self.rag_proxy_agent.initiate_chat(
            self.assistant,
            message=self.rag_proxy_agent.message_generator,
            problem=question,
            max_turns=10
        )

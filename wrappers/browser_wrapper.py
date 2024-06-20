from autogen import ChatResult, ConversableAgent, UserProxyAgent, register_function
from functools import partial
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from typing import Dict, List
from webdriver_manager.chrome import ChromeDriverManager
from xvfbwrapper import Xvfb


class BrowserWrapper(object):
    GSEARCH_CUSTOM_SEARCH_ID: str = "15c5c6f98a3d246ca"
    MAX_TOKENS: int = 10000

    def __init__(self, config_list: List[Dict], gsearch_api_key: str) -> None:
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            system_message="""
                You are a human user.
                When you are satisfied with the answer, reply with TERMINATE.
                """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
        )
        self.web_retriever = self.get_web_retriever(config_list)

        self.register_functions(self.user_proxy, self.web_retriever, gsearch_api_key)

    @staticmethod
    def get_web_retriever(config_list: List[Dict]) -> ConversableAgent:
        return ConversableAgent(
            name="web_retriever",
            system_message="""
                You can use the following functions to help you generate the answer:

                1. search(query) to retrieve the context of a question using Google Search.
                2. open(url) to open a specific URL address if provided by the user.
                """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            is_termination_msg=BrowserWrapper.is_termination_message,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
        )

    @staticmethod
    def register_functions(
            user_proxy: UserProxyAgent,
            web_retriever: ConversableAgent,
            gsearch_api_key: str,
    ) -> None:
        register_function(
            partial(BrowserWrapper.search, gsearch_api_key=gsearch_api_key),
            caller=web_retriever,
            executor=user_proxy,
            name="search",
            description="Execute fetch_page(page_number) to retrieve the contents of a page.",
        )

        register_function(
            BrowserWrapper.open,
            caller=web_retriever,
            executor=user_proxy,
            name="open",
            description="Execute open(url) to open a specific web page and retrieve its contents.",
        )

    @staticmethod
    def is_termination_message(message: Dict) -> bool:
        return "TERMINATE" in message['content']

    @staticmethod
    def search(gsearch_api_key: str, query: str) -> str:
        service = build("customsearch", "v1", developerKey=gsearch_api_key)

        results = service.cse().list(
            q=query, cx=BrowserWrapper.GSEARCH_CUSTOM_SEARCH_ID, num=10
        ).execute()

        return '\n'.join([
            f"""
                Search result #{i}
                Title: {result["title"]}
                Snippet: {result["snippet"]}
                Link: {result["link"]}
    
                """
            for i, result in enumerate(results["items"])
        ])

    @staticmethod
    def open(url: str) -> str:
        with Xvfb(width=1920, height=1080):
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--headless')

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            try:
                driver.get(url)
                body = driver.find_element(By.TAG_NAME, "body")
                # The responses can be lengthy, truncating them here to ensure we don't overrun the limits
                content = body.text[:BrowserWrapper.MAX_TOKENS]
                driver.quit()
            except Exception as e:
                content = ""

        return content

    def initiate_chat(self, user_prompt: str) -> ChatResult:
        self.web_retriever.reset()

        return self.user_proxy.initiate_chat(
            self.web_retriever,
            message=user_prompt,
        )

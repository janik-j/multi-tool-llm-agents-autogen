import autogen
from PIL import Image
from autogen import ChatResult, ConversableAgent
from typing import Dict, List, Optional, Tuple
from wrappers.browser_wrapper import BrowserWrapper
from wrappers.calculator_wrapper import CalculatorWrapper
from wrappers.chat_wrapper_mixin import ChatWrapperMixin
from wrappers.dalle_wrapper import DalleWrapper
from wrappers.multimodal_wrapper import MultimodalWrapper
from wrappers.pdf_triage_wrapper import PdfTriageWrapper
from wrappers.coding_wrapper import CodingWrapper


class OverarchingWrapper(ChatWrapperMixin):
    agents: Dict[str, ConversableAgent] = {}
    dalle: Optional[ConversableAgent] = None
    image_path: Optional[str] = None
    is_pdf_attached: bool = False

    def __init__(self, config_list: List[Dict]) -> None:
        self.config_list = config_list

        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            system_message="""
                You are a human user.
                If the question has been answered, reply with TERMINATE.
                If the request was to generate an image and the image was generated, reply with TERMINATE.
                """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": self.config_list},
        )
        self.agents[self.user_proxy.name] = self.user_proxy

    def add_custom_agent(self, agent_name: str, system_message: str) -> None:
        agent = autogen.AssistantAgent(
            name=agent_name,
            system_message=system_message,
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": self.config_list},
        )
        self.agents[agent.name] = agent

    def remove_custom_agent(self, agent_name: str) -> None:
        self.agents.pop(agent_name, None)

    def add_calculator(self) -> None:
        calculator_agent = CalculatorWrapper.get_calculator(self.config_list)
        self.agents[CalculatorWrapper.AGENT_NAME] = calculator_agent
        CalculatorWrapper.register_functions(self.user_proxy, calculator_agent)

    def remove_calculator(self) -> None:
        self.agents.pop(CalculatorWrapper.AGENT_NAME, None)

    def add_dalle(self) -> None:
        api_key = self.config_list[0]["api_key"]

        self.dalle = DalleWrapper.get_dalle_agent(
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": self.config_list},
            gpt_vision_config={
                "config_list": [{"model": "gpt-4-vision-preview", "api_key": api_key}],
                "timeout": 120,
                "temperature": 0.7,
                "seed": 7,
            },
            dalle_config={
                "config_list": [{"model": "dall-e-3", "api_key": api_key}],
                "timeout": 120,
                "temperature": 0.7,
                "seed": 7,
            },
        )
        self.agents[DalleWrapper.AGENT_NAME] = self.dalle

        critic_agent = DalleWrapper.get_dalle_critic_agent(
            {"cache_seed": None, "seed": 7, "temperature": 0, "config_list": self.config_list}
        )
        self.agents[DalleWrapper.CRITIC_AGENT_NAME] = critic_agent

    def remove_dalle(self) -> None:
        self.dalle = None
        self.agents.pop(DalleWrapper.AGENT_NAME, None)
        self.agents.pop(DalleWrapper.CRITIC_AGENT_NAME, None)

    def add_web_retriever(self, gsearch_api_key: str) -> None:
        web_retriever_agent = BrowserWrapper.get_web_retriever(self.config_list)
        self.agents[BrowserWrapper.AGENT_NAME] = web_retriever_agent
        BrowserWrapper.register_functions(self.user_proxy, web_retriever_agent, gsearch_api_key)

    def remove_web_retriever(self) -> None:
        self.agents.pop(BrowserWrapper.AGENT_NAME, None)

    def add_image_explainer(self, image_path: str) -> None:
        self.image_path = image_path

        image_explainer_agent = MultimodalWrapper.get_image_explainer(
            [{"cache_seed": None, "seed": 7, "model": "gpt-4o", "api_key": self.config_list[0]["api_key"]}]
        )
        self.agents[MultimodalWrapper.AGENT_NAME] = image_explainer_agent

    def remove_image_explainer(self) -> None:
        self.image_path = None
        self.agents.pop(MultimodalWrapper.AGENT_NAME, None)

    def add_pdf_parser(self, pdf_path: str) -> None:
        self.is_pdf_attached = True

        pdf_parser_agent = PdfTriageWrapper.get_pdf_parser(self.config_list)
        self.agents[PdfTriageWrapper.AGENT_NAME] = pdf_parser_agent
        PdfTriageWrapper.register_functions(
            self.user_proxy,
            pdf_parser_agent,
            pdf_path,
            self.config_list[0]["api_key"],
            self.config_list[0]["model"],
        )

    def remove_pdf_parser(self) -> None:
        self.is_pdf_attached = False
        self.agents.pop(PdfTriageWrapper.AGENT_NAME, None)

    def add_coding(self) -> None:
        coding_agent = CodingWrapper.get_coding_agent(self.config_list)
        safeguard_agent = CodingWrapper.get_safeguard_agent(self.config_list)
        self.agents[CodingWrapper.AGENT_NAME] = coding_agent
        self.agents[CodingWrapper.SAFEGUARD_NAME] = safeguard_agent
        CodingWrapper.register_functions(self.user_proxy, safeguard_agent)

    def remove_coding(self) -> None:
        self.agents.pop(CodingWrapper.AGENT_NAME, None)
        self.agents.pop(CodingWrapper.SAFEGUARD_NAME, None)


    def initiate_chat(self, user_prompt: str) -> Tuple[ChatResult, List[Image.Image]]:

        agents = self.agents.values()
        group_chat = autogen.GroupChat(
            agents=agents,
            messages=[],
            max_round=20,
            send_introductions=True,
            allow_repeat_speaker=False,
        )
        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            system_message="""
                        You are a group chat manager.
                        When asked a question, aim to select the smallest possible set of speakers to answer.
                        If the question has been answered, reply with TERMINATE.
                        """,
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": self.config_list},
        )

        for agent in agents:
            agent.reset()

        self.register_replies_callback([*agents])

        prompt = f"""
            Answer the following question:
            
            {user_prompt}
            
            """
        if self.image_path is not None:
            prompt += f"You can use the attached image (<img {self.image_path}>) to get context.\n"
        if self.is_pdf_attached is True:
            prompt += f"You can use the attached PDF to get context.\n"

        result = self.user_proxy.initiate_chat(
            manager,
            message=prompt,
        )

        if self.dalle is None:
            return result, []
        else:
            return result, DalleWrapper.extract_images(self.dalle, manager)

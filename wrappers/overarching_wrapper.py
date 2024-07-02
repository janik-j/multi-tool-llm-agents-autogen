import autogen
from typing import Dict, List, Optional
from wrappers.browser_wrapper import BrowserWrapper
from wrappers.calculator_wrapper import CalculatorWrapper
from wrappers.chat_wrapper_mixin import ChatWrapperMixin
from wrappers.multimodal_wrapper import MultimodalWrapper
from wrappers.pdf_triage_wrapper import PdfTriageWrapper
from wrappers.dalle_wrapper import DalleWrapper


class OverarchingWrapper(ChatWrapperMixin):

    def __init__(
            self,
            enabled_agents: Dict[str, bool],
            config_list: List[Dict],
            gpt_vision_config : List[Dict],
            dalle_config : List[Dict],
            image_path: Optional[str],
            pdf_path: Optional[str],
            gsearch_api_key: str,
    ) -> None:
        self.image_path = image_path
        self.pdf_path = pdf_path
        self.tool_avatar = None
        self.llm_config = {"cache_seed": None, "temperature": 0, "config_list": config_list}

        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            system_message="""
                You are a human user.
                If the question has been answered, reply with TERMINATE.
                """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            llm_config=self.llm_config,
        )

        self.chatbot = autogen.AssistantAgent(
            name="chatbot",
            system_message="""
                You are a chatbot, you can answer text queries.
                In case no other agents can answer, you should step in.
                """,
            llm_config=self.llm_config,
        )
        self.web_retriever = BrowserWrapper.get_web_retriever(config_list)
        BrowserWrapper.register_functions(self.user_proxy, self.web_retriever, gsearch_api_key)
        self.calculator = CalculatorWrapper.get_calculator(config_list)
        CalculatorWrapper.register_functions(self.user_proxy, self.calculator)
        self.dalle = DalleWrapper.get_dalle_agent(self.llm_config, gpt_vision_config, dalle_config)

        self.agents = [self.user_proxy]
        if enabled_agents["chatbot"]:
            self.agents.append(self.chatbot)
        if enabled_agents["web_retriever"]:
            self.agents.append(self.web_retriever)
        if enabled_agents["calculator"]:
            self.agents.append(self.calculator)
        if enabled_agents["dalle"]:
            self.agents.append(self.dalle)

        if enabled_agents["image_explainer"] and image_path is not None:
            self.image_explainer = MultimodalWrapper.get_image_explainer(config_list)
            self.agents.append(self.image_explainer)

        if enabled_agents["pdf_parser"] and pdf_path is not None:
            self.pdf_parser = PdfTriageWrapper.get_pdf_parser(config_list)
            PdfTriageWrapper.register_functions(
                self.user_proxy,
                self.pdf_parser,
                pdf_path,
                config_list[0]["api_key"],
                config_list[0]["model"],
            )
            self.agents.append(self.pdf_parser)

        self.groupchat = autogen.GroupChat(
            agents=self.agents,
            messages=[],
            max_round=20,
            send_introductions=True,
            allow_repeat_speaker=False,
        )
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            system_message="""
                You are a group chat manager.
                If the question has been answered, reply with TERMINATE.
                """,
            llm_config=self.llm_config,
        )

    def add_agent(self, agent_name: str, system_message: str) -> None:
        self.agents.append(
            autogen.AssistantAgent(
                name=agent_name,
                system_message=system_message,
                llm_config=self.llm_config,
            )
        )

    def initiate_chat(self, user_prompt: str) -> None:
        self.groupchat.reset()
        self.manager.reset()

        for agent in self.agents:
            agent.reset()

        self.register_replies_callback([*self.agents])

        prompt = f"""
            Answer the following question:
            
            {user_prompt}
            
            """
        if self.image_path is not None:
            prompt += f"You can use the attached image (<img {self.image_path}>) to get context.\n"
        if self.pdf_path is not None:
            prompt += f"You can use the attached PDF to get context.\n"

        result = self.user_proxy.initiate_chat(
            self.manager,
            message=prompt,
        )
        return result, DalleWrapper.extract_images(self.dalle, self.manager)

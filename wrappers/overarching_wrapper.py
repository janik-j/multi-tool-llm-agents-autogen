import autogen
from typing import Dict, List, Optional
from wrappers.calculator_wrapper import CalculatorWrapper
from wrappers.browser_wrapper import BrowserWrapper
from wrappers.multimodal_wrapper import MultimodalWrapper
from wrappers.pdf_triage_wrapper import PdfTriageWrapper
from wrappers.dalle_wrapper import DalleWrapper
import streamlit as st

class OverarchingWrapper(object):

    def __init__(
            self,
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
        llm_config = {"cache_seed": None, "temperature": 0, "config_list": config_list}

        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            system_message="""
                You are a human user.
                If the question has been answered, reply with TERMINATE.
                """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            llm_config=llm_config,
        )

        self.chatbot = autogen.AssistantAgent(
            name="chatbot",
            system_message="""
                You are a chatbot, you can answer text queries.
                In case no other agents can answer, you should step in.
                """,
            llm_config=llm_config,
        )
        self.web_retriever = BrowserWrapper.get_web_retriever(config_list)
        BrowserWrapper.register_functions(self.user_proxy, self.web_retriever, gsearch_api_key)
        self.calculator = CalculatorWrapper.get_calculator(config_list)
        CalculatorWrapper.register_functions(self.user_proxy, self.calculator)
        self.dalle = DalleWrapper.get_dalle_agent(llm_config, gpt_vision_config, dalle_config)
        


        def print_messages(recipient, messages, sender, config):
            print(f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {messages[-1]}")
            user = messages[-1]['name']
            content = messages[-1]['content']
            tool_calls = messages[-1].get('tool_calls', [])
            user_avatar = avatar[user]

            for call in tool_calls:
                function_name = call['function']['name']
                arguments = call['function']['arguments']
                content += f"\nFunction call: \"{function_name}\" with arguments {arguments}"
                self.tool_avatar = avatar[user]

            if "tool_responses" in messages[-1]:
                st.chat_message(user, avatar=self.tool_avatar).write(content)
            else:
                st.chat_message(user, avatar=user_avatar).write(content)

        
            return False, None  # required to ensure the agent communication flow continues

        # Define avatars for each agent: logos from https://icons8.com/
        avatar = {"user_proxy" :"https://cdn-icons-png.flaticon.com/512/4333/4333609.png", 
                  "chatbot":"https://img.icons8.com/?size=100&id=GBu1KXnCZZ8j&format=png&color=000000", 
                  "web_retriever":"https://img.icons8.com/?size=100&id=TfgcKLCFPMgk&format=png&color=000000", 
                  "calculator":"https://img.icons8.com/?size=100&id=qrOXrfUDKkOX&format=png&color=000000", 
                  "dalle":"https://img.icons8.com/?size=100&id=ziwGuOoPfTsn&format=png&color=000000",
                  "manager": "https://img.icons8.com/?size=100&id=124190&format=png&color=000000"}


        self.agents = [
            self.user_proxy,
            self.chatbot,
            self.web_retriever,
            self.calculator,
            self.dalle,
        ]


        for component in self.agents:
            component.register_reply(
                [autogen.Agent, None],
                reply_func=print_messages,
                config={"callback": None},
            )

        if image_path is not None:
            self.image_explainer = MultimodalWrapper.get_image_explainer(config_list)
            self.agents.append(self.image_explainer)

        if pdf_path is not None:
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
            llm_config=llm_config,
        )

    def initiate_chat(self, user_prompt: str) -> None:
        self.groupchat.reset()
        self.manager.reset()

        for agent in self.agents:
            agent.reset()

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
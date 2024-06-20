import autogen
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from typing import Dict, List, Optional


class OverarchingWrapper:

    def __init__(self, config_list: List[Dict]) -> None:
        llm_config = {"cache_seed": None, "temperature": 0, "config_list": config_list}

        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            system_message="You are a human user. When you are satisfied with the answer, reply with TERMINATE.",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            llm_config=llm_config,
        )
        self.chatbot = autogen.AssistantAgent(
            name="chatbot",
            system_message="You are a chatbot, you can answer text queries.",
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
        )
        self.image_explainer = MultimodalConversableAgent(
            name="image_explainer",
            system_message="You are an image explainer, you can answer queries based on provided images",
            llm_config=llm_config,
        )

        self.agents = [
            self.user_proxy,
            self.chatbot,
            self.image_explainer,
        ]
        self.groupchat = autogen.GroupChat(
            agents=self.agents,
            messages=[],
            max_round=20,
            send_introductions=True,
            allow_repeat_speaker=False,
        )
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            system_message="You are a group chat manager. When you are satisfied with the answer, reply with TERMINATE.",
            llm_config=llm_config,
        )

    def initiate_chat(self, user_prompt: str, user_image_path: Optional[str]) -> None:
        self.groupchat.reset()
        self.manager.reset()

        for agent in self.agents:
            agent.reset()

        prompt = user_prompt if user_image_path is None else f"""
            Using <img {user_image_path}> as knowledge base, answer the following question:

            {user_prompt}
            """

        self.user_proxy.initiate_chat(
            self.manager,
            message=prompt,
        )

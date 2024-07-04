from autogen.agentchat import ChatResult, UserProxyAgent
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from typing import Dict, List, Optional

from wrappers.chat_wrapper_mixin import ChatWrapperMixin


class MultimodalWrapper(ChatWrapperMixin):
    AGENT_NAME = 'image_explainer'

    def __init__(self, text_config_list: List[Dict], vision_config_list: List[Dict]) -> None:
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            system_message="""
                You are a human user.
                If the question has been answered, reply with TERMINATE.
                """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": text_config_list},
            code_execution_config={"use_docker": False},
        )
        self.image_explainer = self.get_image_explainer(vision_config_list)

    @staticmethod
    def get_image_explainer(vision_config_list: List[Dict]) -> MultimodalConversableAgent:
        return MultimodalConversableAgent(
            name=MultimodalWrapper.AGENT_NAME,
            human_input_mode="NEVER",
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": vision_config_list},
        )

    def initiate_chat(self, user_prompt: str, user_image_path: Optional[str]) -> ChatResult:
        self.image_explainer.reset()

        self.register_replies_callback([self.user_proxy, self.image_explainer])

        prompt = user_prompt if user_image_path is None else f"""
            Using <img {user_image_path}> as knowledge base, answer the following question:
            
            {user_prompt}
            """

        return self.user_proxy.initiate_chat(
            self.image_explainer,
            message=prompt,
        )

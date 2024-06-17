from autogen.agentchat import ChatResult, UserProxyAgent
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from typing import Dict, List, Optional


class MultimodalWrapper(object):

    def __init__(self, text_config_list: List[Dict], vision_config_list: List[Dict]) -> None:
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": text_config_list},
        )
        self.image_explainer = MultimodalConversableAgent(
            name="image-explainer",
            llm_config={"cache_seed": None, "temperature": 0, "config_list": vision_config_list},
        )

    def initiate_chat(self, user_prompt: str, user_image_path: Optional[str]) -> ChatResult:
        self.image_explainer.reset()

        prompt = user_prompt if user_image_path is None else f"""
            Using <img {user_image_path}> as knowledge base, answer the following question:
            
            {user_prompt}
            """

        return self.user_proxy.initiate_chat(
            self.image_explainer,
            message=prompt,
        )

import os
from PIL import Image
from autogen import ConversableAgent
from autogen.agentchat.contrib import img_utils
from autogen.agentchat.contrib.capabilities import generate_images
from typing import List

class DalleWrapper(object):
    CRITIC_SYSTEM_MESSAGE = """You need to improve the prompt of the user.
    Optimize it in a way to create an image that is better in terms of color, shape, text (clarity), and other things.
    Reply with the following format:

    PROMPT: here is the updated prompt!

    If you have no better prompt, just say TERMINATE
    """

    def __init__(self, gpt_config: str, gpt_vision_config: str, dalle_config: str):
        self.gpt_config = gpt_config
        self.gpt_vision_config = gpt_vision_config
        self.dalle_config = dalle_config

    @staticmethod
    def _is_termination_message(msg) -> bool:
        # Detects if we should terminate the conversation
        if isinstance(msg.get("content"), str):
            return msg["content"].rstrip().endswith("TERMINATE")
        elif isinstance(msg.get("content"), list):
            for content in msg["content"]:
                if isinstance(content, dict) and "text" in content:
                    return content["text"].rstrip().endswith("TERMINATE")
        return False

    def critic_agent(self) -> ConversableAgent:
        return ConversableAgent(
            name="critic",
            llm_config=self.gpt_vision_config,
            system_message=self.CRITIC_SYSTEM_MESSAGE,
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER",
            is_termination_msg=self._is_termination_message,
        )

    def image_generator_agent(self) -> ConversableAgent:
        # Create the agent
        agent = ConversableAgent(
            name="dalle",
            llm_config=self.gpt_vision_config,
            max_consecutive_auto_reply=3,
            human_input_mode="NEVER",
            is_termination_msg=self._is_termination_message,
        )

        # Add image generation ability to the agent
        dalle_gen = generate_images.DalleImageGenerator(llm_config=self.dalle_config)
        image_gen_capability = generate_images.ImageGeneration(
            image_generator=dalle_gen, text_analyzer_llm_config=self.gpt_config
        )

        image_gen_capability.add_to_agent(agent)
        return agent

    def extract_images(self, sender: ConversableAgent, recipient: ConversableAgent) -> List[Image.Image]:
        images = []
        all_messages = sender.chat_messages.get(recipient, [])

        for message in reversed(all_messages):
            # The GPT-4V format, where the content is an array of data
            contents = message.get("content", [])
            for content in contents:
                if isinstance(content, str):
                    continue
                if content.get("type", "") == "image_url":
                    img_data = content["image_url"]["url"]
                    images.append(img_utils.get_pil_image(img_data))

        if not images:
            raise ValueError("No image data found in messages.")

        return images
    

    # Main function to generate and critique images
    def generate_and_critique_image(self, prompt: str):
        dalle = self.image_generator_agent()
        critic = self.critic_agent()

        result = dalle.initiate_chat(critic, message=prompt)
        images = self.extract_images(dalle, critic)

        return result, images

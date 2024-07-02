import streamlit as st
from autogen import Agent, AssistantAgent, ConversableAgent, UserProxyAgent
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union


class ChatWrapperMixin(object):
    DEFAULT_AVATAR: str = "https://img.icons8.com/?size=100&id=GBu1KXnCZZ8j&format=png&color=000000"

    AVATARS: Dict[str, str] = {
        "calculator": "https://img.icons8.com/?size=100&id=qrOXrfUDKkOX&format=png&color=000000",
        "chatbot": "https://img.icons8.com/?size=100&id=GBu1KXnCZZ8j&format=png&color=000000",
        "dalle": "https://img.icons8.com/?size=100&id=ziwGuOoPfTsn&format=png&color=000000",
        "image_explainer": "https://img.icons8.com/?size=100&id=13120&format=png&color=000000",
        "manager": "https://img.icons8.com/?size=100&id=124190&format=png&color=000000",
        "user_proxy": "https://cdn-icons-png.flaticon.com/512/4333/4333609.png",
        "web_retriever": "https://img.icons8.com/?size=100&id=TfgcKLCFPMgk&format=png&color=000000",
    }

    @staticmethod
    def print_messages(
            recipient: ConversableAgent,
            messages: Optional[List[Dict]] = None,
            sender: Optional[Agent] = None,
            config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        print(
            f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {messages[-1]}"
        )

        user = sender.name

        content = messages[-1]["content"]
        if content is None:
            content = ""
        if isinstance(content, list) is True:
            content = "".join(line["text"] if line["type"] == "text" else f"<{line['type']}>" for line in content)

        tool_calls = messages[-1].get("tool_calls", [])
        user_avatar = ChatWrapperMixin.AVATARS.get(user, ChatWrapperMixin.DEFAULT_AVATAR)

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            content += f"\nFunction call: \"{function_name}\" with arguments {arguments}"

        message = st.chat_message(user, avatar=user_avatar)
        message.write(content)

        # required to ensure the agent communication flow continues
        return False, None

    @staticmethod
    def register_replies_callback(agents: Iterable[ConversableAgent]) -> None:
        for agent in agents:
            agent.register_reply(
                [Agent, None],
                reply_func=ChatWrapperMixin.print_messages,
                config={"callback": None},
            )

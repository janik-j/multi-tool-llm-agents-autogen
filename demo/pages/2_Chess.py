import streamlit as st
from autogen.io.base import IOStream
from enum import Enum

from demo import IOStreamlit
from wrappers import ChessNestedChatsWrapper, ChessNoBoardWrapper, ChessWrapper


class ChessDemoTypeEnum(Enum):
    CHESS = "Chess"
    CHESS_NO_BOARD = "Chess no Board"
    CHESS_NESTED_CHATS = "Chess Nested Chats"


# Redirect AutoGen's output to streamlit
IOStream.set_global_default(IOStreamlit())

st.title("AutoGen Chess")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4"])


with st.form("chess"):
    demo_type = st.selectbox(
        "Demo Type",
        [
            ChessDemoTypeEnum.CHESS.value,
            ChessDemoTypeEnum.CHESS_NO_BOARD.value,
            ChessDemoTypeEnum.CHESS_NESTED_CHATS.value,
        ]
    )
    number_of_moves = st.number_input("Number of moves per player", min_value=1, max_value=100)

    config_list = [{"model": openai_model, "api_key": openai_api_key}]
    chess_wrapper = {
        ChessDemoTypeEnum.CHESS.value: ChessWrapper,
        ChessDemoTypeEnum.CHESS_NO_BOARD.value: ChessNoBoardWrapper,
        ChessDemoTypeEnum.CHESS_NESTED_CHATS.value: ChessNestedChatsWrapper,
    }[ChessDemoTypeEnum(demo_type).value](config_list, number_of_moves)

    submitted = st.form_submit_button("Generate me a chess play!")
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if submitted and openai_api_key.startswith("sk-"):
        chess_wrapper.initiate_play()

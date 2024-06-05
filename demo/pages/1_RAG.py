import streamlit as st
from autogen.io.base import IOStream
from enum import Enum

from demo import IOStreamlit
from wrappers import RagNoInteractionWrapper, RagWrapper


class RagDemoTypeEnum(Enum):
    RAG = "RAG"
    RAG_NO_INTERACTION = "RAG no Interaction"


# Redirect AutoGen's output to streamlit
IOStream.set_global_default(IOStreamlit(remove_color=True))

st.title("AutoGen Retrieval Augmented Chat")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])


with st.form("rag"):
    demo_type = st.selectbox(
        "Demo Type",
        [
            RagDemoTypeEnum.RAG.value,
            RagDemoTypeEnum.RAG_NO_INTERACTION.value,
        ]
    )
    question = st.text_input('Enter your question')

    config_list = [{"model": openai_model, "api_key": openai_api_key}]
    rag_wrapper = {
        RagDemoTypeEnum.RAG.value: RagWrapper,
        RagDemoTypeEnum.RAG_NO_INTERACTION.value: RagNoInteractionWrapper,
    }[RagDemoTypeEnum(demo_type).value](config_list)

    submitted = st.form_submit_button("Retrieve a response for the question")
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if submitted and openai_api_key.startswith("sk-"):
        rag_wrapper.retrieve(question)

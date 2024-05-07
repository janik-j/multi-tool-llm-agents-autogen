import streamlit as st
from autogen.io.base import IOStream

from demo import IOStreamlit
from wrappers import RagNoInteractionWrapper


# Redirect AutoGen's output to streamlit
IOStream.set_global_default(IOStreamlit(remove_color=True))

st.title("AutoGen Retrieval Augmented Chat without Interaction between Agents")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4"])


with st.form("rag_no_interaction"):
    question = st.text_input('Enter your question')

    config_list = [{"model": openai_model, "api_key": openai_api_key}]
    rag_wrapper = RagNoInteractionWrapper(config_list)

    submitted = st.form_submit_button("Retrieve a response for the question")
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if submitted and openai_api_key.startswith("sk-"):
        rag_wrapper.retrieve(question)

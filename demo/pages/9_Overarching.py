import streamlit as st
import tempfile
from autogen.io.base import IOStream

from demo import IOStreamlit
from wrappers import OverarchingWrapper


IOStream.set_global_default(IOStreamlit())

st.title("AutoGen Overarching Agent")

openai_api_key = st.sidebar.text_input("OpenAI API Key")

config_list = [{"model": "gpt-4o", "api_key": openai_api_key}]


with st.form("overarching"):
    question = st.text_input("Enter your question")
    uploaded_file = st.file_uploader("Add attachment", type=["jpg", "png"])

    overarching_wrapper = OverarchingWrapper(config_list)

    submitted = st.form_submit_button("Generate an answer")
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if submitted and openai_api_key.startswith("sk-"):
        if uploaded_file is None:
            overarching_wrapper.initiate_chat(question, user_image_path=None)
        else:
            with tempfile.NamedTemporaryFile(mode="wb") as f:
                f.write(uploaded_file.read())
                overarching_wrapper.initiate_chat(question, user_image_path=f.name)

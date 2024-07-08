import streamlit as st
import tempfile
from autogen.io.base import IOStream

from demo import IOStreamlitNoOp
from wrappers import MultimodalWrapper


IOStream.set_global_default(IOStreamlitNoOp())

st.title("AutoGen Multimodal")

openai_api_key = st.sidebar.text_input("OpenAI API Key")

text_config_list = [{"model": "gpt-4o", "api_key": openai_api_key}]
vision_config_list = [{"model": "gpt-4o", "api_key": openai_api_key}]


with st.form("multimodal"):
    question = st.text_input("Enter your question")
    uploaded_file = st.file_uploader("Add attachment", type=["jpg", "png"])

    multimodal_wrapper = MultimodalWrapper(text_config_list, vision_config_list)

    submitted = st.form_submit_button("Generate an answer")
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if submitted and openai_api_key.startswith("sk-"):
        if uploaded_file is None:
            multimodal_wrapper.initiate_chat(question, user_image_path=None)
        else:
            file_type = uploaded_file.type.split("/")[-1]
            with tempfile.NamedTemporaryFile(prefix=f".{file_type}", mode="wb") as f:
                f.write(uploaded_file.read())
                multimodal_wrapper.initiate_chat(question, user_image_path=f.name)
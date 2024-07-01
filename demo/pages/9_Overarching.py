import streamlit as st
import tempfile
from autogen.io.base import IOStream

from demo import IOStreamlitChat
from wrappers import OverarchingWrapper


IOStream.set_global_default(IOStreamlitChat())

st.title("AutoGen Overarching Agent")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])
gsearch_api_key = st.sidebar.text_input("Google Search API Key")

config_list = [{"model": openai_model, "api_key": openai_api_key}]
gpt_vision_config = {"config_list": [{"model": "gpt-4-vision-preview", "api_key": openai_api_key}], "timeout": 120, "temperature": 0.7}
dalle_config = {"config_list": [{"model": "dall-e-3", "api_key": openai_api_key}], "timeout": 120,"temperature": 0.7}


with st.form("overarching"):
    user_prompt = st.text_input("Enter your question")
    uploaded_image = st.file_uploader("Add a context image", type=["jpg", "png"])
    uploaded_pdf = st.file_uploader("Add a context PDF", type=["pdf"])

    submitted = st.form_submit_button("Generate an answer")

    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if not gsearch_api_key:
        st.warning("Please enter your Google Search API key!", icon="⚠")

    if submitted and openai_api_key.startswith("sk-"):
        tmp_files = []

        image_path = None
        if uploaded_image is not None:
            image_tmp_file = tempfile.NamedTemporaryFile(mode="wb")
            image_tmp_file.write(uploaded_image.read())
            tmp_files.append(uploaded_image)
            image_path = image_tmp_file.name

        pdf_path = None
        if uploaded_pdf is not None:
            pdf_tmp_file = tempfile.NamedTemporaryFile(mode="wb")
            pdf_tmp_file.write(uploaded_pdf.read())
            tmp_files.append(uploaded_pdf)
            pdf_path = pdf_tmp_file.name

        overarching_wrapper = OverarchingWrapper(config_list, gpt_vision_config, dalle_config, image_path, pdf_path, gsearch_api_key)
        result, images = overarching_wrapper.initiate_chat(user_prompt)
        for image in reversed(images):
            st.image(image.resize((300, 300)))

        for tmp_file in tmp_files:
            tmp_file.close()

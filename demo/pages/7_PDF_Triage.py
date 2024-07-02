import streamlit as st
import tempfile
from autogen.io.base import IOStream

from demo import IOStreamlitNoOp
from wrappers import PdfTriageWrapper


IOStream.set_global_default(IOStreamlitNoOp())

st.title("AutoGen PDF Triage")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])

config_list = [{"model": openai_model, "api_key": openai_api_key}]


with st.form("pdf_triage"):
    question = st.text_input("Enter your question")
    uploaded_file = st.file_uploader("Add attachment", type=["pdf"])

    submitted = st.form_submit_button("Generate an answer")

    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")

    if submitted and openai_api_key.startswith("sk-"):
        if uploaded_file is None:
            pdf_triage_wrapper = PdfTriageWrapper(config_list, pdf_path=None)
            pdf_triage_wrapper.initiate_chat(question)
        else:
            with tempfile.NamedTemporaryFile(mode="wb") as f:
                f.write(uploaded_file.read())
                pdf_triage_wrapper = PdfTriageWrapper(config_list, pdf_path=f.name)
                pdf_triage_wrapper.initiate_chat(question)

import streamlit as st
from autogen.io.base import IOStream

from demo import IOStreamlitChat
from wrappers import BrowserWrapper


IOStream.set_global_default(IOStreamlitChat())

st.title("AutoGen Browser Interaction")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])
gsearch_api_key = st.sidebar.text_input("Google Search API Key")

config_list = [{"model": openai_model, "api_key": openai_api_key}]


with st.form("browser_interaction"):
    question = st.text_input("Enter your question")

    submitted = st.form_submit_button("Generate an answer")

    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if not gsearch_api_key:
        st.warning("Please enter your Google Search API key!", icon="⚠")

    if submitted and openai_api_key.startswith("sk-"):
        browser_wrapper = BrowserWrapper(config_list=config_list, gsearch_api_key=gsearch_api_key)
        browser_wrapper.initiate_chat(question)

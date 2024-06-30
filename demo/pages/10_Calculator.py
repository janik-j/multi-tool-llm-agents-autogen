import streamlit as st
from autogen.io.base import IOStream

from demo import IOStreamlitChat
from wrappers import CalculatorWrapper


IOStream.set_global_default(IOStreamlitChat())

st.title("AutoGen Calculator")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])

config_list = [{"model": openai_model, "api_key": openai_api_key}]


with st.form("calculator"):
    user_prompt = st.text_input("Enter your equation:")

    submitted = st.form_submit_button("Generate an answer")

    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")

    if submitted and openai_api_key.startswith("sk-"):
        calculator_wrapper = CalculatorWrapper(config_list=config_list)
        calculator_wrapper.initiate_chat(user_prompt)

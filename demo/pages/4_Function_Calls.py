import streamlit as st
from autogen.io.base import IOStream

from demo import IOStreamlit
from wrappers import FunctionCallsWrapper


# Redirect AutoGen's output to streamlit
IOStream.set_global_default(IOStreamlit(remove_color=True))

st.title("Function Calls (Websearch function)")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-3.5-turbo-1106", "gpt-4"])


with st.form("function_calls"):
    question = st.text_input('Enter your question')

    config_list = [{"model": openai_model, "api_key": openai_api_key}]
    function_calls_wrapper = FunctionCallsWrapper(config_list)

    submitted = st.form_submit_button("Retrieve a response for the question")
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if submitted and openai_api_key.startswith("sk-"):
        function_calls_wrapper.initiate_chat(question)

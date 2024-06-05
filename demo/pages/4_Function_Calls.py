# To install required packages:
# pip install autogen==0.1.0 streamlit==1.32.2

import streamlit as st
from wrappers import FunctionCallsWrapper

# Initialize avatars
avatars = {
    "tool": "https://img.icons8.com/?size=100&id=vFvrMYYJ8Ra7&format=png&color=000000",
    "assistant": "https://cdn-icons-png.flaticon.com/512/4333/4333609.png", # hint assistant and user are switched see https://github.com/microsoft/autogen/discussions/1839
    "user": "https://img.icons8.com/?size=100&id=GBu1KXnCZZ8j&format=png&color=000000"
}

# Streamlit application
st.title("💬 Autogen Writing Studio")
openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-3.5-turbo-1106", "gpt-4"])
gsearch_api_key = st.sidebar.text_input("Google Search API Key")
config_list = [{"model": openai_model, "api_key": openai_api_key}]

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "user", "content": "What do you wanna learn more about?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"], avatar=avatars.get(msg["role"])).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar=avatars["assistant"]).write(prompt)


    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    else:
        function_calls_wrapper = FunctionCallsWrapper(config_list, gsearch_api_key)

        result = function_calls_wrapper.initiate_chat(prompt)

        for message in result.chat_history:
            role = message["role"]
            content = message["content"]
            if content:  # Skip if content is empty
                st.session_state.messages.append({"role": role, "content": content})
                st.chat_message(role, avatar=avatars.get(role)).write(content)

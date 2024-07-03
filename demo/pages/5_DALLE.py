import streamlit as st
from wrappers import DalleWrapper
import os
from demo import IOStreamlitChat
from autogen.io.base import IOStream


IOStream.set_global_default(IOStreamlitChat())

# Streamlit application
st.title("DALLE 🎨")
openai_api_key = st.sidebar.text_input("OpenAI API Key")

# Configurations for different models
gpt_config = {
    "config_list": [{"model": "gpt-4-turbo-preview", "api_key": openai_api_key}],
    "timeout": 120,
    "temperature": 0.7,
}

gpt_vision_config = {
    "config_list": [{"model": "gpt-4-vision-preview", "api_key": openai_api_key}],
    "timeout": 120,
    "temperature": 0.7,
}

dalle_config = {
    "config_list": [{"model": "dall-e-3", "api_key": openai_api_key}],
    "timeout": 120,
    "temperature": 0.7,
}

# Initialize avatars
avatars = {
    "user": "https://cdn-icons-png.flaticon.com/512/4333/4333609.png", # hint assistant and user are switched 
    "assistant": "https://img.icons8.com/?size=100&id=GBu1KXnCZZ8j&format=png&color=000000"
}

st.chat_message("user", avatar=avatars["assistant"]).write("What kind of art can I generate for you today?")

if prompt := st.chat_input():
    st.chat_message("user", avatar=avatars["user"]).write(prompt)
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    else:
        dalle_wrapper = DalleWrapper(gpt_config, gpt_vision_config, dalle_config)
        result, images = dalle_wrapper.generate_and_critique_image(prompt)
        for image in reversed(images):
            _, central_column, _ = st.columns(3)
            with central_column:
                st.image(image.resize((300, 300)))

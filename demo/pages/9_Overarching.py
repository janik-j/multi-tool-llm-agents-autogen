import streamlit as st
import tempfile
from autogen.io.base import IOStream

from demo import IOStreamlitNoOp
from wrappers import OverarchingWrapper


IOStream.set_global_default(IOStreamlitNoOp())

st.title("AutoGen Overarching Agent")

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Text Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])
gsearch_api_key = st.sidebar.text_input("Google Search API Key")

config_list = [{"model": openai_model, "api_key": openai_api_key}]

overarching_wrapper = OverarchingWrapper(config_list)

calculator_enabled = st.checkbox("Calculator")
chatbot_enabled = st.checkbox("Chatbot")
dalle_enabled = st.checkbox("DALLE")
web_retriever_enabled = st.checkbox("Web Retriever")
image_explainer_enabled = st.checkbox("Image Explainer")
pdf_parser_enabled = st.checkbox("PDF Parser")
coding_enabled = st.checkbox("Coding")

if "custom_agent_names" not in st.session_state:
    st.session_state.custom_agent_names = []

if "custom_agents" not in st.session_state:
    st.session_state.custom_agents = {}

with st.form("add_custom_agent"):
    st.header("Add a custom Agent")
    agent_name = st.text_input("Agent Name")
    system_message = st.text_input("System Message")
    add_custom_agent_submitted = st.form_submit_button("Add Agent")

    if add_custom_agent_submitted:
        st.session_state.custom_agent_names.append(agent_name)
        st.session_state.custom_agents[agent_name] = system_message

with st.form("agent_names"):
    st.header("Your custom Agents")
    new_custom_agent_names = st.multiselect(
        "New custom Agents",
        st.session_state.custom_agent_names,
        default=st.session_state.custom_agent_names,
        key="selected_agents",
    )
    agent_names_submitted = st.form_submit_button("Update Agents")

    if agent_names_submitted:
        st.session_state.custom_agent_names = new_custom_agent_names

with st.form("overarching"):
    user_prompt = st.text_input("Enter your question")
    uploaded_image = st.file_uploader(
        "Add a context image",
        type=["jpg", "png"],
        disabled=(not image_explainer_enabled),
    )
    uploaded_pdf = st.file_uploader(
        "Add a context PDF",
        type=["pdf"],
        disabled=(not pdf_parser_enabled),
    )

    overarching_submitted = st.form_submit_button("Generate an answer")

    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    if web_retriever_enabled and not gsearch_api_key:
        st.warning("Please enter your Google Search API key!", icon="⚠")

    if overarching_submitted and openai_api_key.startswith("sk-") and (not web_retriever_enabled or gsearch_api_key):
        tmp_files = []

        if image_explainer_enabled and uploaded_image is not None:
            image_type = uploaded_image.type.split("/")[-1]
            image_tmp_file = tempfile.NamedTemporaryFile(suffix=f".{image_type}", mode="wb")
            image_tmp_file.write(uploaded_image.read())
            tmp_files.append(image_tmp_file)
            image_path = image_tmp_file.name

            overarching_wrapper.add_image_explainer(image_path)
        else:
            overarching_wrapper.remove_image_explainer()

        if pdf_parser_enabled and uploaded_pdf is not None:
            pdf_tmp_file = tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb")
            pdf_tmp_file.write(uploaded_pdf.read())
            tmp_files.append(pdf_tmp_file)
            pdf_path = pdf_tmp_file.name

            overarching_wrapper.add_pdf_parser(pdf_path)
        else:
            overarching_wrapper.remove_pdf_parser()

        if calculator_enabled:
            overarching_wrapper.add_calculator()
        else:
            overarching_wrapper.remove_calculator()

        if coding_enabled:
            overarching_wrapper.add_coding()
        else:
            overarching_wrapper.remove_coding()

        if chatbot_enabled:
            overarching_wrapper.add_custom_agent(
                agent_name="chatbot",
                system_message="""
                    You are a chatbot, you can answer text queries.
                    In case no other agents can answer, you should step in.
                    """,
            )
        else:
            overarching_wrapper.remove_custom_agent("chatbot")

        if dalle_enabled:
            overarching_wrapper.add_dalle()
        else:
            overarching_wrapper.remove_dalle()

        if web_retriever_enabled:
            overarching_wrapper.add_web_retriever(gsearch_api_key)
        else:
            overarching_wrapper.remove_web_retriever()

        for agent_name, system_message in st.session_state.custom_agents.items():
            if agent_name not in st.session_state.custom_agent_names:
                overarching_wrapper.remove_custom_agent(agent_name)
                continue
            overarching_wrapper.add_custom_agent(agent_name, system_message)

        result, images = overarching_wrapper.initiate_chat(user_prompt)
        for image in reversed(images):
            _, central_column, _ = st.columns(3)
            with central_column:
                st.image(image.resize((300, 300)))

        for tmp_file in tmp_files:
            tmp_file.close()

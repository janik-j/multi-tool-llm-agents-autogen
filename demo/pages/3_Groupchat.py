import streamlit as st
from autogen.io.base import IOStream

from demo import IOStreamlit
from wrappers import GroupChatWrapper


# Redirect AutoGen's output to streamlit
IOStream.set_global_default(IOStreamlit(remove_color=True))

st.title("Groupchat")

agent_templates = {
    "No template selected": {"name": "", "system_message": ""},
    "Engineer": {"name": "Engineer", "system_message": '''Engineer, You write code to resolve given task. If code running fail, you rewrite code.
            Your reply should be in the form of:
            Part 1:
            ```sh 
            // shell script to install python package if needed
            ```
            Part 2:
            ```python
            // python code to resolve task
            ```'''},
    "Critic": {"name": "Critic", "system_message": "Critic, find the bug and ask engineer to fix it, you don't write code."},
    "Product Manager": {"name": "Product Manager", "system_message": "Creative in software product ideas."},
    "Scientist": {"name": "Scientist", "system_message": "Scientist. You follow an approved plan. You are able to categorize papers after seeing their abstracts printed. You don't write code."},
}

avatars = {
    "tool": "https://img.icons8.com/?size=100&id=vFvrMYYJ8Ra7&format=png&color=000000",
    "assistant": "https://cdn-icons-png.flaticon.com/512/4333/4333609.png", # hint assistant and user are switched see https://github.com/microsoft/autogen/discussions/1839
    "user": "https://img.icons8.com/?size=100&id=GBu1KXnCZZ8j&format=png&color=000000"
}

openai_api_key = st.sidebar.text_input("OpenAI API Key")
openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-3.5-turbo-1106", "gpt-4", "gpt-4o"])
config_list = [{"model": openai_model, "api_key": openai_api_key}]

if "group_chat_wrapper" not in st.session_state:
    st.session_state.group_chat_wrapper = GroupChatWrapper([{"model": openai_model, "api_key": openai_api_key}])

if "agent_names" not in st.session_state:
    st.session_state.agent_names = ["Admin"]


with st.form("add_agent"):
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    st.header("Add an Agent")
    selected_template = st.selectbox('Choose a template', list(agent_templates.keys()), key='selected_template')
    agent_name = st.text_input('Agent Name')
    system_message = st.text_input('System Message')
    add_agent_button = st.form_submit_button("Add Agent")

    if add_agent_button:
        if agent_name == "":
            agent_name = selected_template
        st.session_state.group_chat_wrapper.add_agent(config_list, agent_name, system_message)
        st.session_state.agent_names.append(agent_name)
        

with st.form("reorder_agents"):
    st.header("Reorder Agents")
    reordered_agents = st.multiselect('Select agents in the order you want', st.session_state.agent_names, default=st.session_state.agent_names, key='reordered_agents')

    reorder_agents_button = st.form_submit_button("Reorder Agents")

    if reorder_agents_button:
        st.session_state.agent_names = reordered_agents
        st.session_state.group_chat_wrapper.reorder_agents(reordered_agents)

with st.form("groupchat"):
    custom_speaker_selection_func = st.selectbox("Select speaker selection function", ["auto", "random", "round_robin"])
    submitted = st.form_submit_button("Ask question")

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
        result = st.session_state.group_chat_wrapper.retrieve(config_list, prompt, custom_speaker_selection_func)
        for message in result.chat_history:
            print(message)
            role = message["role"]
            content = message["content"]
            if content:  # Skip if content is empty
                st.session_state.messages.append({"role": role, "content": content})
                st.chat_message(role, avatar=avatars.get(role)).write(content)

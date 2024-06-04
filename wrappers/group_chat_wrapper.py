# group_chat_wrapper.py
import autogen
from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat import ChatResult
from typing import Dict, List
import os

class GroupChatWrapper(object):
    def __init__(self, config_list: List[Dict]) -> None:
        cwd = os.path.dirname(__file__)
        self.work_dir = os.path.join(cwd, "workspace")
        self.agents = []

        self.user_proxy = autogen.UserProxyAgent(
            name="Admin",
            system_message="you are Admin, a human user. You will reply [TERMINATE] if task get resolved.",
            max_consecutive_auto_reply=10,
            human_input_mode="NEVER",
            description="Admin, a human user.",
            code_execution_config={"last_n_messages": 3, "work_dir": self.work_dir, "use_docker": True },
        )

        self.agents = [self.user_proxy]
        self.groupchat = autogen.GroupChat(agents=self.agents, messages=[], max_round=30, send_introductions=True)
        self.manager = autogen.GroupChatManager(groupchat=self.groupchat, llm_config={
                "seed": 42,
                "config_list": config_list,
            })


    def add_agent(self, config_list: List[Dict], agent_name : str, system_message : str):
        agent = autogen.AssistantAgent(
            name=agent_name,
            system_message=system_message,
            description=system_message,
            llm_config={
                "seed": 42,
                "config_list": config_list,
            },
        )
        self.agents.append(agent)

    def reorder_agents(self, ordered_agent_names : List[str]):
        ordered_agents = []
        for name in ordered_agent_names:
            for agent in self.agents:
                if agent.name == name:
                    ordered_agents.append(agent)
                    break
        self.agents = ordered_agents

    def retrieve(self, config_list: List[Dict], prompt: str, custom_speaker_selection_func : str) -> ChatResult:
        self.groupchat.reset()
        self.manager.reset()
        for agent in self.groupchat.agents:
            agent.reset()

        self.groupchat = autogen.GroupChat(agents=self.agents, messages=[], speaker_selection_method=custom_speaker_selection_func, max_round=30)
        self.manager = autogen.GroupChatManager(groupchat=self.groupchat, llm_config={
                "seed": 42,
                "config_list": config_list,
            })

        return self.user_proxy.initiate_chat(
            self.manager,
            message=prompt,
            max_turns=30
        )
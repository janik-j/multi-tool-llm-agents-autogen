# this code is based on 
# https://github.com/microsoft/autogen/blob/main/notebook/agentchat_function_call.ipynb
# https://medium.com/@kyeg/equipping-autonomous-agents-with-tools-49d146bcbf9e

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from autogen import AssistantAgent, UserProxyAgent
from IPython import get_ipython
from typing_extensions import Annotated
from autogen.agentchat import ChatResult
import os
import autogen
from autogen.cache import Cache

class FunctionCallsWrapper(object):

    def __init__(self, config_list: List[Dict]) -> None:

        self.sys_msg_tmpl = """You are a function call agent. You can use functions: `python`, `browser`

1. **Step-by-Step Approach**:
    - Break down the problem into clear, manageable steps.
    - Avoid over-dividing steps but ensure each step is concise and logical.

2. **Python Code Format**:
    - When suggesting Python code, enclose it within the following format:
    ```python
    # your code
    ```
    - If additional packages are needed, suggest the installation command.

3. **Query Extraction**:
    - Identify and extract any queries that can be resolved through Python code or available functions in this context.
    - Do not mix suggested Python codes and function calls in one step.

4. **Execution and Validation**:
    - Wait for the user to provide the results or execute the function call.
    - Continue if the result is correct. If not, adjust your query or reasoning and try again.

5. **Communication Style**:
    - Be clear and concise in your explanations.
    - Always summarize the final answer within a \\boxed{} statement.

6. **Web Search**:
    - Use the `browser` function to search the web for additional information.
    - Provide a brief explanation of the search query.

Problem:
"""
        cwd = os.path.dirname(__file__)
        self.work_dir = os.path.join(cwd, "output")
        self.chatbot = AssistantAgent(
            name="chatbot",
            system_message=self.sys_msg_tmpl,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
        )
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": self.work_dir,
                "use_docker": True,
            }
        )
        
        # define functions according to the function description
        @self.user_proxy.register_for_execution()
        @self.chatbot.register_for_llm(name="browser", description="The browser tool performs web searches by opening the provided query in the default web browser using the webbrowser module. It returns a string indicating the search is being performed.")
        def exec_browser(query: Annotated[str, "The query to search in the browser."]) -> str:
            """
            Search the query in the browser with the `browser` tool.
            Args:
                query (str): The query to search in the browser.
            Returns:
                str: The search results.
            """
            import webbrowser
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            return f"Searching for {query} in the browser."
        

    def initiate_chat(self, question) -> ChatResult:
        with Cache.disk() as cache:
            # start the conversation
            return self.user_proxy.initiate_chat(
                self.chatbot,
                message=question,
                cache=cache,
                max_turns=4,
            )


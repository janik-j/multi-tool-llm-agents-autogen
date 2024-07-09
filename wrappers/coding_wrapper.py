import autogen
from typing import Dict, List, Union
import re

class CodingWrapper:
    AGENT_NAME: str = "coding"
    SAFEGUARD_NAME: str = "code_safeguard"

    CODING_SYSTEM_MSG = """You are a coding assistant capable of:
    (1) Writing Python code to answer users' questions and solve programming problems.
    (2) Explaining your code and solutions clearly.

    When writing code, always use Python code blocks like this:
    ```python
    # Your code here
    ```

    Provide clear explanations for your code when necessary.
    """

    SAFEGUARD_SYSTEM_MSG = """
    You are a code safeguard. Your task is to review Python code for safety.
    Given a piece of code, answer with only one word:
    If not safe, answer `DANGER`; else, answer `SAFE`.

    Consider code unsafe if it:
    - Attempts to access the file system inappropriately
    - Tries to make network connections or API calls without authorization
    - Contains potentially harmful system calls
    - Might lead to infinite loops or excessive resource consumption
    """

    @staticmethod
    def get_coding_agent(config_list: List[Dict]) -> autogen.AssistantAgent:
        return autogen.AssistantAgent(
            name=CodingWrapper.AGENT_NAME,
            system_message=CodingWrapper.CODING_SYSTEM_MSG,
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": config_list},
        )

    @staticmethod
    def get_safeguard_agent(config_list: List[Dict]) -> autogen.AssistantAgent:
        return autogen.AssistantAgent(
            name=CodingWrapper.SAFEGUARD_NAME,
            system_message=CodingWrapper.SAFEGUARD_SYSTEM_MSG,
            llm_config={"cache_seed": None, "seed": 7, "temperature": 0, "config_list": config_list},
        )

    @staticmethod
    def execute_code(code: str) -> str:
        try:
            exec_globals = {}
            exec(code, exec_globals)
            return "Code executed successfully."
        except Exception as e:
            return f"Error executing code: {str(e)}"

    @staticmethod
    def register_functions(user_proxy: autogen.UserProxyAgent, safeguard_agent: autogen.AssistantAgent):
        def safe_execute_code(code: str) -> str:
            safety_check = safeguard_agent.generate_reply([{"content": code}], user_proxy)
            if safety_check.strip().lower() == "safe":
                return CodingWrapper.execute_code(code)
            else:
                return "The code was deemed unsafe and was not executed."

        user_proxy.register_function(
            function_map={
                "safe_execute_code": safe_execute_code,
            }
        )

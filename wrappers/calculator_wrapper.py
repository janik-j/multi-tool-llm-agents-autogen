from autogen import register_function
from autogen.agentchat import ChatResult, ConversableAgent, UserProxyAgent
from typing import Dict, List, Union

from wrappers.chat_wrapper_mixin import ChatWrapperMixin


class CalculatorWrapper(ChatWrapperMixin):
    AGENT_NAME: str = 'calculator'

    def __init__(self, config_list: List[Dict]) -> None:
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            system_message="""
                You are a human user.
                If you have been given an answer for the equation, reply with TERMINATE.
                """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
            code_execution_config={"use_docker": False},
        )
        self.calculator = self.get_calculator(config_list)

        self.register_functions(self.user_proxy, self.calculator)

    @staticmethod
    def register_functions(
            user_proxy: UserProxyAgent,
            calculator: ConversableAgent,
    ) -> None:
        register_function(
            CalculatorWrapper.add,
            caller=calculator,
            executor=user_proxy,
            name="add",
            description="Execute add(x, y) to retrieve x + y.",
        )
        register_function(
            CalculatorWrapper.subtract,
            caller=calculator,
            executor=user_proxy,
            name="subtract",
            description="Execute subtract(x, y) to retrieve x - y.",
        )
        register_function(
            CalculatorWrapper.multiply,
            caller=calculator,
            executor=user_proxy,
            name="multiply",
            description="Execute multiply(x, y) to retrieve x * y.",
        )
        register_function(
            CalculatorWrapper.divide,
            caller=calculator,
            executor=user_proxy,
            name="divide",
            description="Execute divide(x, y) to retrieve x / y.",
        )

    @staticmethod
    def get_calculator(config_list: List[Dict]) -> ConversableAgent:
        return ConversableAgent(
            name=CalculatorWrapper.AGENT_NAME,
            system_message="""
            You are a calculator. Use the following functions to provide the answer:

            1. add(x, y) to retrieve a + b.
            2. subtract(x, y) to retrieve a - b.
            3. multiply(x, y) to retrieve a * b.
            4. divide(x, y) to retrieve a / b.
            """,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=CalculatorWrapper.is_termination_message,
            llm_config={"cache_seed": None, "temperature": 0, "config_list": config_list},
        )

    @staticmethod
    def is_termination_message(message: Dict) -> bool:
        return "TERMINATE" in message['content']

    @staticmethod
    def add(x: Union[int, float], y: Union[int, float]) -> Union[int, float]:
        return x + y

    @staticmethod
    def subtract(x: Union[int, float], y: Union[int, float]) -> Union[int, float]:
        return x - y

    @staticmethod
    def multiply(x: Union[int, float], y: Union[int, float]) -> Union[int, float]:
        return x * y

    @staticmethod
    def divide(x: Union[int, float], y: Union[int, float]) -> Union[int, float]:
        return x / y

    def initiate_chat(self, user_prompt: str) -> ChatResult:
        self.calculator.reset()

        self.register_replies_callback([self.user_proxy, self.calculator])

        return self.user_proxy.initiate_chat(
            self.calculator,
            message=user_prompt,
        )

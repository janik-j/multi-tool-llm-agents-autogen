from autogen.io.console import IOConsole
from typing import Any


class IOStreamlitNoOp(IOConsole):

    def print(self, *objects: Any, sep: str = " ", end: str = "\n", flush: bool = False) -> None:
        pass

import re
import streamlit as st
from ansi2html import Ansi2HTMLConverter
from autogen.io.console import IOConsole
from io import StringIO
from typing import Any


class IOStreamlit(IOConsole):

    def __init__(self, remove_color: bool = False) -> None:
        self.remove_color = remove_color

    def print(self, *objects: Any, sep: str = " ", end: str = "\n", flush: bool = False) -> None:
        output = StringIO()
        print(*objects, sep=sep, end=end, flush=flush, file=output)

        if self.remove_color:
            ansi_remover = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            st.write(ansi_remover.sub("", output.getvalue()))
        else:
            # autogen uses ANSI colors, converting them to HTML to display in streamlit properly
            ansi_converter = Ansi2HTMLConverter()
            converted = ansi_converter.convert(output.getvalue())
            st.write(converted, unsafe_allow_html=True)

        output.close()

from bs4 import BeautifulSoup
from autogen.io.console import IOConsole
from io import StringIO
import re
import streamlit as st
from ansi2html import Ansi2HTMLConverter

class IOStreamlitChat(IOConsole):

    def __init__(self, remove_color: bool = False) -> None:
        self.remove_color = remove_color
        self.avatars = {
            "assistant": "https://img.icons8.com/?size=100&id=GBu1KXnCZZ8j&format=png&color=000000"
        }
        self.print_count = 0

    def print(self, *objects, sep=" ", end="\n", flush=False) -> None:
        self.print_count += 1
        if self.print_count >= 3: # skip first user message
            output = StringIO()
            print(*objects, sep=sep, end=end, flush=flush, file=output)
            output_value = output.getvalue()
            # Convert ANSI colors to HTML
            ansi_converter = Ansi2HTMLConverter()
            output_value = ansi_converter.convert(output_value)
            # Display the output using Streamlit
            self.extract_non_empty_ansi2html(output_value)
            output.close()
            

    def extract_non_empty_ansi2html(self, html_content):
        non_empty_content = []
        soup = BeautifulSoup(html_content, 'html.parser')
        pre_tags = soup.find_all('pre', class_='ansi2html-content')
        
        for pre_tag in pre_tags:
            content = pre_tag.get_text().strip() 
            content = re.sub(r'-{80,}', '', content) # Remove horizontal lines
            if content and not pre_tag.find('span'):
                non_empty_content.append(content)

        for content in non_empty_content:
            st.chat_message("assistant", avatar=self.avatars["assistant"]).write(content)

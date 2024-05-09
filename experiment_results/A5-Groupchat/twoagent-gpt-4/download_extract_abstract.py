# filename: download_extract_abstract.py

import requests
import PyPDF2
import re
import io

# Step 1: Download the PDF
url = "https://arxiv.org/pdf/2303.08774.pdf"
response = requests.get(url)

# Step 2: Extract text from the PDF
pdf_file = io.BytesIO(response.content)
pdf_reader = PyPDF2.PdfReader(pdf_file)
text = ""
for page in pdf_reader.pages:
    text += page.extract_text()

# Step 3: Identify and extract the abstract
abstract_pattern = r"Abstract(.*?)1\sIntroduction"
match = re.search(abstract_pattern, text, re.DOTALL)
if match:
    abstract = match.group(1).strip()

# Step 4: Save the abstract into a text file
with open("gpt4_abstract.txt", "w") as file:
    file.write(abstract)
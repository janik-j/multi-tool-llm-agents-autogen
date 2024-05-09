# filename: download_extract_pdf.py
import requests
import PyPDF2

# Download the PDF file
url = "https://arxiv.org/pdf/2303.08774.pdf"
response = requests.get(url)

# Save the PDF file
with open("gpt4_tech_report.pdf", "wb") as pdf_file:
    pdf_file.write(response.content)

# Extract the abstract from the PDF file
pdf_file_path = "gpt4_tech_report.pdf"
pdf_text = ""
with open(pdf_file_path, "rb") as pdf_file:
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    for page_num in range(pdf_reader.numPages):
        page = pdf_reader.getPage(page_num)
        pdf_text += page.extract_text()

# Find the abstract section
abstract_start = pdf_text.find("Abstract")
abstract_end = pdf_text.find("Introduction")

# Extract the abstract
abstract = pdf_text[abstract_start:abstract_end]

# Save the abstract into a text file
with open("gpt4_abstract.txt", "w") as abstract_file:
    abstract_file.write(abstract)

print("Abstract extracted and saved into gpt4_abstract.txt")
# filename: download_arxiv_pdfs.py
import requests
import os
from datetime import datetime, timedelta
import urllib.request

# Create a folder to save the PDFs
os.makedirs('arxiv', exist_ok=True)

# Get the date three days ago
date_three_days_ago = datetime.now() - timedelta(days=3)
date_str = date_three_days_ago.strftime('%Y-%m-%d')

# Make a request to arXiv API to get recent papers
url = f'http://export.arxiv.org/api/query?search_query=submittedDate:[{date_str}T00:00:00Z+TO+{date_str}T23:59:59Z]&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending'
response = requests.get(url)

# Parse the XML response to get the URLs of the PDFs
from xml.etree import ElementTree as ET
root = ET.fromstring(response.content)
for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
    pdf_url = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]')
    if pdf_url is not None:
        pdf_url = pdf_url.attrib['href']
        # Download the PDF and save it in the arxiv folder
        pdf_filename = pdf_url.split('/')[-1]
        urllib.request.urlretrieve(pdf_url, f'arxiv/{pdf_filename}')

print("PDFs downloaded successfully.")

# filename: extract_arxiv_links.py
import requests
from bs4 import BeautifulSoup

# Get the HTML content of the arXiv website
url = 'https://arxiv.org/'
response = requests.get(url)
html_content = response.text

# Parse the HTML content using Beautiful Soup
soup = BeautifulSoup(html_content, 'html.parser')

# Find all links in the HTML content
links = [link.get('href') for link in soup.find_all('a')]

# Save the extracted links to a file named "arxiv.txt"
with open('arxiv.txt', 'w') as file:
    for link in links:
        file.write(str(link) + '\n')

print("Links extracted from arXiv and saved to arxiv.txt successfully.")
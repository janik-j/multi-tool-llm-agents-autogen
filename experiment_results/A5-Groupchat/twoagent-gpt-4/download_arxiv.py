# filename: download_arxiv.py

import os
import urllib.request

def download_pdf(arxiv_id):
    directory = "/arxiv"
    if not os.path.exists(directory):
        os.makedirs(directory)

    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    filename = f"{directory}/{arxiv_id}.pdf"
    urllib.request.urlretrieve(url, filename)
    print(f"Downloaded {url} to {filename}")

# Replace '2101.00005' with the ID of the article you want to download
download_pdf('2101.00005')
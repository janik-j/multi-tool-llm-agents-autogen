# filename: extract_links.py

import requests
from bs4 import BeautifulSoup

def extract_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    return links

def save_links(links, filename):
    with open(filename, 'w') as f:
        for link in links:
            f.write(link + '\n')

def main():
    url = 'https://arxiv.org'
    links = extract_links(url)
    save_links(links, 'arxiv.txt')

if __name__ == '__main__':
    main()
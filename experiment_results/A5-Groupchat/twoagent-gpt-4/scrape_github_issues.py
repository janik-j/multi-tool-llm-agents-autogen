# filename: scrape_github_issues.py

import requests
from bs4 import BeautifulSoup

# URL of the ML.Net repo
url = "https://github.com/dotnet/machinelearning/issues"

# Send a GET request to the URL
response = requests.get(url)

# Parse the response text with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find the issue links
issue_links = soup.select('a.Link--primary.v-align-middle.no-underline.h4.js-navigation-open.markdown-title')

# Open the markdown file
with open('mlnet_issue.md', 'w') as f:
    # Write the 10 most recent issues to the file
    for issue_link in issue_links[:10]:
        f.write(f"- [{issue_link.text.strip()}](https://github.com{issue_link['href']})\n")
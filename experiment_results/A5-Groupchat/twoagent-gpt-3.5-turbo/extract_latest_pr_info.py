# filename: extract_latest_pr_info.py

from bs4 import BeautifulSoup

# Read the downloaded HTML content
with open('flaml_repo.html', 'r') as file:
    html_content = file.read()

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Find the title and URL of the latest PR
latest_pr = soup.select_one('.js-navigation-open').text.strip()
latest_pr_url = 'https://github.com' + soup.select_one('.js-navigation-open')['href']

# Save the extracted information into flaml_latest_pr.txt
with open('flaml_latest_pr.txt', 'w') as output_file:
    output_file.write(f"Latest PR: {latest_pr}\nURL: {latest_pr_url}")

print("Latest PR information extracted and saved successfully.")
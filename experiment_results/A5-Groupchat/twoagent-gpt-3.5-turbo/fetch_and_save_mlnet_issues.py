# filename: fetch_and_save_mlnet_issues.py

import requests

# Define the GitHub API endpoint for ML.Net repository issues
url = "https://api.github.com/repos/dotnet/machinelearning/issues"

# Parameters to get the most recent 10 issues
params = {
    'state': 'open',
    'per_page': 10
}

# Make a GET request to fetch the issues
response = requests.get(url, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    issues = response.json()

    # Save the issues into a markdown file
    with open("mlnet_issue.md", "w") as file:
        for issue in issues:
            file.write(f"## {issue['title']}\n")
            file.write(f"Issue URL: {issue['html_url']}\n\n")
    print("Successfully saved the most recent 10 issues into mlnet_issue.md")
else:
    print("Failed to fetch issues. Status code:", response.status_code)
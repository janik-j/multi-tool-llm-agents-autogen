# filename: fetch_mlnet_latest_issues.py

import requests
import json

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

    # Print the titles of the 10 most recent issues
    for issue in issues:
        print(issue['title'])
else:
    print("Failed to fetch issues. Status code:", response.status_code)
# filename: find_active_contributor.py
import requests
from datetime import datetime, timedelta

# Define the repository and the time range (last month)
repo = "microsoft/FLAML"
since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

# Make a request to the GitHub API to get the contributors
url = f"https://api.github.com/repos/{repo}/stats/contributors"
params = {"since": since_date}
headers = {"Accept": "application/vnd.github.v3+json"}
response = requests.get(url, params=params, headers=headers)

# Get the contributor with the most commits
if response.status_code == 200:
    contributors = response.json()
    most_active_contributor = max(contributors, key=lambda x: x["total"])
    username = most_active_contributor["author"]["login"]

    # Save the result to a file
    with open("flaml_active_contributor.txt", "w") as file:
        file.write(username)
        print(f"The most active contributor of {repo} in the last month is: {username}")
else:
    print("Failed to fetch data from GitHub API")
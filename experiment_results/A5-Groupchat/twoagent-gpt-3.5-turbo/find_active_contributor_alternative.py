# filename: find_active_contributor_alternative.py
import requests
from datetime import datetime, timedelta

# Define the repository and the time range (last month)
repo = "microsoft/FLAML"
since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

# Make a request to the GitHub API to get the list of commits in the last month
url = f"https://api.github.com/repos/{repo}/commits"
params = {"since": since_date}
headers = {"Accept": "application/vnd.github.v3+json"}
response = requests.get(url, params=params, headers=headers)

# Extract the author of each commit and count the number of commits per author
if response.status_code == 200:
    commits = response.json()
    commit_counts = {}
    for commit in commits:
        author = commit["commit"]["author"]["name"]
        commit_counts[author] = commit_counts.get(author, 0) + 1

    # Get the author with the most commits
    most_active_contributor = max(commit_counts, key=commit_counts.get)

    # Save the result to a file
    with open("flaml_active_contributor.txt", "w") as file:
        file.write(most_active_contributor)
        print(f"The most active contributor of {repo} in the last month is: {most_active_contributor}")
else:
    print("Failed to fetch data from GitHub API")
# filename: active_contributor.py

import requests
from dateutil.relativedelta import relativedelta
from datetime import datetime
from collections import Counter

# Define the repository and the time frame
repo = 'microsoft/flaml'
since = (datetime.now() - relativedelta(months=1)).isoformat()

# Send a request to the GitHub API
response = requests.get(f'https://api.github.com/repos/{repo}/commits?since={since}')

# Check the response status
if response.status_code != 200:
    print(f'Error with status code: {response.status_code}')
    exit()

# Count the commits by author
counter = Counter(commit['commit']['author']['name'] for commit in response.json())

# Check if there were any commits
if not counter:
    print('No commits in the last month.')
    exit()

# Find the most active contributor
most_active_contributor = counter.most_common(1)[0]

# Save the result to a file
with open('flaml_active_contrbutor.txt', 'w') as f:
    f.write(f'The most active contributor of {repo} in the last month is {most_active_contributor[0]} with {most_active_contributor[1]} commits.\n')

print('The result has been saved to flaml_active_contrbutor.txt.')
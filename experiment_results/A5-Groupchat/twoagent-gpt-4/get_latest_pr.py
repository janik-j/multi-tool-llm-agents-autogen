# filename: get_latest_pr.py

import requests
import json

# Define the API endpoint
url = 'https://api.github.com/repos/microsoft/FLAML/pulls'

# Send a GET request to the API endpoint
response = requests.get(url)

# Check that the request was successful
if response.status_code == 200:
    # Parse the response as JSON
    data = response.json()

    # Sort the list of PRs by the 'created_at' field
    data.sort(key=lambda x: x['created_at'], reverse=True)

    # Get the latest PR
    latest_pr = data[0]

    # Write the information about the latest PR to a file
    with open('flaml_latest_pr.txt', 'w') as f:
        f.write(json.dumps(latest_pr, indent=4))
else:
    print(f'Error: {response.status_code}')
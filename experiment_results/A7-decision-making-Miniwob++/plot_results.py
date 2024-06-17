import json
import os
import matplotlib.pyplot as plt

# Original results from page 33: https://arxiv.org/pdf/2308.08155
paper_result = paper_result = [
    {'filename': 'choose-list', 'value': 5},
    {'filename': 'click-button-sequence', 'value': 4},
    {'filename': 'click-button', 'value': 9},
    {'filename': 'click-checkboxes-large', 'value': 5},
    {'filename': 'click-checkboxes-soft', 'value': 1},
    {'filename': 'click-checkboxes-transfer', 'value': 6},
    {'filename': 'click-checkboxes', 'value': 5},
    {'filename': 'click-collapsible-2', 'value': 4},
    {'filename': 'click-collapsible', 'value': 1},
    {'filename': 'click-color', 'value': 8},
    {'filename': 'click-dialog-2', 'value': 8},
    {'filename': 'click-dialog', 'value': 10},
    {'filename': 'click-link', 'value': 8},
    {'filename': 'click-menu', 'value': 4},
    {'filename': 'click-option', 'value': 3},
    {'filename': 'click-scroll-list', 'value': 8},
    {'filename': 'click-shades', 'value': 0},
    {'filename': 'click-shape', 'value': 7},
    {'filename': 'click-test-2', 'value': 5},
    {'filename': 'count-shape', 'value': 2},
    {'filename': 'email-inbox-forward-nl', 'value': 4},
    {'filename': 'email-inbox-nl-turk', 'value': 7},
    {'filename': 'search-engine', 'value': 5},
]

# Convert paper_result values to success rates and create a dictionary
paper_result_dict = {item['filename']: item['value'] * 10.0 for item in paper_result}

# Get the current working directory
directory = os.getcwd()

# List to store filenames and their success rates from JSON files
data = []

# Read each file in the directory
for filename in os.listdir(directory):
    if filename.endswith(".json"):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as file:
            content = json.load(file)
            value = content.get("value", 0)
            success_rate = value * 10.0
            filename_without_extension = os.path.splitext(filename)[0]
            data.append((filename_without_extension, success_rate))

# Convert data list to a dictionary
data_dict = dict(data)

# Combine both sets of data and ensure all filenames are included
all_filenames = sorted(set(paper_result_dict.keys()).union(data_dict.keys()))

# Extract success rates for both datasets, filling missing values with 0
paper_success_rates = [paper_result_dict.get(filename, 0) for filename in all_filenames]
json_success_rates = [data_dict.get(filename, 0) for filename in all_filenames]

# Create the bar chart
bar_width = 0.4
index = range(len(all_filenames))

plt.figure(figsize=(12, 10))
plt.barh(index, paper_success_rates, bar_width, label='Paper Result (gpt-3.5-turbo-16k)', color='#87CEEB', edgecolor='black')
plt.barh([i + bar_width for i in index], json_success_rates, bar_width, label='Recreated Result (gpt-3.5-turbo-16k)', color='salmon', edgecolor='black')

plt.xlabel('Success Ratio (%)')
plt.ylabel('Task')
plt.title('A7: Performance on MiniWob++ (Results for 23 out of 47 tasks)')
plt.yticks([i + bar_width / 2 for i in index], all_filenames)
plt.xticks(range(0, 101, 10))
plt.xlim(0, 100)
plt.legend()
plt.grid(axis='x', linestyle='--', alpha=0.7)

# Show the plot
plt.tight_layout()
plt.show()

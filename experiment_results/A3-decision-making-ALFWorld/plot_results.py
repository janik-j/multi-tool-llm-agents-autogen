import matplotlib.pyplot as plt
import numpy as np

# the results where recreated using https://github.com/qingyun-wu/autogen/tree/2024-03/application/A3-decision-making-ALFWorld
# the results were saved in JSON files in the same directory as this script
# the results are to be compared to the original results from the paper: https://arxiv.org/pdf/2308.08155

# Data
methods = ["ALFChat (3 agent)", "ALFChat (2 agent)"]
average = [65, 51]
best_of_3 = [79, 68]

# Set up the bar chart
x = np.arange(len(methods))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))

# Create bars
rects1 = ax.bar(x - width/2, average, width, label='Average', color='salmon', edgecolor='black', linewidth=0.5)
rects2 = ax.bar(x + width/2, best_of_3, width, label='Best of 3', color='#ADD6E3', edgecolor='black', linewidth=0.5)

# Customize the chart
ax.set_ylabel('Success Ratio (%)')
ax.set_xlabel('Methods')
ax.set_title('A3: Performance on ALFWorld')
ax.set_xticks(x)
ax.set_xticklabels(methods)
ax.legend()

# Set y-axis range
ax.set_ylim(0, 100)

# Add grid
ax.yaxis.grid(True, linestyle='--', alpha=0.7)

# Add value labels on the bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)

# Adjust layout and display
plt.tight_layout()
plt.show()
import numpy as np
import matplotlib.pyplot as plt

ind = np.arange(2)
width = 0.25

res = [0.3919639060405176, 0.4817858189282338]
bar1 = plt.bar(ind, res, width, color='#ADD8E6', linewidth=0.5, edgecolor='black')

res_no_interaction = [0.3558901851162091, 0.44217757732463603]
bar2 = plt.bar(ind + width, res_no_interaction, width, color='salmon', linewidth=0.5, edgecolor='black')
plt.title("A2: Performance on Natural Questions dataset")

plt.xlabel("Metrics")
plt.ylabel("Percentage")

plt.xticks(ind + width / 2, ["F1", "Recall"])
plt.legend((bar1, bar2), ("Autogen", "Autogen W/O interactive retrieval"))
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.show()
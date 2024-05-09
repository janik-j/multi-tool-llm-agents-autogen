# filename: plot_sinx.py

import matplotlib.pyplot as plt
import numpy as np

# Create an array of x values from 0 to 2pi
x = np.linspace(0, 2*np.pi, 100)

# Create an array of y values using numpy's sin function
y = np.sin(x)

# Create a figure and a set of subplots
fig, ax = plt.subplots()

# Plot y = sin(x)
ax.plot(x, y)

# Set the x and y axis labels
ax.set(xlabel='x', ylabel='sin(x)',
       title='Plot of y = sin(x)')

# Grid on
ax.grid()

# Save the figure as a png file
fig.savefig("sinx.png")

print("The graph has been saved as sinx.png")
# filename: sinx_plot.py
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2*np.pi, 1000)
y = np.sin(x)

plt.plot(x, y)
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.title('Graph of y = sin(x)')
plt.grid(True)
plt.savefig('sinx.png')
plt.show()
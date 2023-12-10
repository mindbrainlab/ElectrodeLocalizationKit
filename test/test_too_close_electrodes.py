import matplotlib.pyplot as plt
import numpy as np


dist_matrix = np.loadtxt("dist_matrix.csv", delimiter=",")

print(len(dist_matrix))

# plot the histogram
plt.hist(dist_matrix, bins=100)

plt.show()

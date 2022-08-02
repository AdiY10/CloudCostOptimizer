from binascii import a2b_base64
from matplotlib import pyplot as plt
import numpy as np

def interp2(a1, a2):
	min_a1_x, max_a1_x = min(a1[:,0]), max(a1[:,0])
	min_a2_x, max_a2_x = min(a2[:,0]), max(a2[:,0])

	new_a1_x = np.linspace(min_a1_x, max_a1_x, 100)
	new_a2_x = np.linspace(min_a2_x, max_a2_x, 100)

	new_a1_y = np.interp(new_a1_x, a1[:,0], a1[:,1])
	new_a2_y = np.interp(new_a2_x, a2[:,0], a2[:,1])

	midx = [np.mean([new_a1_x[i], new_a2_x[i]]) for i in range(100)]
	midy = [np.mean([new_a1_y[i], new_a2_y[i]]) for i in range(100)]

	plt.plot(a1[:,0], a1[:,1],c='black')
	plt.plot(a2[:,0], a2[:,1],c='black')
	plt.plot(midx, midy, '--', c='black')

def average_curve(granularity: int, *axis_list)->tuple:
	"""takes a list of np arrays the shape (n, 2), each represents a curve.
		returns a pair of lists (lists of floats), representing the average curve."""
	min_max_xs = [(min(axis[:,0]), max(axis[:,0])) for axis in axis_list]

	new_axis_xs = [np.linspace(min_x, max_x, granularity) for min_x, max_x in min_max_xs]
	new_axis_ys = [np.interp(new_x_axis, axis[:,0], axis[:,1]) for axis, new_x_axis in zip(axis_list, new_axis_xs)]

	midx = [np.mean([new_axis_xs[axis_idx][i] for axis_idx in range(len(axis_list))]) for i in range(granularity)]
	midy = [np.mean([new_axis_ys[axis_idx][i] for axis_idx in range(len(axis_list))]) for i in range(granularity)]
	return midx, midy

def interp(granularity: int, *axis_list):
	min_max_xs = [(min(axis[:,0]), max(axis[:,0])) for axis in axis_list]

	new_axis_xs = [np.linspace(min_x, max_x, granularity) for min_x, max_x in min_max_xs]
	new_axis_ys = [np.interp(new_x_axis, axis[:,0], axis[:,1]) for axis, new_x_axis in zip(axis_list, new_axis_xs)]

	midx = [np.mean([new_axis_xs[axis_idx][i] for axis_idx in range(len(axis_list))]) for i in range(granularity)]
	midy = [np.mean([new_axis_ys[axis_idx][i] for axis_idx in range(len(axis_list))]) for i in range(granularity)]

	for axis in axis_list:
		plt.plot(axis[:,0], axis[:,1],c='black')

	plt.plot(midx, midy, '--', c='red')
	plt.show()

if __name__ == "__main__":
	a1 = np.array([(x, x**2+5*(x%4)) for x in range(10)])
	a2 = np.array([(x-0.5, x**2+6*(x%3)) for x in range(10)])
	a3 = np.array([(x+0.2, x**2+7*(x%2)) for x in range(10)])
	interp(a1, a2, a3)
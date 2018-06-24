# example_gp_mml_small_y
# author: Jungtaek Kim (jtkim@postech.ac.kr)
# last updated: June 24, 2018

import numpy as np

from bayeso import gp
from bayeso.utils import utils_plot


def main():
    X_train = np.array([
        [-3.0],
        [-2.0],
        [-1.0],
        [2.0],
        [1.2],
        [1.1],
    ])
    Y_train = np.cos(X_train) * 0.01
    num_test = 200
    X_test = np.linspace(-3, 3, num_test)
    X_test = X_test.reshape((num_test, 1))
    Y_test_truth = np.cos(X_test) * 0.01
    mu, sigma = gp.predict_optimized(X_train, Y_train, X_test)
    utils_plot.plot_gp(X_train, Y_train, X_test, mu, sigma, Y_test_truth, '../results/gp/', 'test_optimized_large_y')


if __name__ == '__main__':
    main()


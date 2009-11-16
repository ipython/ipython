#!/usr/bin/env python
# encoding: utf-8
"""Run a Monte-Carlo options pricer in parallel."""

from IPython.kernel import client
import numpy as np
from mcpricer import price_options


tc = client.TaskClient(profile='default')
mec = client.MultiEngineClient(profile='default')


# Initialize the common code on the engines
mec.run('mcpricer.py')

# Define the function that will do the calculation
def my_prices(K, sigma):
    S = 100.0
    r = 0.05
    days = 260
    paths = 10000
    return price_options(S, K, sigma, r, days, paths)

# Create arrays of strike prices and volatilities
nK = 5
nsigma = 5
K_vals = np.linspace(90.0, 100.0, nK)
sigma_vals = np.linspace(0.0, 0.2, nsigma)

# Submit tasks
taskids = []
for K in K_vals:
    for sigma in sigma_vals:
        t = client.MapTask(my_prices, args=(K, sigma))
        taskids.append(tc.run(t))

print "Submitted tasks: ", taskids

# Block until tasks are completed
tc.barrier(taskids)

# Get the results
results = [tc.get_task_result(tid) for tid in taskids]

# Assemble the result
prices = np.empty(nK*nsigma,
    dtype=[('vcall',float),('vput',float),('acall',float),('aput',float)]
)
for i, price_tuple in enumerate(results):
    prices[i] = price_tuple
prices.shape = (nK, nsigma)


def plot_options(K_vals, sigma_vals, prices):
    """
    Make a contour plot of the option prices.
    """
    from matplotlib import pyplot as plt
    plt.contourf(sigma_vals, K_vals, prices)
    plt.colorbar()
    plt.title("Option Price")
    plt.xlabel("Volatility")
    plt.ylabel("Strike Price")

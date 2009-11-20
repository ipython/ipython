#!/usr/bin/env python
"""Run a Monte-Carlo options pricer in parallel."""

from IPython.kernel import client
import numpy as np
from mcpricer import price_options

# The MultiEngineClient is used to setup the calculation and works with all
# engine.
mec = client.MultiEngineClient(profile='default')

# The TaskClient is an interface to the engines that provides dynamic load 
# balancing at the expense of not knowing which engine will execute the code.
tc = client.TaskClient(profile='default')

# Initialize the common code on the engines. This Python module has the
# price_options function that prices the options.
mec.run('mcpricer.py')

# Define the function that will make up our tasks. We basically want to
# call the price_options function with all but two arguments (K, sigma)
# fixed.
def my_prices(K, sigma):
    S = 100.0
    r = 0.05
    days = 260
    paths = 100000
    return price_options(S, K, sigma, r, days, paths)

# Create arrays of strike prices and volatilities
nK = 5
nsigma = 5
K_vals = np.linspace(90.0, 100.0, nK)
sigma_vals = np.linspace(0.0, 0.2, nsigma)

# Submit tasks to the TaskClient for each (K, sigma) pair as a MapTask.
# The MapTask simply applies a function (my_prices) to the arguments:
# my_prices(K, sigma) and returns the result.
taskids = []
for K in K_vals:
    for sigma in sigma_vals:
        t = client.MapTask(my_prices, args=(K, sigma))
        taskids.append(tc.run(t))

print "Submitted tasks: ", taskids

# Block until all tasks are completed.
tc.barrier(taskids)

# Get the results using TaskClient.get_task_result.
results = [tc.get_task_result(tid) for tid in taskids]

# Assemble the result into a structured NumPy array.
prices = np.empty(nK*nsigma,
    dtype=[('ecall',float),('eput',float),('acall',float),('aput',float)]
)
for i, price_tuple in enumerate(results):
    prices[i] = price_tuple
prices.shape = (nK, nsigma)
K_vals, sigma_vals = np.meshgrid(K_vals, sigma_vals)

def plot_options(sigma_vals, K_vals, prices):
    """
    Make a contour plot of the option price in (sigma, K) space.
    """
    from matplotlib import pyplot as plt
    plt.contourf(sigma_vals, K_vals, prices)
    plt.colorbar()
    plt.title("Option Price")
    plt.xlabel("Volatility")
    plt.ylabel("Strike Price")

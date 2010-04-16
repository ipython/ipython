#!/usr/bin/env python
"""Run a Monte-Carlo options pricer in parallel."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import time
from IPython.kernel import client
import numpy as np
from mcpricer import price_options
from matplotlib import pyplot as plt

#-----------------------------------------------------------------------------
# Setup parameters for the run
#-----------------------------------------------------------------------------

def ask_question(text, the_type, default):
    s = '%s [%r]: ' % (text, the_type(default))
    result = raw_input(s)
    if result:
        return the_type(result)
    else:
        return the_type(default)

cluster_profile = ask_question("Cluster profile", str, "default")
price = ask_question("Initial price", float, 100.0)
rate = ask_question("Interest rate", float, 0.05)
days = ask_question("Days to expiration", int, 260)
paths = ask_question("Number of MC paths", int, 10000)
n_strikes = ask_question("Number of strike values", int, 5)
min_strike = ask_question("Min strike price", float, 90.0)
max_strike = ask_question("Max strike price", float, 110.0)
n_sigmas = ask_question("Number of volatility values", int, 5)
min_sigma = ask_question("Min volatility", float, 0.1)
max_sigma = ask_question("Max volatility", float, 0.4)

strike_vals = np.linspace(min_strike, max_strike, n_strikes)
sigma_vals = np.linspace(min_sigma, max_sigma, n_sigmas)

#-----------------------------------------------------------------------------
# Setup for parallel calculation
#-----------------------------------------------------------------------------

# The MultiEngineClient is used to setup the calculation and works with all
# engine.
mec = client.MultiEngineClient(profile=cluster_profile)

# The TaskClient is an interface to the engines that provides dynamic load 
# balancing at the expense of not knowing which engine will execute the code.
tc = client.TaskClient(profile=cluster_profile)

# Initialize the common code on the engines. This Python module has the
# price_options function that prices the options.
mec.run('mcpricer.py')

#-----------------------------------------------------------------------------
# Perform parallel calculation
#-----------------------------------------------------------------------------

print "Running parallel calculation over strike prices and volatilities..."
print "Strike prices: ", strike_vals
print "Volatilities: ", sigma_vals
sys.stdout.flush()

# Submit tasks to the TaskClient for each (strike, sigma) pair as a MapTask.
t1 = time.time()
taskids = []
for strike in strike_vals:
    for sigma in sigma_vals:
        t = client.MapTask(
            price_options, 
            args=(price, strike, sigma, rate, days, paths)
        )
        taskids.append(tc.run(t))

print "Submitted tasks: ", len(taskids)
sys.stdout.flush()

# Block until all tasks are completed.
tc.barrier(taskids)
t2 = time.time()
t = t2-t1

print "Parallel calculation completed, time = %s s" % t
print "Collecting results..."

# Get the results using TaskClient.get_task_result.
results = [tc.get_task_result(tid) for tid in taskids]

# Assemble the result into a structured NumPy array.
prices = np.empty(n_strikes*n_sigmas,
    dtype=[('ecall',float),('eput',float),('acall',float),('aput',float)]
)

for i, price_tuple in enumerate(results):
    prices[i] = price_tuple
    
prices.shape = (n_strikes, n_sigmas)
strike_mesh, sigma_mesh = np.meshgrid(strike_vals, sigma_vals)

print "Results are available: strike_mesh, sigma_mesh, prices"
print "To plot results type 'plot_options(sigma_mesh, strike_mesh, prices)'"

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

def plot_options(sigma_mesh, strike_mesh, prices):
    """
    Make a contour plot of the option price in (sigma, strike) space.
    """
    plt.figure(1)
    
    plt.subplot(221)
    plt.contourf(sigma_mesh, strike_mesh, prices['ecall'])
    plt.axis('tight')
    plt.colorbar()
    plt.title('European Call')
    plt.ylabel("Strike Price")

    plt.subplot(222)
    plt.contourf(sigma_mesh, strike_mesh, prices['acall'])
    plt.axis('tight')
    plt.colorbar()
    plt.title("Asian Call")

    plt.subplot(223)
    plt.contourf(sigma_mesh, strike_mesh, prices['eput'])
    plt.axis('tight')
    plt.colorbar()
    plt.title("European Put")
    plt.xlabel("Volatility")
    plt.ylabel("Strike Price")

    plt.subplot(224)
    plt.contourf(sigma_mesh, strike_mesh, prices['aput'])
    plt.axis('tight')
    plt.colorbar()
    plt.title("Asian Put")
    plt.xlabel("Volatility")



    



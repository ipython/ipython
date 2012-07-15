# <nbformat>2</nbformat>

# <markdowncell>

# # Parallel Monto-Carlo options pricing

# <markdowncell>

# ## Problem setup

# <codecell>
from __future__ import print_function

import sys
import time
from IPython.parallel import Client
import numpy as np
from mckernel import price_options
from matplotlib import pyplot as plt

# <codecell>

cluster_profile = "default"
price = 100.0  # Initial price
rate = 0.05  # Interest rate
days = 260  # Days to expiration
paths = 10000  # Number of MC paths
n_strikes = 6  # Number of strike values
min_strike = 90.0  # Min strike price
max_strike = 110.0  # Max strike price
n_sigmas = 5  # Number of volatility values
min_sigma = 0.1  # Min volatility
max_sigma = 0.4  # Max volatility

# <codecell>

strike_vals = np.linspace(min_strike, max_strike, n_strikes)
sigma_vals = np.linspace(min_sigma, max_sigma, n_sigmas)

# <markdowncell>

# ## Parallel computation across strike prices and volatilities

# <markdowncell>

# The Client is used to setup the calculation and works with all engines.

# <codecell>

c = Client(profile=cluster_profile)

# <markdowncell>

# A LoadBalancedView is an interface to the engines that provides dynamic load
# balancing at the expense of not knowing which engine will execute the code.

# <codecell>

view = c.load_balanced_view()

# <codecell>

print("Strike prices: ", strike_vals)
print("Volatilities: ", sigma_vals)

# <markdowncell>

# Submit tasks for each (strike, sigma) pair.

# <codecell>

t1 = time.time()
async_results = []
for strike in strike_vals:
    for sigma in sigma_vals:
        ar = view.apply_async(price_options, price, strike, sigma, rate, days, paths)
        async_results.append(ar)

# <codecell>

print("Submitted tasks: ", len(async_results))

# <markdowncell>

# Block until all tasks are completed.

# <codecell>

c.wait(async_results)
t2 = time.time()
t = t2-t1

print("Parallel calculation completed, time = %s s" % t)

# <markdowncell>

# ## Process and visualize results

# <markdowncell>

# Get the results using the `get` method:

# <codecell>

results = [ar.get() for ar in async_results]

# <markdowncell>

# Assemble the result into a structured NumPy array.

# <codecell>

prices = np.empty(n_strikes*n_sigmas,
    dtype=[('ecall',float),('eput',float),('acall',float),('aput',float)]
)

for i, price in enumerate(results):
    prices[i] = tuple(price)

prices.shape = (n_strikes, n_sigmas)

# <markdowncell>

# Plot the value of the European call in (volatility, strike) space.

# <codecell>

plt.figure()
plt.contourf(sigma_vals, strike_vals, prices['ecall'])
plt.axis('tight')
plt.colorbar()
plt.title('European Call')
plt.xlabel("Volatility")
plt.ylabel("Strike Price")

# <markdowncell>

# Plot the value of the Asian call in (volatility, strike) space.

# <codecell>

plt.figure()
plt.contourf(sigma_vals, strike_vals, prices['acall'])
plt.axis('tight')
plt.colorbar()
plt.title("Asian Call")
plt.xlabel("Volatility")
plt.ylabel("Strike Price")

# <markdowncell>

# Plot the value of the European put in (volatility, strike) space.

# <codecell>

plt.figure()
plt.contourf(sigma_vals, strike_vals, prices['eput'])
plt.axis('tight')
plt.colorbar()
plt.title("European Put")
plt.xlabel("Volatility")
plt.ylabel("Strike Price")

# <markdowncell>

# Plot the value of the Asian put in (volatility, strike) space.

# <codecell>

plt.figure()
plt.contourf(sigma_vals, strike_vals, prices['aput'])
plt.axis('tight')
plt.colorbar()
plt.title("Asian Put")
plt.xlabel("Volatility")
plt.ylabel("Strike Price")

# <codecell>

plt.show()


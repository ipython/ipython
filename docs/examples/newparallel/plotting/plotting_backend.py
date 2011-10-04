"""An example of how to use IPython for plotting remote parallel data

The two files plotting_frontend.py and plotting_backend.py go together.

This file (plotting_backend.py) performs the actual computation.  For this
example, the computation just generates a set of random numbers that
look like a distribution of particles with 2D position (x,y) and
momentum (px,py).  In a real situation, this file would do some time
consuming and complicated calculation, and could possibly make calls
to MPI.

One important feature is that this script can also be run standalone without
IPython.  This is nice as it allows it to be run in more traditional
settings where IPython isn't being used.

When used with IPython.parallel, this code is run on the engines.  Because this
code doesn't make any plots, the engines don't have to have any plotting
packages installed.
"""

# Imports
import numpy as N
import time
import random

# Functions
def compute_particles(number):
    x = N.random.standard_normal(number)
    y = N.random.standard_normal(number)
    px = N.random.standard_normal(number)
    py = N.random.standard_normal(number)
    return x, y, px, py

def downsample(array, k):
    """Choose k random elements of array."""
    length = array.shape[0]
    indices = random.sample(xrange(length), k)
    return array[indices]

# Parameters of the run
number = 100000
d_number = 1000

# The actual run

time.sleep(0) # Pretend it took a while
x, y, px, py = compute_particles(number)
# Now downsample the data
downx = downsample(x, d_number)
downy = downsample(x, d_number)
downpx = downsample(px, d_number)
downpy = downsample(py, d_number)

print "downx: ", downx[:10]
print "downy: ", downy[:10]
print "downpx: ", downpx[:10]
print "downpy: ", downpy[:10]
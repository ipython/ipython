"""An example of how to use IPython1 for plotting remote parallel data

The two files plotting_frontend.py and plotting_backend.py go together.

To run this example, first start the IPython controller and 4
engines::

    ipcluster start -n 4

Then start ipython in pylab mode::

    ipython -pylab
    
Then a simple "run plotting_frontend.py" in IPython will run the
example.  When this is done, all the variables (such as number, downx, etc.)
are available in IPython, so for example you can make additional plots.
"""
from __future__ import print_function

import numpy as N
from pylab import *
from IPython.parallel import Client

# Connect to the cluster
rc = Client()
view = rc[:]

# Run the simulation on all the engines
view.run('plotting_backend.py')

# Bring back the data. These are all AsyncResult objects
number = view.pull('number')
d_number = view.pull('d_number')
downx = view.gather('downx')
downy = view.gather('downy')
downpx = view.gather('downpx')
downpy = view.gather('downpy')

# but we can still iterate through AsyncResults before they are done
print("number: ", sum(number))
print("downsampled number: ", sum(d_number))


# Make a scatter plot of the gathered data
# These calls to matplotlib could be replaced by calls to pygist or
# another plotting package.
figure(1)
# wait for downx/y
downx = downx.get()
downy = downy.get()
scatter(downx, downy)
xlabel('x')
ylabel('y')
figure(2)
# wait for downpx/y
downpx = downpx.get()
downpy = downpy.get()
scatter(downpx, downpy)
xlabel('px')
ylabel('py')
show()

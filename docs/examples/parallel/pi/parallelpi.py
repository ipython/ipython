"""Calculate statistics on the digits of pi in parallel.

This program uses the functions in :file:`pidigits.py` to calculate
the frequencies of 2 digit sequences in the digits of pi. The
results are plotted using matplotlib.

To run, text files from http://www.super-computing.org/
must be installed in the working directory of the IPython engines.
The actual filenames to be used can be set with the ``filestring``
variable below.

The dataset we have been using for this is the 200 million digit one here:
ftp://pi.super-computing.org/.2/pi200m/

and the files used will be downloaded if they are not in the working directory
of the IPython engines.
"""

from IPython.parallel import Client
from matplotlib import pyplot as plt
import numpy as np
from pidigits import *
from timeit import default_timer as clock

# Files with digits of pi (10m digits each)
filestring = 'pi200m.ascii.%(i)02dof20'
files = [filestring % {'i':i} for i in range(1,21)]

# Connect to the IPython cluster
c = Client()
c[:].run('pidigits.py')

# the number of engines
n = len(c)
id0 = c.ids[0]
v = c[:]
v.block=True
# fetch the pi-files
print "downloading %i files of pi"%n
v.map(fetch_pi_file, files[:n])
print "done"

# Run 10m digits on 1 engine
t1 = clock()
freqs10m = c[id0].apply_sync(compute_two_digit_freqs, files[0])
t2 = clock()
digits_per_second1 = 10.0e6/(t2-t1)
print "Digits per second (1 core, 10m digits):   ", digits_per_second1


# Run n*10m digits on all engines
t1 = clock()
freqs_all = v.map(compute_two_digit_freqs, files[:n])
freqs150m = reduce_freqs(freqs_all)
t2 = clock()
digits_per_second8 = n*10.0e6/(t2-t1)
print "Digits per second (%i engines, %i0m digits): "%(n,n), digits_per_second8

print "Speedup: ", digits_per_second8/digits_per_second1

plot_two_digit_freqs(freqs150m)
plt.title("2 digit sequences in %i0m digits of pi"%n)
plt.show()


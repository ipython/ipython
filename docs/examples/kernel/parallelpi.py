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
""" 

from IPython.kernel import client
from matplotlib import pyplot as plt
import numpy as np
from pidigits import *
from timeit import default_timer as clock


# Files with digits of pi (10m digits each)
filestring = 'pi200m-ascii-%(i)02dof20.txt'
files = [filestring % {'i':i} for i in range(1,16)]


# A function for reducing the frequencies calculated
# by different engines.
def reduce_freqs(freqlist):
    allfreqs = np.zeros_like(freqlist[0])
    for f in freqlist:
        allfreqs += f
    return allfreqs


# Connect to the IPython cluster
mec = client.MultiEngineClient(profile='mycluster')
mec.run('pidigits.py')


# Run 10m digits on 1 engine
mapper = mec.mapper(targets=0)
t1 = clock()

freqs10m = mapper.map(compute_two_digit_freqs, files[:1])[0]

t2 = clock()
digits_per_second1 = 10.0e6/(t2-t1)
print "Digits per second (1 core, 10m digits):   ", digits_per_second1


# Run 150m digits on 15 engines (8 cores)
t1 = clock()

freqs_all = mec.map(compute_two_digit_freqs, files[:len(mec)])
freqs150m = reduce_freqs(freqs_all)

t2 = clock()
digits_per_second8 = 150.0e6/(t2-t1)
print "Digits per second (8 cores, 150m digits): ", digits_per_second8

print "Speedup: ", digits_per_second8/digits_per_second1

plot_two_digit_freqs(freqs150m)
plt.title("2 digit sequences in 150m digits of pi")


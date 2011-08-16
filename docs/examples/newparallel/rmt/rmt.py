#-------------------------------------------------------------------------------
# Driver code that the client runs.
#-------------------------------------------------------------------------------
# To run this code start a controller and engines using:
# ipcluster -n 2
# Then run the scripts by doing irunner rmt.ipy or by starting ipython and
# doing run rmt.ipy.

from rmtkernel import *
import numpy
from IPython.parallel import Client


def wignerDistribution(s):
    """Returns (s, rho(s)) for the Wigner GOE distribution."""
    return (numpy.pi*s/2.0) * numpy.exp(-numpy.pi*s**2/4.)


def generateWignerData():
    s = numpy.linspace(0.0,4.0,400)
    rhos = wignerDistribution(s)
    return s, rhos
    

def serialDiffs(num, N):
    diffs = ensembleDiffs(num, N)
    normalizedDiffs = normalizeDiffs(diffs)
    return normalizedDiffs


def parallelDiffs(rc, num, N):
    nengines = len(rc.targets)
    num_per_engine = num/nengines
    print "Running with", num_per_engine, "per engine."
    ar = rc.apply_async(ensembleDiffs, num_per_engine, N)
    return numpy.array(ar.get()).flatten()


# Main code
if __name__ == '__main__':
    rc = Client()
    view = rc[:]
    print "Distributing code to engines..."
    view.run('rmtkernel.py')
    view.block = False

    # Simulation parameters
    nmats = 100
    matsize = 30
    # tic = time.time()
    %timeit -r1 -n1 serialDiffs(nmats,matsize)
    %timeit -r1 -n1 parallelDiffs(view, nmats, matsize)

    # Uncomment these to plot the histogram
    # import pylab
    # pylab.hist(parallelDiffs(rc,matsize,matsize))

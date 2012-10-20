"""Parallel histogram function"""
import numpy
from IPython.parallel import Reference

def phistogram(view, a, bins=10, rng=None, normed=False):
    """Compute the histogram of a remote array a.
    
    Parameters
    ----------
        view
            IPython DirectView instance
        a : str
            String name of the remote array
        bins : int
            Number of histogram bins
        rng : (float, float)
            Tuple of min, max of the range to histogram
        normed : boolean
            Should the histogram counts be normalized to 1
    """
    nengines = len(view.targets)
    
    # view.push(dict(bins=bins, rng=rng))
    with view.sync_imports():
        import numpy
    rets = view.apply_sync(lambda a, b, rng: numpy.histogram(a,b,rng), Reference(a), bins, rng)
    hists = [ r[0] for r in rets ]
    lower_edges = [ r[1] for r in rets ]
    # view.execute('hist, lower_edges = numpy.histogram(%s, bins, rng)' % a)
    lower_edges = view.pull('lower_edges', targets=0)
    hist_array = numpy.array(hists).reshape(nengines, -1)
    # hist_array.shape = (nengines,-1)
    total_hist = numpy.sum(hist_array, 0)
    if normed:
        total_hist = total_hist/numpy.sum(total_hist,dtype=float)
    return total_hist, lower_edges


    
    

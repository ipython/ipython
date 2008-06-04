""" IPython 'scipy' profile, preloads NumPy and SciPy.

This profile loads the math/cmath modules as well as all of numpy and scipy.

It exposes numpy and scipy via the 'np' and 'sp' shorthands as well for
convenience.
"""

import IPython.ipapi
import ipy_defaults

def main():
    ip = IPython.ipapi.get()

    try:
        ip.ex("import math,cmath")
        ip.ex("import numpy")
        ip.ex("import scipy")

        ip.ex("import numpy as np")
        ip.ex("import scipy as sp")
    
        ip.ex("from numpy import *")
        ip.ex("from scipy import *")

    except ImportError:
        print "Unable to start scipy profile, are numpy and scipy installed?"
    
main()

""" IPython 'numpy' profile, to preload NumPy.

This profile loads the math/cmath modules as well as all of numpy.

It exposes numpy via the 'np' shorthand as well for convenience.
"""

import IPython.ipapi
import ipy_defaults

def main():
    ip = IPython.ipapi.get()

    try:
        ip.ex("import math,cmath")
        ip.ex("import numpy")
        ip.ex("import numpy as np")

        ip.ex("from numpy import *")

    except ImportError:
        print "Unable to start NumPy profile, is numpy installed?"
    
main()

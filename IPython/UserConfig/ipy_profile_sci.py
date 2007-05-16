""" IPython 'sci' profile

Replaces the old scipy profile.

"""


import IPython.ipapi
import ipy_defaults

def main():
    ip = IPython.ipapi.get()

    try:
        ip.ex("import scipy")
        ip.ex("import numpy")
        
        ip.ex("from scipy import *")
        ip.ex("from numpy import *")
        print "SciPy profile successfully loaded."
    except ImportError:
        print "Unable to start scipy profile, are scipy and numpy installed?"
    

main()
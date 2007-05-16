import ipy_defaults
# import ...
# Load Numpy an SciPy by themselves so that 'help' works on them

import IPython.ipapi
import ipy_defaults

def main():
    ip = IPython.ipapi.get()

    ip.ex("import scipy")
    ip.ex("import numpy")
    
    ip.ex("from scipy import *")
    ip.ex("from numpy import *")

if __name__ == "__main__":
    main()
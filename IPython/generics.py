from IPython.ipapi import TryNext
from IPython.external.simplegeneric import generic

''' 'Generic' functions for extending IPython

See http://cheeseshop.python.org/pypi/simplegeneric

Here's an example from genutils.py:

    def print_lsstring(arg):
        """ Prettier (non-repr-like) and more informative printer for LSString """
        print "LSString (.p, .n, .l, .s available). Value:"
        print arg
        
    print_lsstring = result_display.when_type(LSString)(print_lsstring)

(Yes, the nasty syntax is for python 2.3 compatibility. Your own extensions
can use the niftier decorator syntax)

'''

@generic
def result_display(result):
    """ print the result of computation """
    raise TryNext

result_display = generic(result_display)


''' 'Generic' functions for extending IPython.

See http://cheeseshop.python.org/pypi/simplegeneric.

Here is an example from genutils.py:

    def print_lsstring(arg):
        "Prettier (non-repr-like) and more informative printer for LSString"
        print "LSString (.p, .n, .l, .s available). Value:"
        print arg
        
    print_lsstring = result_display.when_type(LSString)(print_lsstring)

(Yes, the nasty syntax is for python 2.3 compatibility. Your own extensions
can use the niftier decorator syntax introduced in Python 2.4).
'''

from IPython.ipapi import TryNext
from IPython.external.simplegeneric import generic

def result_display(result):
    """ print the result of computation """
    raise TryNext

result_display = generic(result_display)

def inspect_object(obj):
    """ Called when you do obj? """
    raise TryNext
inspect_object = generic(inspect_object)

def complete_object(obj, prev_completions):
    """ Custom completer dispatching for python objects
    
    obj is the object itself.
    prev_completions is the list of attributes discovered so far.
    
    This should return the list of attributes in obj. If you only wish to
    add to the attributes already discovered normally, return
    own_attrs + prev_completions.
    """
  
    raise TryNext
complete_object = generic(complete_object)

#import os
#def my_demo_complete_object(obj, prev_completions):
#    """ Demo completer that adds 'foobar' to the completions suggested
#    for any object that has attribute (path), e.g. 'os'"""
#    if hasattr(obj,'path'):
#        return prev_completions + ['foobar']
#    raise TryNext
#
#my_demo_complete_object = complete_object.when_type(type(os))(my_demo_complete_object)

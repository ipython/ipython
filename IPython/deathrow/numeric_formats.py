# -*- coding: utf-8 -*-
"""
Extension for printing Numeric Arrays in flexible ways.
"""

from Numeric import ArrayType

def num_display(self,arg):
    """Display method for printing which treats Numeric arrays specially.
    """

    # Non-numpy variables are printed using the system default
    if type(arg) != ArrayType:
        self._display(arg)
        return
    # Otherwise, we do work.
    format = __IPYTHON__.runtime_rc.numarray_print_format
    print 'NumPy array, format:',format
    # Here is where all the printing logic needs to be implemented
    print arg # nothing yet :)


def magic_format(self,parameter_s=''):
    """Specifies format of numerical output.

    This command is similar to Ocave's format command.
    """

    valid_formats = ['long','short']
    
    if parameter_s in valid_formats:
        self.runtime_rc.numarray_print_format = parameter_s
        print 'Numeric output format is now:',parameter_s
    else:
        print 'Invalid format:',parameter_s
        print 'Valid formats:',valid_formats

# setup default format
__IPYTHON__.runtime_rc.numarray_print_format = 'long'

# Bind our new functions to the interpreter
__IPYTHON__.__class__.magic_format = magic_format
__IPYTHON__.hooks.display = num_display

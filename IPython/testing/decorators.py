"""Decorators for labeling test objects.

Decorators that merely return a modified version of the original
function object are straightforward.  Decorators that return a new
function object need to use
nose.tools.make_decorator(original_function)(decorator) in returning
the decorator, in order to preserve metadata such as function name,
setup and teardown functions and so on - see nose.tools for more
information.

This module provides a set of useful decorators meant to be ready to use in
your own tests.  See the bottom of the file for the ready-made ones, and if you
find yourself writing a new one that may be of generic use, add it here.

NOTE: This file contains IPython-specific decorators and imports the
numpy.testing.decorators file, which we've copied verbatim.  Any of our own
code will be added at the bottom if we end up extending this.
"""

# Stdlib imports
import inspect
import sys

# Third-party imports

# This is Michele Simionato's decorator module, also kept verbatim.
from decorator_msim import decorator, update_wrapper

# Grab the numpy-specific decorators which we keep in a file that we
# occasionally update from upstream: decorators_numpy.py is an IDENTICAL copy
# of numpy.testing.decorators.
from decorators_numpy import *

##############################################################################
# Local code begins

# Utility functions

def apply_wrapper(wrapper,func):
    """Apply a wrapper to a function for decoration.

    This mixes Michele Simionato's decorator tool with nose's make_decorator,
    to apply a wrapper in a decorator so that all nose attributes, as well as
    function signature and other properties, survive the decoration cleanly.
    This will ensure that wrapped functions can still be well introspected via
    IPython, for example.
    """
    import nose.tools

    return decorator(wrapper,nose.tools.make_decorator(func)(wrapper))


def make_label_dec(label,ds=None):
    """Factory function to create a decorator that applies one or more labels.

    :Parameters:
      label : string or sequence
      One or more labels that will be applied by the decorator to the functions
    it decorates.  Labels are attributes of the decorated function with their
    value set to True.

    :Keywords:
      ds : string
      An optional docstring for the resulting decorator.  If not given, a
      default docstring is auto-generated.

    :Returns:
      A decorator.

    :Examples:

    A simple labeling decorator:
    >>> slow = make_label_dec('slow')
    >>> print slow.__doc__
    Labels a test as 'slow'.

    And one that uses multiple labels and a custom docstring:
    >>> rare = make_label_dec(['slow','hard'],
    ... "Mix labels 'slow' and 'hard' for rare tests.")
    >>> print rare.__doc__
    Mix labels 'slow' and 'hard' for rare tests.

    Now, let's test using this one:
    >>> @rare
    ... def f(): pass
    ...
    >>>
    >>> f.slow
    True
    >>> f.hard
    True
    """

    if isinstance(label,basestring):
        labels = [label]
    else:
        labels = label
        
    # Validate that the given label(s) are OK for use in setattr() by doing a
    # dry run on a dummy function.
    tmp = lambda : None
    for label in labels:
        setattr(tmp,label,True)

    # This is the actual decorator we'll return
    def decor(f):
        for label in labels:
            setattr(f,label,True)
        return f
    
    # Apply the user's docstring, or autogenerate a basic one
    if ds is None:
        ds = "Labels a test as %r." % label
    decor.__doc__ = ds
    
    return decor

#-----------------------------------------------------------------------------
# Decorators for public use

skip_doctest = make_label_dec('skip_doctest',
    """Decorator - mark a function or method for skipping its doctest.

    This decorator allows you to mark a function whose docstring you wish to
    omit from testing, while preserving the docstring for introspection, help,
    etc.""")                              

def skip(msg=''):
    """Decorator - mark a test function for skipping from test suite.

    This function *is* already a decorator, it is not a factory like
    make_label_dec or some of those in decorators_numpy.

    :Parameters:

      func : function
        Test function to be skipped

      msg : string
        Optional message to be added.
      """

    import nose

    def inner(func):

        def wrapper(*a,**k):
            if msg: out = '\n'+msg
            else: out = ''
            raise nose.SkipTest("Skipping test for function: %s%s" %
                                (func.__name__,out))

        return apply_wrapper(wrapper,func)

    return inner

# Decorators to skip certain tests on specific platforms.
skip_win32 = skipif(sys.platform=='win32',"This test does not run under Windows")
skip_linux = skipif(sys.platform=='linux2',"This test does not run under Linux")
skip_osx = skipif(sys.platform=='darwin',"This test does not run under OSX")

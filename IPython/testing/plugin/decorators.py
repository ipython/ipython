"""Decorators for labeling test objects.

Decorators that merely return a modified version of the original
function object are straightforward.  Decorators that return a new
function object need to use
nose.tools.make_decorator(original_function)(decorator) in returning
the decorator, in order to preserve metadata such as function name,
setup and teardown functions and so on - see nose.tools for more
information.

NOTE: This file contains IPython-specific decorators and imports the
numpy.testing.decorators file, which we've copied verbatim.  Any of our own
code will be added at the bottom if we end up extending this.
"""

# Stdlib imports
import inspect

# Third-party imports

# This is Michele Simionato's decorator module, also kept verbatim.
from decorator_msim import decorator

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

def skip_doctest(func):
    """Decorator - mark a function for skipping its doctest.

    This decorator allows you to mark a function whose docstring you wish to
    omit from testing, while preserving the docstring for introspection, help,
    etc."""

    # We just return the function unmodified, but the wrapping has the effect
    # of making the doctest plugin skip the doctest.
    def wrapper(*a,**k):
        return func(*a,**k)

    # Here we use plain 'decorator' and not apply_wrapper, because we don't
    # need all the nose-protection machinery (functions containing doctests
    # can't be full-blown nose tests, so we don't need to prserve
    # setup/teardown).
    return decorator(wrapper,func)


def skip(func):
    """Decorator - mark a test function for skipping from test suite."""

    import nose
    
    def wrapper(*a,**k):
        raise nose.SkipTest("Skipping test for function: %s" %
                            func.__name__)
    
    return apply_wrapper(wrapper,func)

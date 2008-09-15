"""Tests for the decorators we've created for IPython.
"""

# Module imports
# Std lib
import inspect
import sys

# Third party
import nose.tools as nt

# Our own
from IPython.testing import decorators as dec


#-----------------------------------------------------------------------------
# Utilities

# Note: copied from OInspect, kept here so the testing stuff doesn't create
# circular dependencies and is easier to reuse.
def getargspec(obj):
    """Get the names and default values of a function's arguments.

    A tuple of four things is returned: (args, varargs, varkw, defaults).
    'args' is a list of the argument names (it may contain nested lists).
    'varargs' and 'varkw' are the names of the * and ** arguments or None.
    'defaults' is an n-tuple of the default values of the last n arguments.

    Modified version of inspect.getargspec from the Python Standard
    Library."""

    if inspect.isfunction(obj):
        func_obj = obj
    elif inspect.ismethod(obj):
        func_obj = obj.im_func
    else:
        raise TypeError, 'arg is not a Python function'
    args, varargs, varkw = inspect.getargs(func_obj.func_code)
    return args, varargs, varkw, func_obj.func_defaults

#-----------------------------------------------------------------------------
# Testing functions

@dec.skip
def test_deliberately_broken():
    """A deliberately broken test - we want to skip this one."""
    1/0

@dec.skip('foo')
def test_deliberately_broken2():
    """Another deliberately broken test - we want to skip this one."""
    1/0


# Verify that we can correctly skip the doctest for a function at will, but
# that the docstring itself is NOT destroyed by the decorator.
@dec.skip_doctest
def doctest_bad(x,y=1,**k):
    """A function whose doctest we need to skip.

    >>> 1+1
    3
    """
    print 'x:',x
    print 'y:',y
    print 'k:',k


def call_doctest_bad():
    """Check that we can still call the decorated functions.
    
    >>> doctest_bad(3,y=4)
    x: 3
    y: 4
    k: {}
    """
    pass


def test_skip_dt_decorator():
    """Doctest-skipping decorator should preserve the docstring.
    """
    # Careful: 'check' must be a *verbatim* copy of the doctest_bad docstring!
    check = """A function whose doctest we need to skip.

    >>> 1+1
    3
    """
    # Fetch the docstring from doctest_bad after decoration.
    val = doctest_bad.__doc__
    
    assert check==val,"doctest_bad docstrings don't match"

# Doctest skipping should work for class methods too
class foo(object):
    """Foo

    Example:

    >>> 1+1
    2
    """

    @dec.skip_doctest
    def __init__(self,x):
        """Make a foo.

        Example:

        >>> f = foo(3)
        junk
        """
        print 'Making a foo.'
        self.x = x
        
    @dec.skip_doctest
    def bar(self,y):
        """Example:

        >>> f = foo(3)
        >>> f.bar(0)
        boom!
        >>> 1/0
        bam!
        """
        return 1/y

    def baz(self,y):
        """Example:

        >>> f = foo(3)
        Making a foo.
        >>> f.baz(3)
        True
        """
        return self.x==y



def test_skip_dt_decorator2():
    """Doctest-skipping decorator should preserve function signature.
    """
    # Hardcoded correct answer
    dtargs = (['x', 'y'], None, 'k', (1,))
    # Introspect out the value
    dtargsr = getargspec(doctest_bad)
    assert dtargsr==dtargs, \
           "Incorrectly reconstructed args for doctest_bad: %s" % (dtargsr,)


@dec.skip_linux
def test_linux():
    nt.assert_not_equals(sys.platform,'linux2',"This test can't run under linux")

@dec.skip_win32
def test_win32():
    nt.assert_not_equals(sys.platform,'win32',"This test can't run under windows")

@dec.skip_osx
def test_osx():
    nt.assert_not_equals(sys.platform,'darwin',"This test can't run under osx")

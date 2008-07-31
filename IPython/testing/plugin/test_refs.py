# Module imports
# Std lib
import inspect

# Third party

# Our own
import decorators as dec

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

def test_trivial():
    """A trivial passing test."""
    pass


@dec.skip
def test_deliberately_broken():
    """A deliberately broken test - we want to skip this one."""
    1/0


# Verify that we can correctly skip the doctest for a function at will, but
# that the docstring itself is NOT destroyed by the decorator.
@dec.skip_doctest
def doctest_bad(x,y=1,**k):
    """A function whose doctest we need to skip.

    >>> 1+1
    3
    """
    z=2


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


def test_skip_dt_decorator2():
    """Doctest-skipping decorator should preserve function signature.
    """
    # Hardcoded correct answer
    dtargs = (['x', 'y'], None, 'k', (1,))
    # Introspect out the value
    dtargsr = getargspec(doctest_bad)
    assert dtargsr==dtargs, \
           "Incorrectly reconstructed args for doctest_bad: %s" % (dtargsr,)


def doctest_run():
    """Test running a trivial script.

    In [13]: run simplevars.py
    x is: 1
    """
    
#@dec.skip_doctest
def doctest_runvars():
    """Test that variables defined in scripts get loaded correcly via %run.

    In [13]: run simplevars.py
    x is: 1

    In [14]: x
    Out[14]: 1
    """

def doctest_ivars():
    """Test that variables defined interactively are picked up.
    In [5]: zz=1

    In [6]: zz
    Out[6]: 1
    """
    
@dec.skip_doctest
def doctest_refs():
    """DocTest reference holding issues when running scripts.

    In [32]: run show_refs.py
    c referrers: [<type 'dict'>]

    In [33]: map(type,gc.get_referrers(c))
    Out[33]: [<type 'dict'>]
    """

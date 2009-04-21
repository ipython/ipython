"""Tests for the ipdoctest machinery itself.

Note: in a file named test_X, functions whose only test is their docstring (as
a doctest) and which have no test functionality of their own, should be called
'doctest_foo' instead of 'test_foo', otherwise they get double-counted (the
empty function call is counted as a test, which just inflates tests numbers
artificially).
"""

def doctest_simple():
    """ipdoctest must handle simple inputs
    
    In [1]: 1
    Out[1]: 1

    In [2]: print 1
    1
    """


def doctest_run_builtins():
    """Check that %run doesn't damage __builtins__ via a doctest.

    This is similar to the test_run_builtins, but I want *both* forms of the
    test to catch any possible glitches in our testing machinery, since that
    modifies %run somewhat.  So for this, we have both a normal test (below)
    and a doctest (this one).

    In [1]: import tempfile

    In [3]: f = tempfile.NamedTemporaryFile()

    In [4]: f.write('pass\\n')

    In [5]: f.flush()

    In [7]: %run $f.name
    """

def doctest_multiline1():
    """The ipdoctest machinery must handle multiline examples gracefully.

    In [2]: for i in range(10):
       ...:     print i,
       ...:      
    0 1 2 3 4 5 6 7 8 9
    """

    
def doctest_multiline2():
    """Multiline examples that define functions and print output.

    In [7]: def f(x):
       ...:     return x+1
       ...: 

    In [8]: f(1)
    Out[8]: 2

    In [9]: def g(x):
       ...:     print 'x is:',x
       ...:      

    In [10]: g(1)
    x is: 1

    In [11]: g('hello')
    x is: hello
    """


def doctest_multiline3():
    """Multiline examples with blank lines.

    In [12]: def h(x):
       ....:     if x>1:
       ....:         return x**2
       ....:     # To leave a blank line in the input, you must mark it
       ....:     # with a comment character:
       ....:     #
       ....:     # otherwise the doctest parser gets confused.
       ....:     else:
       ....:         return -1
       ....:      

    In [13]: h(5)
    Out[13]: 25

    In [14]: h(1)
    Out[14]: -1

    In [15]: h(0)
    Out[15]: -1
   """

"""These kinds of tests are less than ideal, but at least they run.

This was an old test that was being run interactively in the top-level tests/
directory, which we are removing.  For now putting this here ensures at least
we do run the test, though ultimately this functionality should all be tested
with better-isolated tests that don't rely on the global instance in iptest.
"""
from IPython.utils import py3compat

@py3compat.doctest_refactor_print
def doctest_autocall():
    """
    In [1]: def f1(a,b,c):
       ...:     return a+b+c
       ...: 

    In [2]: def f2(a):
       ...:     return a + a
       ...:   

    In [3]: ;f2 a b c
    Out[3]: 'a b ca b c'

    In [4]: assert _ == "a b ca b c"

    In [5]: ,f1 a b c
    Out[5]: 'abc'

    In [6]: assert _ == 'abc'

    In [7]: print _
    abc

    In [8]: /f1 1,2,3
    Out[8]: 6

    In [9]: assert _ == 6

    In [10]: /f2 4
    Out[10]: 8

    In [11]: assert _ == 8

    In [11]: del f1, f2
    """

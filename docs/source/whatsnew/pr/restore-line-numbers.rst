Restore line numbers for Input
==================================

Line number information in tracebacks from input are restored.
Line numbers from input were removed during the transition to v8 enhanced traceback reporting.

So, instead of::

    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    Input In [3], in <cell line: 1>()
    ----> 1 myfunc(2)

    Input In [2], in myfunc(z)
          1 def myfunc(z):
    ----> 2     foo.boo(z-1)

    File ~/code/python/ipython/foo.py:3, in boo(x)
          2 def boo(x):
    ----> 3     return 1/(1-x)

    ZeroDivisionError: division by zero

The error traceback now looks like::

      ---------------------------------------------------------------------------
      ZeroDivisionError                         Traceback (most recent call last)
      Cell In [3], line 1
      ----> 1 myfunc(2)

      Cell In [2], line 2, in myfunc(z)
            1 def myfunc(z):
      ----> 2     foo.boo(z-1)

      File ~/code/python/ipython/foo.py:3, in boo(x)
            2 def boo(x):
      ----> 3     return 1/(1-x)

      ZeroDivisionError: division by zero

or, with xmode=Plain::

    Traceback (most recent call last):
      Cell In [12], line 1
        myfunc(2)
      Cell In [6], line 2 in myfunc
        foo.boo(z-1)
      File ~/code/python/ipython/foo.py:3 in boo
        return 1/(1-x)
    ZeroDivisionError: division by zero

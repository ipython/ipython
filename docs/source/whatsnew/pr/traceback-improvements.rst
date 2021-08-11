Traceback improvements
======================

Previously, error tracebacks for errors happening in code cells were showing a hash, the one used for compiling the Python AST::

    In [1]: def foo():
    ...:     return 3 / 0
    ...:

    In [2]: foo()
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    <ipython-input-2-c19b6d9633cf> in <module>
    ----> 1 foo()

    <ipython-input-1-1595a74c32d5> in foo()
        1 def foo():
    ----> 2     return 3 / 0
        3

    ZeroDivisionError: division by zero

The error traceback is now correctly formatted, showing the cell number in which the error happened::

    In [1]: def foo():
    ...:     return 3 / 0
    ...:

    In [2]: foo()
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    In [2], in <module>
    ----> 1 foo()

    In [1], in foo()
        1 def foo():
    ----> 2     return 3 / 0

    ZeroDivisionError: division by zero

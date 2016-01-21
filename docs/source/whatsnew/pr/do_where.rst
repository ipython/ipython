IPython debugger (IPdb) now supports the number of context lines for the
``where`` (and ``w``) commands. The `context` keyword is also available in various APIs.

.. code::

    In [2]: def foo():
    ...:     1
    ...:     2
    ...:     3
    ...:     4
    ...:     5
    ...:     raise ValueError('6 is not acceptable')
    ...:     7
    ...:     8
    ...:     9
    ...:     10
    ...:

    In [3]: foo()
    ----------------------------------------------------
    ValueError         Traceback (most recent call last)
    <ipython-input-3> in <module>()
    ----> 1 foo()

    <ipython-input-2> in foo()
        5     4
        6     5
    ----> 7     raise ValueError('6 is not acceptable')
        8     7
        9     8

    ValueError: 6 is not acceptable

    In [4]: debug
    > <ipython-input-2>(7)foo()
        5     4
        6     5
    ----> 7     raise ValueError('6 is not acceptable')
        8     7
        9     8

    ipdb> where 1
    <ipython-input-3>(1)<module>()
    ----> 1 foo()

    > <ipython-input-2>(7)foo()
    ----> 7     raise ValueError('6 is not acceptable')

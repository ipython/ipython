Doctest xmode
=============

Added a new ``%xmode Doctest`` mode that formats tracebacks for easy
copy-paste into Python doctests. The output shows only the traceback
header, a literal ellipsis, and the exception line::

    Traceback (most recent call last):
        ...
    ZeroDivisionError: division by zero

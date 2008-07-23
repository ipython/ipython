"""Simple example using doctests.

This file just contains doctests both using plain python and IPython prompts.
All tests should be loaded by nose.
"""

def pyfunc():
    """Some pure python tests...

    >>> pyfunc()
    'pyfunc'

    >>> import os

    >>> 2+3
    5

    >>> for i in range(3):
    ...     print i,
    ...     print i+1,
    ...
    0 1 1 2 2 3
    """

    return 'pyfunc'

def ipfunc():
    """Some ipython tests...

    In [1]: import os

    In [2]: cd /
    /

    In [3]: 2+3
    Out[3]: 5

    In [26]: for i in range(3):
       ....:     print i,
       ....:     print i+1,
       ....:
    0 1 1 2 2 3


    Examples that access the operating system work:

    In [1]: !echo hello
    hello

    In [2]: !echo hello > /tmp/foo

    In [3]: !cat /tmp/foo
    hello

    In [4]: rm -f /tmp/foo

    It's OK to use '_' for the last result, but do NOT try to use IPython's
    numbered history of _NN outputs, since those won't exist under the
    doctest environment:

    In [7]: 3+4
    Out[7]: 7

    In [8]: _+3
    Out[8]: 10

    In [9]: ipfunc()
    Out[9]: 'ipfunc'
    """

    return 'ipfunc'


if 1:
    def ranfunc():
        """A function with some random output.

           >>> 1+3
           junk goes here...  #random

           >>> 1+3
           4

           >>> 1+2
           again,  anything goes #random
           if multiline, the random mark is only needed in teh first line.

           >>> 1+3
           4

           >>> ranfunc()
           'ranfunc'
        """
        return 'ranfunc'


if 0:
    def ranf2():
        """A function whose examples'output are all to be ignored.

        Examples:

        #all-random

           >>> 1+3
           junk goes here...

           >>> 1+3
           klasdfj;

           >>> 1+2
           again,  anything goes
           blah...

        """
        return 'ranf2'


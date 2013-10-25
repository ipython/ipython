Single codebase Python 3 support
--------------------------------

IPython previously supported Python 3 by running 2to3 during setup. We
have now switched to a single codebase which runs natively on Python 2.7
and 3.3.

For notes on how to maintain this, see :doc:`/development/pycompat`.

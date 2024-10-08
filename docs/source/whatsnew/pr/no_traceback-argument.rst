no_traceback argument to :okexcept: option
==========================================

The ``:okexcept:`` option of the ``.. ipython::`` directive can now have an
optional argument ``no_traceback`` that prevents printing of the (potentially
long) traceback. Only the exception is printed in this case.

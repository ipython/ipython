.. _parallel_asyncresult:

======================
The AsyncResult object
======================

In non-blocking mode, :meth:`apply` submits the command to be executed and
then returns a :class:`~.AsyncResult` object immediately. The
AsyncResult object gives you a way of getting a result at a later
time through its :meth:`get` method, but it also collects metadata
on execution.


Beyond multiprocessing's AsyncResult
====================================

.. Note::

    The :class:`~.AsyncResult` object provides a superset of the interface in 
    :py:class:`multiprocessing.pool.AsyncResult`.  See the 
    `official Python documentation <http://docs.python.org/library/multiprocessing#multiprocessing.pool.AsyncResult>`_
    for more on the basics of this interface.

Our AsyncResult objects add a number of convenient features for working with
parallel results, beyond what is provided by the original AsyncResult.


get_dict
--------

First, is :meth:`.AsyncResult.get_dict`, which pulls results as a dictionary
keyed by engine_id, rather than a flat list.  This is useful for quickly
coordinating or distributing information about all of the engines.

As an example, here is a quick call that gives every engine a dict showing
the PID of every other engine:

.. sourcecode:: ipython

    In [10]: ar = rc[:].apply_async(os.getpid)
    In [11]: pids = ar.get_dict()
    In [12]: rc[:]['pid_map'] = pids

This trick is particularly useful when setting up inter-engine communication,
as in IPython's :file:`examples/parallel/interengine` examples.


Metadata
========

IPython.parallel tracks some metadata about the tasks, which is stored
in the :attr:`.Client.metadata` dict.  The AsyncResult object gives you an
interface for this information as well, including timestamps stdout/err,
and engine IDs.


Timing
------

IPython tracks various timestamps as :py:class:`.datetime` objects,
and the AsyncResult object has a few properties that turn these into useful
times (in seconds as floats).

For use while the tasks are still pending:

* :attr:`ar.elapsed` is just the elapsed seconds since submission, for use
  before the AsyncResult is complete.
* :attr:`ar.progress` is the number of tasks that have completed.  Fractional progress
  would be::

    1.0 * ar.progress / len(ar)

* :meth:`AsyncResult.wait_interactive` will wait for the result to finish, but
  print out status updates on progress and elapsed time while it waits.

For use after the tasks are done:

* :attr:`ar.serial_time` is the sum of the computation time of all of the tasks
  done in parallel.
* :attr:`ar.wall_time` is the time between the first task submitted and last result
  received.  This is the actual cost of computation, including IPython overhead. 
  

.. note::

  wall_time is only precise if the Client is waiting for results when
  the task finished, because the `received` timestamp is made when the result is
  unpacked by the Client, triggered by the :meth:`~Client.spin` call. If you
  are doing work in the Client, and not waiting/spinning, then `received` might
  be artificially high.

An often interesting metric is the time it actually cost to do the work in parallel
relative to the serial computation, and this can be given simply with

.. sourcecode:: python

    speedup = ar.serial_time / ar.wall_time


Map results are iterable!
=========================

When an AsyncResult object has multiple results (e.g. the :class:`~AsyncMapResult`
object), you can actually iterate through results themselves, and act on them as they arrive:

.. literalinclude:: ../../../examples/parallel/itermapresult.py
    :language: python
    :lines: 20-67
    
That is to say, if you treat an AsyncMapResult as if it were a list of your actual
results, it should behave as you would expect, with the only difference being
that you can start iterating through the results before they have even been computed.

This lets you do a dumb version of map/reduce with the builtin Python functions,
and the only difference between doing this locally and doing it remotely in parallel
is using the asynchronous view.map instead of the builtin map.


Here is a simple one-line RMS (root-mean-square) implemented with Python's builtin map/reduce.

.. sourcecode:: ipython

    In [38]: X = np.linspace(0,100)

    In [39]: from math import sqrt

    In [40]: add = lambda a,b: a+b

    In [41]: sq = lambda x: x*x

    In [42]: sqrt(reduce(add, map(sq, X)) / len(X))
    Out[42]: 58.028845747399714

    In [43]: sqrt(reduce(add, view.map(sq, X)) / len(X))
    Out[43]: 58.028845747399714

To break that down:

1. ``map(sq, X)`` Compute the square of each element in the list (locally, or in parallel)
2. ``reduce(add, sqX) / len(X)`` compute the mean by summing over the list (or AsyncMapResult)
   and dividing by the size
3. take the square root of the resulting number

.. seealso::

    When AsyncResult or the AsyncMapResult don't provide what you need (for instance,
    handling individual results as they arrive, but with metadata), you can always
    just split the original result's ``msg_ids`` attribute, and handle them as you like.
    
    For an example of this, see :file:`examples/parallel/customresult.py`

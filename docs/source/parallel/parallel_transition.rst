.. _parallel_transition:

=====================================================
Transitioning from IPython.kernel to IPython.parallel
=====================================================


We have rewritten our parallel computing tools to use 0MQ_ and Tornado_.  The redesign
has resulted in dramatically improved performance, as well as (we think), an improved
interface for executing code remotely.  This doc is to help users of IPython.kernel
transition their codes to the new code.

.. _0MQ: http://zeromq.org
.. _Tornado: https://github.com/facebook/tornado


Processes
=========

The process model for the new parallel code is very similar to that of IPython.kernel. There is
still a Controller, Engines, and Clients. However, the the Controller is now split into multiple
processes, and can even be split across multiple machines. There does remain a single
ipcontroller script for starting all of the controller processes.


.. note::

    TODO: fill this out after config system is updated


.. seealso::

    Detailed :ref:`Parallel Process <parallel_process>` doc for configuring and launching
    IPython processes.

Creating a Client
=================

Creating a client with default settings has not changed much, though the extended options have.
One significant change is that there are no longer multiple Client classes to represent the
various execution models. There is just one low-level Client object for connecting to the
cluster, and View objects are created from that Client that provide the different interfaces for
execution.


To create a new client, and set up the default direct and load-balanced objects:

.. sourcecode:: ipython

    # old
    In [1]: from IPython.kernel import client as kclient
    
    In [2]: mec = kclient.MultiEngineClient()

    In [3]: tc = kclient.TaskClient()
    
    # new 
    In [1]: from IPython.parallel import Client
    
    In [2]: rc = Client()

    In [3]: dview = rc[:]
    
    In [4]: lbview = rc.load_balanced_view()

Apply
=====

The main change to the API is the addition of the :meth:`apply` to the View objects. This is a
method that takes `view.apply(f,*args,**kwargs)`, and calls `f(*args, **kwargs)` remotely on one
or more engines, returning the result. This means that the natural unit of remote execution
is no longer a string of Python code, but rather a Python function.

* non-copying sends (track)
* remote References

The flags for execution have also changed.  Previously, there was only `block` denoting whether
to wait for results.  This remains, but due to the addition of fully non-copying sends of 
arrays and buffers, there is also a `track` flag, which instructs PyZMQ to produce a :class:`MessageTracker` that will let you know when it is safe again to edit arrays in-place.

The result of a non-blocking call to `apply` is now an :doc:`AsyncResult object <asyncresult>`.

MultiEngine to DirectView
=========================

The multiplexing interface previously provided by the MultiEngineClient is now provided by the
DirectView. Once you have a Client connected, you can create a DirectView with index-access
to the client (``view = client[1:5]``). The core methods for
communicating with engines remain: `execute`, `run`, `push`, `pull`, `scatter`, `gather`. These
methods all behave in much the same way as they did on a MultiEngineClient.


.. sourcecode:: ipython

    # old
    In [2]: mec.execute('a=5', targets=[0,1,2])
    
    # new
    In [2]: view.execute('a=5', targets=[0,1,2])
    # or
    In [2]: rc[0,1,2].execute('a=5')
    

This extends to any method that communicates with the engines. 

Requests of the Hub (queue status, etc.) are no-longer asynchronous, and do not take a `block`
argument.


* :meth:`get_ids` is now the property :attr:`ids`, which is passively updated by the Hub (no
  need for network requests for an up-to-date list).
* :meth:`barrier` has been renamed to :meth:`wait`, and now takes an optional timeout. :meth:`flush` is removed, as it is redundant with :meth:`wait`
* :meth:`zip_pull` has been removed
* :meth:`keys` has been removed, but is easily implemented as::

    dview.apply(lambda : globals().keys())

* :meth:`push_function` and :meth:`push_serialized` are removed, as :meth:`push` handles 
  functions without issue.
 
.. seealso::

    :ref:`Our Direct Interface doc <parallel_multiengine>` for a simple tutorial with the 
    DirectView.


The other major difference is the use of :meth:`apply`. When remote work is simply functions,
the natural return value is the actual Python objects. It is no longer the recommended pattern
to use stdout as your results, due to stream decoupling and the asynchronous nature of how the
stdout streams are handled in the new system.

Task to LoadBalancedView
========================

Load-Balancing has changed more than Multiplexing.  This is because there is no longer a notion
of a StringTask or a MapTask, there are simply Python functions to call.  Tasks are now
simpler, because they are no longer composites of push/execute/pull/clear calls, they are
a single function that takes arguments, and returns objects.

The load-balanced interface is provided by the :class:`LoadBalancedView` class, created by the client:

.. sourcecode:: ipython

    In [10]: lbview = rc.load_balanced_view()
    
    # load-balancing can also be restricted to a subset of engines:
    In [10]: lbview = rc.load_balanced_view([1,2,3])

A simple task would consist of sending some data, calling a function on that data, plus some
data that was resident on the engine already, and then pulling back some results.  This can
all be done with a single function.


Let's say you want to compute the dot product of two matrices, one of which resides on the
engine, and another resides on the client.  You might construct a task that looks like this:

.. sourcecode:: ipython

    In [10]: st = kclient.StringTask("""
                import numpy
                C=numpy.dot(A,B)
                """,
                push=dict(B=B),
                pull='C'
                )
    
    In [11]: tid = tc.run(st)
    
    In [12]: tr = tc.get_task_result(tid)
    
    In [13]: C = tc['C']

In the new code, this is simpler:

.. sourcecode:: ipython

    In [10]: import numpy
    
    In [11]: from IPython.parallel import Reference
    
    In [12]: ar = lbview.apply(numpy.dot, Reference('A'), B)
    
    In [13]: C = ar.get()

Note the use of ``Reference`` This is a convenient representation of an object that exists
in the engine's namespace, so you can pass remote objects as arguments to your task functions.

Also note that in the kernel model, after the task is run, 'A', 'B', and 'C' are all defined on
the engine. In order to deal with this, there is also a `clear_after` flag for Tasks to prevent
pollution of the namespace, and bloating of engine memory. This is not necessary with the new
code, because only those objects explicitly pushed (or set via `globals()`) will be resident on
the engine beyond the duration of the task.

.. seealso::

    Dependencies also work very differently than in IPython.kernel.  See our :ref:`doc on Dependencies<parallel_dependencies>` for details.

.. seealso::

    :ref:`Our Task Interface doc <parallel_task>` for a simple tutorial with the 
    LoadBalancedView.


PendingResults to AsyncResults
------------------------------

With the departure from Twisted, we no longer have the :class:`Deferred` class for representing
unfinished results. For this, we have an AsyncResult object, based on the object of the same
name in the built-in :mod:`multiprocessing.pool` module. Our version provides a superset of that
interface.

However, unlike in IPython.kernel, we do not have PendingDeferred, PendingResult, or TaskResult
objects. Simply this one object, the AsyncResult. Every asynchronous (`block=False`) call
returns one.

The basic methods of an AsyncResult are:

.. sourcecode:: python

    AsyncResult.wait([timeout]): # wait for the result to arrive
    AsyncResult.get([timeout]): # wait for the result to arrive, and then return it
    AsyncResult.metadata: # dict of extra information about execution.

There are still some things that behave the same as IPython.kernel:

.. sourcecode:: ipython

    # old
    In [5]: pr = mec.pull('a', targets=[0,1], block=False)
    In [6]: pr.r
    Out[6]: [5, 5]

    # new
    In [5]: ar = dview.pull('a', targets=[0,1], block=False)
    In [6]: ar.r
    Out[6]: [5, 5]

The ``.r`` or ``.result`` property simply calls :meth:`get`, waiting for and returning the
result.

.. seealso::

    :doc:`AsyncResult details <asyncresult>`



.. _parallel_multiengine:

==========================
IPython's Direct interface
==========================

The direct, or multiengine, interface represents one possible way of working with a set of
IPython engines. The basic idea behind the multiengine interface is that the
capabilities of each engine are directly and explicitly exposed to the user.
Thus, in the multiengine interface, each engine is given an id that is used to
identify the engine and give it work to do. This interface is very intuitive
and is designed with interactive usage in mind, and is the best place for
new users of IPython to begin.

Starting the IPython controller and engines
===========================================

To follow along with this tutorial, you will need to start the IPython
controller and four IPython engines. The simplest way of doing this is to use
the :command:`ipcluster` command::

    $ ipcluster start -n 4
    
For more detailed information about starting the controller and engines, see
our :ref:`introduction <parallel_overview>` to using IPython for parallel computing.

Creating a ``DirectView`` instance
==================================

The first step is to import the IPython :mod:`IPython.parallel`
module and then create a :class:`.Client` instance:

.. sourcecode:: ipython

    In [1]: from IPython.parallel import Client
    
    In [2]: rc = Client()

This form assumes that the default connection information (stored in
:file:`ipcontroller-client.json` found in :file:`IPYTHONDIR/profile_default/security`) is
accurate. If the controller was started on a remote machine, you must copy that connection
file to the client machine, or enter its contents as arguments to the Client constructor:

.. sourcecode:: ipython

    # If you have copied the json connector file from the controller:
    In [2]: rc = Client('/path/to/ipcontroller-client.json')
    # or to connect with a specific profile you have set up:
    In [3]: rc = Client(profile='mpi')
    

To make sure there are engines connected to the controller, users can get a list
of engine ids:

.. sourcecode:: ipython

    In [3]: rc.ids
    Out[3]: [0, 1, 2, 3]

Here we see that there are four engines ready to do work for us.

For direct execution, we will make use of a :class:`DirectView` object, which can be
constructed via list-access to the client:

.. sourcecode:: ipython

    In [4]: dview = rc[:] # use all engines

.. seealso::

    For more information, see the in-depth explanation of :ref:`Views <parallel_details>`.


Quick and easy parallelism
==========================

In many cases, you simply want to apply a Python function to a sequence of
objects, but *in parallel*. The client interface provides a simple way
of accomplishing this: using the DirectView's :meth:`~DirectView.map` method.

Parallel map
------------

Python's builtin :func:`map` functions allows a function to be applied to a
sequence element-by-element. This type of code is typically trivial to
parallelize. In fact, since IPython's interface is all about functions anyway,
you can just use the builtin :func:`map` with a :class:`RemoteFunction`, or a 
DirectView's :meth:`map` method:

.. sourcecode:: ipython

    In [62]: serial_result = map(lambda x:x**10, range(32))
    
    In [63]: parallel_result = dview.map_sync(lambda x: x**10, range(32))

    In [67]: serial_result==parallel_result
    Out[67]: True


.. note::

    The :class:`DirectView`'s version of :meth:`map` does
    not do dynamic load balancing. For a load balanced version, use a
    :class:`LoadBalancedView`.

.. seealso::
    
    :meth:`map` is implemented via :class:`ParallelFunction`.

Remote function decorators
--------------------------

Remote functions are just like normal functions, but when they are called,
they execute on one or more engines, rather than locally. IPython provides
two decorators:

.. sourcecode:: ipython

    In [10]: @dview.remote(block=True)
       ....: def getpid():
       ....:     import os
       ....:     return os.getpid()
       ....: 

    In [11]: getpid()
    Out[11]: [12345, 12346, 12347, 12348]

The ``@parallel`` decorator creates parallel functions, that break up an element-wise
operations and distribute them, reconstructing the result.

.. sourcecode:: ipython

    In [12]: import numpy as np
    
    In [13]: A = np.random.random((64,48))
    
    In [14]: @dview.parallel(block=True)
       ....: def pmul(A,B):
       ....:     return A*B
    
    In [15]: C_local = A*A
    
    In [16]: C_remote = pmul(A,A)
    
    In [17]: (C_local == C_remote).all()
    Out[17]: True

Calling a ``@parallel`` function *does not* correspond to map. It is used for splitting
element-wise operations that operate on a sequence or array.  For ``map`` behavior,
parallel functions do have a map method.

====================    ============================    =============================
call                    pfunc(seq)                      pfunc.map(seq)
====================    ============================    =============================
# of tasks              # of engines (1 per engine)     # of engines (1 per engine)
# of remote calls       # of engines (1 per engine)     ``len(seq)``
argument to remote      ``seq[i:j]`` (sub-sequence)     ``seq[i]`` (single element)
====================    ============================    =============================

A quick example to illustrate the difference in arguments for the two modes:

.. sourcecode:: ipython

    In [16]: @dview.parallel(block=True)
       ....: def echo(x):
       ....:     return str(x)
       ....: 

    In [17]: echo(range(5))
    Out[17]: ['[0, 1]', '[2]', '[3]', '[4]']

    In [18]: echo.map(range(5))
    Out[18]: ['0', '1', '2', '3', '4']


.. seealso::

    See the :func:`~.remotefunction.parallel` and :func:`~.remotefunction.remote`
    decorators for options.

Calling Python functions
========================

The most basic type of operation that can be performed on the engines is to
execute Python code or call Python functions. Executing Python code can be
done in blocking or non-blocking mode (non-blocking is default) using the
:meth:`.View.execute` method, and calling functions can be done via the
:meth:`.View.apply` method.

apply
-----

The main method for doing remote execution (in fact, all methods that
communicate with the engines are built on top of it), is :meth:`View.apply`.

We strive to provide the cleanest interface we can, so `apply` has the following
signature:

.. sourcecode:: python

    view.apply(f, *args, **kwargs)

There are various ways to call functions with IPython, and these flags are set as
attributes of the View.  The ``DirectView`` has just two of these flags:

dv.block : bool
    whether to wait for the result, or return an :class:`AsyncResult` object
    immediately
dv.track : bool
    whether to instruct pyzmq to track when zeromq is done sending the message.
    This is primarily useful for non-copying sends of numpy arrays that you plan to
    edit in-place.  You need to know when it becomes safe to edit the buffer
    without corrupting the message.
dv.targets : int, list of ints
    which targets this view is associated with.


Creating a view is simple: index-access on a client creates a :class:`.DirectView`.

.. sourcecode:: ipython

    In [4]: view = rc[1:3]
    Out[4]: <DirectView [1, 2]>

    In [5]: view.apply<tab>
    view.apply  view.apply_async  view.apply_sync

For convenience, you can set block temporarily for a single call with the extra sync/async methods.

Blocking execution
------------------

In blocking mode, the :class:`.DirectView` object (called ``dview`` in
these examples) submits the command to the controller, which places the
command in the engines' queues for execution. The :meth:`apply` call then
blocks until the engines are done executing the command:

.. sourcecode:: ipython

    In [2]: dview = rc[:] # A DirectView of all engines
    In [3]: dview.block=True
    In [4]: dview['a'] = 5

    In [5]: dview['b'] = 10

    In [6]: dview.apply(lambda x: a+b+x, 27)
    Out[6]: [42, 42, 42, 42]

You can also select blocking execution on a call-by-call basis with the :meth:`apply_sync`
method:

.. sourcecode:: ipython

    In [7]: dview.block=False

    In [8]: dview.apply_sync(lambda x: a+b+x, 27)
    Out[8]: [42, 42, 42, 42]

Python commands can be executed as strings on specific engines by using a View's ``execute``
method:

.. sourcecode:: ipython

    In [6]: rc[::2].execute('c=a+b')

    In [7]: rc[1::2].execute('c=a-b')

    In [8]: dview['c'] # shorthand for dview.pull('c', block=True)
    Out[8]: [15, -5, 15, -5]


Non-blocking execution
----------------------

In non-blocking mode, :meth:`apply` submits the command to be executed and
then returns a :class:`AsyncResult` object immediately. The
:class:`AsyncResult` object gives you a way of getting a result at a later
time through its :meth:`get` method.

.. seealso::

    Docs on the :ref:`AsyncResult <parallel_asyncresult>` object.

This allows you to quickly submit long running commands without blocking your
local Python/IPython session:

.. sourcecode:: ipython
    
    # define our function
    In [6]: def wait(t):
      ....:     import time
      ....:     tic = time.time()
      ....:     time.sleep(t)
      ....:     return time.time()-tic
    
    # In non-blocking mode
    In [7]: ar = dview.apply_async(wait, 2)

    # Now block for the result
    In [8]: ar.get()
    Out[8]: [2.0006198883056641, 1.9997570514678955, 1.9996809959411621, 2.0003249645233154]

    # Again in non-blocking mode
    In [9]: ar = dview.apply_async(wait, 10)

    # Poll to see if the result is ready
    In [10]: ar.ready()
    Out[10]: False
    
    # ask for the result, but wait a maximum of 1 second:
    In [45]: ar.get(1)
    ---------------------------------------------------------------------------
    TimeoutError                              Traceback (most recent call last)
    /home/you/<ipython-input-45-7cd858bbb8e0> in <module>()
    ----> 1 ar.get(1)

    /path/to/site-packages/IPython/parallel/asyncresult.pyc in get(self, timeout)
         62                 raise self._exception
         63         else:
    ---> 64             raise error.TimeoutError("Result not ready.")
         65 
         66     def ready(self):

    TimeoutError: Result not ready.

.. Note::

    Note the import inside the function. This is a common model, to ensure
    that the appropriate modules are imported where the task is run. You can
    also manually import modules into the engine(s) namespace(s) via 
    :meth:`view.execute('import numpy')`.

Often, it is desirable to wait until a set of :class:`AsyncResult` objects
are done. For this, there is a the method :meth:`wait`. This method takes a
tuple of :class:`AsyncResult` objects (or `msg_ids` or indices to the client's History),
and blocks until all of the associated results are ready:

.. sourcecode:: ipython

    In [72]: dview.block=False

    # A trivial list of AsyncResults objects
    In [73]: pr_list = [dview.apply_async(wait, 3) for i in range(10)]

    # Wait until all of them are done
    In [74]: dview.wait(pr_list)

    # Then, their results are ready using get() or the `.r` attribute
    In [75]: pr_list[0].get()
    Out[75]: [2.9982571601867676, 2.9982588291168213, 2.9987530708312988, 2.9990990161895752]



The ``block`` and ``targets`` keyword arguments and attributes
--------------------------------------------------------------

Most DirectView methods (excluding :meth:`apply`) accept ``block`` and
``targets`` as keyword arguments. As we have seen above, these keyword arguments control the
blocking mode and which engines the command is applied to. The :class:`View` class also has
:attr:`block` and :attr:`targets` attributes that control the default behavior when the keyword
arguments are not provided. Thus the following logic is used for :attr:`block` and :attr:`targets`:

* If no keyword argument is provided, the instance attributes are used.
* The Keyword arguments, if provided overrides the instance attributes for
  the duration of a single call.
  
The following examples demonstrate how to use the instance attributes:

.. sourcecode:: ipython

    In [16]: dview.targets = [0,2]
    
    In [17]: dview.block = False

    In [18]: ar = dview.apply(lambda : 10)

    In [19]: ar.get()
    Out[19]: [10, 10]

    In [20]: dview.targets = v.client.ids # all engines (4)
    
    In [21]: dview.block = True

    In [22]: dview.apply(lambda : 42)
    Out[22]: [42, 42, 42, 42]

The :attr:`block` and :attr:`targets` instance attributes of the
:class:`.DirectView` also determine the behavior of the parallel magic commands.

.. seealso::

    See the documentation of the :ref:`Parallel Magics <parallel_magics>`.


Moving Python objects around
============================

In addition to calling functions and executing code on engines, you can
transfer Python objects to and from your IPython session and the engines. In
IPython, these operations are called :meth:`push` (sending an object to the
engines) and :meth:`pull` (getting an object from the engines).

Basic push and pull
-------------------

Here are some examples of how you use :meth:`push` and :meth:`pull`:

.. sourcecode:: ipython

    In [38]: dview.push(dict(a=1.03234,b=3453))
    Out[38]: [None,None,None,None]

    In [39]: dview.pull('a')
    Out[39]: [ 1.03234, 1.03234, 1.03234, 1.03234]

    In [40]: dview.pull('b', targets=0)
    Out[40]: 3453

    In [41]: dview.pull(('a','b'))
    Out[41]: [ [1.03234, 3453], [1.03234, 3453], [1.03234, 3453], [1.03234, 3453] ]
    
    In [42]: dview.push(dict(c='speed'))
    Out[42]: [None,None,None,None]

In non-blocking mode :meth:`push` and :meth:`pull` also return
:class:`AsyncResult` objects:

.. sourcecode:: ipython

    In [48]: ar = dview.pull('a', block=False)

    In [49]: ar.get()
    Out[49]: [1.03234, 1.03234, 1.03234, 1.03234]


Dictionary interface
--------------------

Since a Python namespace is just a :class:`dict`, :class:`DirectView` objects provide
dictionary-style access by key and methods such as :meth:`get` and
:meth:`update` for convenience. This make the remote namespaces of the engines
appear as a local dictionary. Underneath, these methods call :meth:`apply`:

.. sourcecode:: ipython

    In [51]: dview['a']=['foo','bar']

    In [52]: dview['a']
    Out[52]: [ ['foo', 'bar'], ['foo', 'bar'], ['foo', 'bar'], ['foo', 'bar'] ]

Scatter and gather
------------------

Sometimes it is useful to partition a sequence and push the partitions to
different engines. In MPI language, this is know as scatter/gather and we
follow that terminology. However, it is important to remember that in
IPython's :class:`Client` class, :meth:`scatter` is from the
interactive IPython session to the engines and :meth:`gather` is from the
engines back to the interactive IPython session. For scatter/gather operations
between engines, MPI, pyzmq, or some other direct interconnect should be used.

.. sourcecode:: ipython

    In [58]: dview.scatter('a',range(16))
    Out[58]: [None,None,None,None]

    In [59]: dview['a']
    Out[59]: [ [0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15] ]

    In [60]: dview.gather('a')
    Out[60]: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

Other things to look at
=======================

How to do parallel list comprehensions
--------------------------------------

In many cases list comprehensions are nicer than using the map function. While
we don't have fully parallel list comprehensions, it is simple to get the
basic effect using :meth:`scatter` and :meth:`gather`:

.. sourcecode:: ipython

    In [66]: dview.scatter('x',range(64))

    In [67]: %px y = [i**10 for i in x]
    Parallel execution on engines: [0, 1, 2, 3]

    In [68]: y = dview.gather('y')

    In [69]: print y
    [0, 1, 1024, 59049, 1048576, 9765625, 60466176, 282475249, 1073741824,...]

Remote imports
--------------

Sometimes you will want to import packages both in your interactive session
and on your remote engines.  This can be done with the :class:`ContextManager`
created by a DirectView's :meth:`sync_imports` method:

.. sourcecode:: ipython

    In [69]: with dview.sync_imports():
       ....:     import numpy
    importing numpy on engine(s)

Any imports made inside the block will also be performed on the view's engines.
sync_imports also takes a `local` boolean flag that defaults to True, which specifies
whether the local imports should also be performed.  However, support for `local=False`
has not been implemented, so only packages that can be imported locally will work
this way.

You can also specify imports via the ``@require`` decorator.  This is a decorator
designed for use in Dependencies, but can be used to handle remote imports as well.
Modules or module names passed to ``@require`` will be imported before the decorated
function is called.  If they cannot be imported, the decorated function will never
execute and will fail with an UnmetDependencyError. Failures of single Engines will
be collected and raise a CompositeError, as demonstrated in the next section.

.. sourcecode:: ipython

    In [69]: from IPython.parallel import require

    In [70]: @require('re'):
       ....: def findall(pat, x):
       ....:     # re is guaranteed to be available
       ....:     return re.findall(pat, x)
          
    # you can also pass modules themselves, that you already have locally:
    In [71]: @require(time):
       ....: def wait(t):
       ....:     time.sleep(t)
       ....:     return t

.. note::

    :func:`sync_imports` does not allow ``import foo as bar`` syntax,
    because the assignment represented by the ``as bar`` part is not
    available to the import hook.


.. _parallel_exceptions:

Parallel exceptions
-------------------

In the multiengine interface, parallel commands can raise Python exceptions,
just like serial commands. But it is a little subtle, because a single
parallel command can actually raise multiple exceptions (one for each engine
the command was run on). To express this idea, we have a
:exc:`CompositeError` exception class that will be raised in most cases. The
:exc:`CompositeError` class is a special type of exception that wraps one or
more other types of exceptions. Here is how it works:

.. sourcecode:: ipython

    In [78]: dview.block = True
    
    In [79]: dview.execute("1/0")
    [0:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

    [1:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

    [2:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

    [3:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

Notice how the error message printed when :exc:`CompositeError` is raised has
information about the individual exceptions that were raised on each engine.
If you want, you can even raise one of these original exceptions:

.. sourcecode:: ipython

    In [80]: try:
       ....:     dview.execute('1/0', block=True)
       ....: except parallel.error.CompositeError, e:
       ....:     e.raise_exception()
       ....: 
       ....: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

If you are working in IPython, you can simple type ``%debug`` after one of
these :exc:`CompositeError` exceptions is raised, and inspect the exception
instance:

.. sourcecode:: ipython

    In [81]: dview.execute('1/0')
    [0:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

    [1:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

    [2:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero

    [3:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero
    
    In [82]: %debug
    > /.../site-packages/IPython/parallel/client/asyncresult.py(125)get()
        124             else:
    --> 125                 raise self._exception
        126         else:
    
    # Here, self._exception is the CompositeError instance:
    
    ipdb> e = self._exception
    ipdb> e
    CompositeError(4)
    
    # we can tab-complete on e to see available methods:
    ipdb> e.<TAB>
    e.args               e.message            e.traceback
    e.elist              e.msg
    e.ename              e.print_traceback
    e.engine_info        e.raise_exception
    e.evalue             e.render_traceback
    
    # We can then display the individual tracebacks, if we want:
    ipdb> e.print_traceback(1)
    [1:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero


Since you might have 100 engines, you probably don't want to see 100 tracebacks
for a simple NameError because of a typo.
For this reason, CompositeError truncates the list of exceptions it will print
to :attr:`CompositeError.tb_limit` (default is five).
You can change this limit to suit your needs with:

.. sourcecode:: ipython

    In [20]: from IPython.parallel import CompositeError
    In [21]: CompositeError.tb_limit = 1
    In [22]: %px a=b
    [0:execute]: 
    ---------------------------------------------------------------------------
    NameError                                 Traceback (most recent call last)
    ----> 1 a=b
    NameError: name 'b' is not defined

    ... 3 more exceptions ...


All of this same error handling magic even works in non-blocking mode:

.. sourcecode:: ipython

    In [83]: dview.block=False

    In [84]: ar = dview.execute('1/0')

    In [85]: ar.get()
    [0:execute]: 
    ---------------------------------------------------------------------------
    ZeroDivisionError                         Traceback (most recent call last)
    ----> 1 1/0
    ZeroDivisionError: integer division or modulo by zero
    
    ... 3 more exceptions ...

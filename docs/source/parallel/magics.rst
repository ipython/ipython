.. _parallel_magics:

=======================
Parallel Magic Commands
=======================

We provide a few IPython magic commands
that make it a bit more pleasant to execute Python commands on the engines interactively.
These are mainly shortcuts to :meth:`.DirectView.execute`
and :meth:`.AsyncResult.display_outputs` methods respectively.

These magics will automatically become available when you create a Client:

.. sourcecode:: ipython

    In [2]: rc = parallel.Client()

The initially active View will have attributes ``targets='all', block=True``,
which is a blocking view of all engines, evaluated at request time
(adding/removing engines will change where this view's tasks will run).

The Magics
==========

%px
---

The %px magic executes a single Python command on the engines
specified by the :attr:`targets` attribute of the :class:`DirectView` instance:

.. sourcecode:: ipython

    # import numpy here and everywhere
    In [25]: with rc[:].sync_imports():
       ....:    import numpy
    importing numpy on engine(s)

    In [27]: %px a = numpy.random.rand(2,2)
    Parallel execution on engines: [0, 1, 2, 3]

    In [28]: %px numpy.linalg.eigvals(a)
    Parallel execution on engines: [0, 1, 2, 3]
    Out [0:68]: array([ 0.77120707, -0.19448286])
    Out [1:68]: array([ 1.10815921,  0.05110369])
    Out [2:68]: array([ 0.74625527, -0.37475081])
    Out [3:68]: array([ 0.72931905,  0.07159743])
    
    In [29]: %px print 'hi'
    Parallel execution on engine(s): all
    [stdout:0] hi
    [stdout:1] hi
    [stdout:2] hi
    [stdout:3] hi


Since engines are IPython as well, you can even run magics remotely:

.. sourcecode:: ipython

    In [28]: %px %pylab inline
    Parallel execution on engine(s): all
    [stdout:0] 
    Populating the interactive namespace from numpy and matplotlib
    [stdout:1] 
    Populating the interactive namespace from numpy and matplotlib
    [stdout:2] 
    Populating the interactive namespace from numpy and matplotlib
    [stdout:3] 
    Populating the interactive namespace from numpy and matplotlib

And once in pylab mode with the inline backend,
you can make plots and they will be displayed in your frontend
if it supports the inline figures (e.g. notebook or qtconsole):

.. sourcecode:: ipython

    In [40]: %px plot(rand(100))
    Parallel execution on engine(s): all
    <plot0>
    <plot1>
    <plot2>
    <plot3>
    Out[0:79]: [<matplotlib.lines.Line2D at 0x10a6286d0>]
    Out[1:79]: [<matplotlib.lines.Line2D at 0x10b9476d0>]
    Out[2:79]: [<matplotlib.lines.Line2D at 0x110652750>]
    Out[3:79]: [<matplotlib.lines.Line2D at 0x10c6566d0>]


%%px Cell Magic
---------------

%%px can be used as a Cell Magic, which accepts some arguments for controlling
the execution.


Targets and Blocking
********************

%%px accepts ``--targets`` for controlling which engines on which to run,
and ``--[no]block`` for specifying the blocking behavior of this cell,
independent of the defaults for the View.

.. sourcecode:: ipython

    In [6]: %%px --targets ::2
       ...: print "I am even"
       ...: 
    Parallel execution on engine(s): [0, 2]
    [stdout:0] I am even
    [stdout:2] I am even

    In [7]: %%px --targets 1
       ...: print "I am number 1"
       ...: 
    Parallel execution on engine(s): 1
    I am number 1

    In [8]: %%px
       ...: print "still 'all' by default"
       ...: 
    Parallel execution on engine(s): all
    [stdout:0] still 'all' by default
    [stdout:1] still 'all' by default
    [stdout:2] still 'all' by default
    [stdout:3] still 'all' by default

    In [9]: %%px --noblock
       ...: import time
       ...: time.sleep(1)
       ...: time.time()
       ...: 
    Async parallel execution on engine(s): all
    Out[9]: <AsyncResult: execute>

    In [10]: %pxresult
    Out[0:12]: 1339454561.069116
    Out[1:10]: 1339454561.076752
    Out[2:12]: 1339454561.072837
    Out[3:10]: 1339454561.066665


.. seealso::

    :ref:`pxconfig` accepts these same arguments for changing the *default*
    values of targets/blocking for the active View.


Output Display
**************


%%px also accepts a ``--group-outputs`` argument,
which adjusts how the outputs of multiple engines are presented.

.. seealso::

    :meth:`.AsyncResult.display_outputs` for the grouping options.

.. sourcecode:: ipython

    In [50]: %%px --block --group-outputs=engine
       ....: import numpy as np
       ....: A = np.random.random((2,2))
       ....: ev = numpy.linalg.eigvals(A)
       ....: print ev
       ....: ev.max()
       ....:
    Parallel execution on engine(s): all
    [stdout:0] [ 0.60640442  0.95919621]
    Out [0:73]: 0.9591962130899806
    [stdout:1] [ 0.38501813  1.29430871]
    Out [1:73]: 1.2943087091452372
    [stdout:2] [-0.85925141  0.9387692 ]
    Out [2:73]: 0.93876920456230284
    [stdout:3] [ 0.37998269  1.24218246]
    Out [3:73]: 1.2421824618493817


%pxresult
---------

If you are using %px in non-blocking mode, you won't get output.
You can use %pxresult to display the outputs of the latest command,
just as is done when %px is blocking:

.. sourcecode:: ipython

    In [39]: dv.block = False
    
    In [40]: %px print 'hi'
    Async parallel execution on engine(s): all
    
    In [41]: %pxresult
    [stdout:0] hi
    [stdout:1] hi
    [stdout:2] hi
    [stdout:3] hi

%pxresult simply calls :meth:`.AsyncResult.display_outputs` on the most recent request.
It accepts the same output-grouping arguments as %%px, so you can use it to view
a result in different ways.


%autopx
-------

The %autopx magic switches to a mode where everything you type is executed
on the engines until you do %autopx again.

.. sourcecode:: ipython

    In [30]: dv.block=True

    In [31]: %autopx
    %autopx enabled

    In [32]: max_evals = []

    In [33]: for i in range(100):
       ....:     a = numpy.random.rand(10,10)
       ....:     a = a+a.transpose()
       ....:     evals = numpy.linalg.eigvals(a)
       ....:     max_evals.append(evals[0].real)
       ....:

    In [34]: print "Average max eigenvalue is: %f" % (sum(max_evals)/len(max_evals))
    [stdout:0] Average max eigenvalue is: 10.193101
    [stdout:1] Average max eigenvalue is: 10.064508
    [stdout:2] Average max eigenvalue is: 10.055724
    [stdout:3] Average max eigenvalue is: 10.086876

    In [35]: %autopx
    Auto Parallel Disabled

.. _pxconfig:

%pxconfig
---------

The default targets and blocking behavior for the magics are governed by the :attr:`block`
and :attr:`targets` attribute of the active View.  If you have a handle for the view,
you can set these attributes directly, but if you don't, you can change them with
the %pxconfig magic:

.. sourcecode:: ipython

    In [3]: %pxconfig --block

    In [5]: %px print 'hi'
    Parallel execution on engine(s): all
    [stdout:0] hi
    [stdout:1] hi
    [stdout:2] hi
    [stdout:3] hi

    In [6]: %pxconfig --targets ::2

    In [7]: %px print 'hi'
    Parallel execution on engine(s): [0, 2]
    [stdout:0] hi
    [stdout:2] hi

    In [8]: %pxconfig --noblock

    In [9]: %px print 'are you there?'
    Async parallel execution on engine(s): [0, 2]
    Out[9]: <AsyncResult: execute>

    In [10]: %pxresult
    [stdout:0] are you there?
    [stdout:2] are you there?


Multiple Active Views
=====================

The parallel magics are associated with a particular :class:`~.DirectView` object.
You can change the active view by calling the :meth:`~.DirectView.activate` method
on any view.

.. sourcecode:: ipython

    In [11]: even = rc[::2]

    In [12]: even.activate()

    In [13]: %px print 'hi'
    Async parallel execution on engine(s): [0, 2]
    Out[13]: <AsyncResult: execute>

    In [14]: even.block = True

    In [15]: %px print 'hi'
    Parallel execution on engine(s): [0, 2]
    [stdout:0] hi
    [stdout:2] hi

When activating a View, you can also specify a *suffix*, so that a whole different
set of magics are associated with that view, without replacing the existing ones.

.. sourcecode:: ipython

    # restore the original DirecView to the base %px magics
    In [16]: rc.activate()
    Out[16]: <DirectView all>

    In [17]: even.activate('_even')

    In [18]: %px print 'hi all'
    Parallel execution on engine(s): all
    [stdout:0] hi all
    [stdout:1] hi all
    [stdout:2] hi all
    [stdout:3] hi all

    In [19]: %px_even print "We aren't odd!"
    Parallel execution on engine(s): [0, 2]
    [stdout:0] We aren't odd!
    [stdout:2] We aren't odd!

This suffix is applied to the end of all magics, e.g. %autopx_even, %pxresult_even, etc.

For convenience, the :class:`~.Client` has a :meth:`~.Client.activate` method as well,
which creates a DirectView with block=True, activates it, and returns the new View.

The initial magics registered when you create a client are the result of a call to
:meth:`rc.activate` with default args.


Engines as Kernels
==================

Engines are really the same object as the Kernels used elsewhere in IPython,
with the minor exception that engines connect to a controller, while regular kernels
bind their sockets, listening for connections from a QtConsole or other frontends.

Sometimes for debugging or inspection purposes, you would like a QtConsole connected
to an engine for more direct interaction.  You can do this by first instructing
the Engine to *also* bind its kernel, to listen for connections:

.. sourcecode:: ipython

    In [50]: %px from IPython.parallel import bind_kernel; bind_kernel()

Then, if your engines are local, you can start a qtconsole right on the engine(s):

.. sourcecode:: ipython

    In [51]: %px %qtconsole

Careful with this one, because if your view is of 16 engines it will start 16 QtConsoles!

Or you can view just the connection info, and work out the right way to connect to the engines,
depending on where they live and where you are:

.. sourcecode:: ipython

    In [51]: %px %connect_info
    Parallel execution on engine(s): all
    [stdout:0] 
    {
      "stdin_port": 60387, 
      "ip": "127.0.0.1", 
      "hb_port": 50835, 
      "key": "eee2dd69-7dd3-4340-bf3e-7e2e22a62542", 
      "shell_port": 55328, 
      "iopub_port": 58264
    }

    Paste the above JSON into a file, and connect with:
        $> ipython <app> --existing <file>
    or, if you are local, you can connect with just:
        $> ipython <app> --existing kernel-60125.json 
    or even just:
        $> ipython <app> --existing 
    if this is the most recent IPython session you have started.
    [stdout:1] 
    {
      "stdin_port": 61869,
    ...

.. note::

    ``%qtconsole`` will call :func:`bind_kernel` on an engine if it hasn't been done already,
    so you can often skip that first step.



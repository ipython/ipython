.. _parallelmpi:

=======================
Using MPI with IPython
=======================

Often, a parallel algorithm will require moving data between the engines. One
way of accomplishing this is by doing a pull and then a push using the
multiengine client. However, this will be slow as all the data has to go
through the controller to the client and then back through the controller, to
its final destination.

A much better way of moving data between engines is to use a message passing
library, such as the Message Passing Interface (MPI) [MPI]_. IPython's
parallel computing architecture has been designed from the ground up to
integrate with MPI. This document describes how to use MPI with IPython.

Additional installation requirements
====================================

If you want to use MPI with IPython, you will need to install:

* A standard MPI implementation such as OpenMPI [OpenMPI]_ or MPICH.
* The mpi4py [mpi4py]_ package.

.. note::

    The mpi4py package is not a strict requirement. However, you need to
    have *some* way of calling MPI from Python. You also need some way of
    making sure that :func:`MPI_Init` is called when the IPython engines start
    up. There are a number of ways of doing this and a good number of
    associated subtleties. We highly recommend just using mpi4py as it
    takes care of most of these problems. If you want to do something
    different, let us know and we can help you get started.

Starting the engines with MPI enabled
=====================================

To use code that calls MPI, there are typically two things that MPI requires.

1. The process that wants to call MPI must be started using
   :command:`mpiexec` or a batch system (like PBS) that has MPI support.
2. Once the process starts, it must call :func:`MPI_Init`.

There are a couple of ways that you can start the IPython engines and get
these things to happen.

Automatic starting using :command:`mpiexec` and :command:`ipcluster`
--------------------------------------------------------------------

The easiest approach is to use the `MPI` Launchers in :command:`ipcluster`,
which will first start a controller and then a set of engines using
:command:`mpiexec`::

    $ ipcluster start -n 4 --engines=MPIEngineSetLauncher

This approach is best as interrupting :command:`ipcluster` will automatically
stop and clean up the controller and engines.

Manual starting using :command:`mpiexec`
----------------------------------------

If you want to start the IPython engines using the :command:`mpiexec`, just
do::

    $ mpiexec -n 4 ipengine --mpi=mpi4py

This requires that you already have a controller running and that the FURL
files for the engines are in place. We also have built in support for
PyTrilinos [PyTrilinos]_, which can be used (assuming is installed) by
starting the engines with::

    $ mpiexec -n 4 ipengine --mpi=pytrilinos

Automatic starting using PBS and :command:`ipcluster`
------------------------------------------------------

The :command:`ipcluster` command also has built-in integration with PBS. For
more information on this approach, see our documentation on :ref:`ipcluster
<parallel_process>`.

Actually using MPI
==================

Once the engines are running with MPI enabled, you are ready to go. You can
now call any code that uses MPI in the IPython engines. And, all of this can
be done interactively. Here we show a simple example that uses mpi4py
[mpi4py]_ version 1.1.0 or later.

First, lets define a simply function that uses MPI to calculate the sum of a
distributed array. Save the following text in a file called :file:`psum.py`:

.. sourcecode:: python

    from mpi4py import MPI
    import numpy as np

    def psum(a):
        locsum = np.sum(a)
        rcvBuf = np.array(0.0,'d')
        MPI.COMM_WORLD.Allreduce([locsum, MPI.DOUBLE],
            [rcvBuf, MPI.DOUBLE],
            op=MPI.SUM)
        return rcvBuf

Now, start an IPython cluster::

    $ ipcluster start --profile=mpi -n 4
    
.. note::

    It is assumed here that the mpi profile has been set up, as described :ref:`here
    <parallel_process>`.

Finally, connect to the cluster and use this function interactively. In this
case, we create a distributed array and sum up all its elements in a distributed
manner using our :func:`psum` function:

.. sourcecode:: ipython

    In [1]: from IPython.parallel import Client

    In [2]: c = Client(profile='mpi')

    In [3]: view = c[:]

    In [4]: view.activate() # enable magics

    # run the contents of the file on each engine:
    In [5]: view.run('psum.py')

    In [6]: view.scatter('a',np.arange(16,dtype='float'))

    In [7]: view['a']
    Out[7]: [array([ 0.,  1.,  2.,  3.]),
             array([ 4.,  5.,  6.,  7.]),
             array([  8.,   9.,  10.,  11.]),
             array([ 12.,  13.,  14.,  15.])]

    In [7]: %px totalsum = psum(a)
    Parallel execution on engines: [0,1,2,3]

    In [8]: view['totalsum']
    Out[8]: [120.0, 120.0, 120.0, 120.0]

Any Python code that makes calls to MPI can be used in this manner, including
compiled C, C++ and Fortran libraries that have been exposed to Python.

.. [MPI] Message Passing Interface.  http://www-unix.mcs.anl.gov/mpi/
.. [mpi4py] MPI for Python. mpi4py: http://mpi4py.scipy.org/
.. [OpenMPI] Open MPI. http://www.open-mpi.org/
.. [PyTrilinos] PyTrilinos. http://trilinos.sandia.gov/packages/pytrilinos/



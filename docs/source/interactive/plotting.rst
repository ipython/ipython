.. _plotting:

Rich Outputs
------------

One of the main feature of IPython when used as a kernel is its ability to
show rich output. This means that object that can be representing as image,
sounds, animation, (etc...) can be shown this way if the frontend support it.

In order for this to be possible, you need to use the ``display()`` function,
that should be available by default on IPython 5.4+ and 6.1+, or that you can
import with ``from IPython.display import display``. Then use ``display(<your
object>)`` instead of ``print()``, and if possible your object will be displayed
with a richer representation. In the terminal of course, there won't be much
difference as object are most of the time represented by text, but in notebook
and similar interface you will get richer outputs.


Plotting
--------

.. note::

    Starting with IPython 5.0 and matplotlib 2.0 you can avoid the use of
    IPython's specific magic and use
    ``matplotlib.pyplot.ion()``/``matplotlib.pyplot.ioff()`` which have the
    advantages of working outside of IPython as well.


One major feature of the IPython kernel is the ability to display plots that 
are the output of running code cells. The IPython kernel is designed to work 
seamlessly with the matplotlib_ plotting library to provide this functionality.

To set this up, before any plotting or import of matplotlib is performed you
must execute the ``%matplotlib``  :ref:`magic command <magics_explained>`. This
performs the necessary behind-the-scenes setup for IPython to work correctly
hand in hand with ``matplotlib``; it does *not*, however, actually execute any
Python ``import`` commands, that is, no names are added to the namespace.

If the ``%matplotlib`` magic is called without an argument, the
output of a plotting command is displayed using the default ``matplotlib``
backend in a separate window. Alternatively, the backend can be explicitly
requested using, for example::

  %matplotlib gtk

A particularly interesting backend, provided by IPython, is the ``inline``
backend.  This is available only for the Jupyter Notebook and the
Jupyter QtConsole.  It can be invoked as follows::

  %matplotlib inline

With this backend, the output of plotting commands is displayed *inline* within
frontends like the Jupyter notebook, directly below the code cell that produced
it. The resulting plots will then also be stored in the notebook document.

.. seealso::

    `Plotting with Matplotlib`_  example notebook


The matplotlib_ library also ships with ``%matplotlib notebook`` command that
allows interactive figures if your environment allows it.

See the matplotlib_ documentation for more information. 

.. include:: ../links.txt

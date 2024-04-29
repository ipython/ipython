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


.. _matplotlib_magic:

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
may execute the ``%matplotlib`` :ref:`magic command <magics_explained>`. This
performs the necessary behind-the-scenes setup for IPython to work correctly
hand in hand with ``matplotlib``; it does *not*, however, actually execute any
Python ``import`` commands, that is, no names are added to the namespace.

If you do not use the ``%matplotlib`` magic or you call it without an argument,
the output of a plotting command is displayed using the default ``matplotlib``
backend, which may be different depending on Operating System and whether
running within Jupyter or not.

Alternatively, the backend can be explicitly requested using, for example::

  %matplotlib gtk

The argument passed to the ``%matplotlib`` magic command may be the name of any
backend understood by ``matplotlib`` or it may the name of a GUI loop such as
``qt`` or ``osx``, in which case an appropriate backend supporting that GUI
loop will be selected. To obtain a full list of all backends and GUI loops
understood by ``matplotlib`` use ``%matplotlib --list``.

There are some specific backends that are used in the Jupyter ecosystem:

- The ``inline`` backend is provided by IPython and can be used in Jupyter Lab,
  Notebook and QtConsole; it is the default backend when using Jupyter. The
  outputs of plotting commands are displayed *inline* within frontends like
  Jupyter Notebook, directly below the code cells that produced them.
  The resulting plots will then also be stored in the notebook document.

- The ``notebook`` or ``nbagg`` backend is built into ``matplotlib`` and can be
  used with Jupyter ``notebook <7`` and ``nbclassic``. Plots are interactive so
  they can be zoomed and panned.

- The ``ipympl`` or ``widget`` backend is for use with Jupyter ``lab`` and
  ``notebook >=7``. It is in a separate ``ipympl`` module that must be
  installed using ``pip`` or ``conda`` in the usual manner. Plots are
  interactive so they can be zoomed and panned.

.. seealso::

    `Plotting with Matplotlib`_  example notebook

See the matplotlib_ documentation for more information, in particular the
section on backends.

.. include:: ../links.txt

.. _plotting:

Plotting
--------
One major feature of the IPython kernel is the ability to display plots that 
are the output of running code cells. The IPython kernel is designed to work 
seamlessly with the matplotlib_ plotting library to provide this functionality.

To set this up, before any plotting is performed you must execute the
``%matplotlib``  :ref:`magic command <magics_explained>`. This performs the
necessary behind-the-scenes setup for IPython to work correctly hand in hand
with ``matplotlib``; it does *not*, however, actually execute any Python
``import`` commands, that is, no names are added to the namespace.

If the ``%matplotlib`` magic is called without an argument, the
output of a plotting command is displayed using the default ``matplotlib``
backend in a separate window. Alternatively, the backend can be explicitly
requested using, for example::

  %matplotlib gtk

A particularly interesting backend, provided by IPython, is the ``inline``
backend.  This is available only for the Jupyter Notebook and the
:ref:`Jupyter QtConsole <qtconsole>`.  It can be invoked as follows::

  %matplotlib inline

With this backend, the output of plotting commands is displayed *inline*
within the notebook, directly below the code cell that produced it. The
resulting plots will then also be stored in the notebook document.

.. seealso::

    `Plotting with Matplotlib`_  example notebook

.. include:: ../links.txt

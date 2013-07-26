.. _extensions_overview:

==================
IPython extensions
==================

A level above configuration are IPython extensions, Python modules which modify
the behaviour of the shell. They are referred to by an importable module name,
and can be placed anywhere you'd normally import from, or in
``$IPYTHONDIR/extensions/``.

Getting extensions
==================

A few important extensions are :ref:`bundled with IPython <bundled_extensions>`.
Others can be found on the `extensions index
<https://github.com/ipython/ipython/wiki/Extensions-Index>`_ on the wiki, and installed with
the ``%install_ext`` magic function.

Using extensions
================

To load an extension while IPython is running, use the ``%load_ext`` magic:

.. sourcecode:: ipython

    In [1]: %load_ext myextension

To load it each time IPython starts, list it in your configuration file::

    c.InteractiveShellApp.extensions = [
        'myextension'
    ]

Writing extensions
==================

An IPython extension is an importable Python module that has a couple of special
functions to load and unload it. Here is a template::

    # myextension.py

    def load_ipython_extension(ipython):
        # The `ipython` argument is the currently active `InteractiveShell`
        # instance, which can be used in any way. This allows you to register
        # new magics or aliases, for example.

    def unload_ipython_extension(ipython):
        # If you want your extension to be unloadable, put that logic here.

This :func:`load_ipython_extension` function is called after your extension is
imported, and the currently active :class:`~IPython.core.interactiveshell.InteractiveShell`
instance is passed as the only argument. You can do anything you want with
IPython at that point.

:func:`load_ipython_extension` will be called again if you load or reload
the extension again. It is up to the extension author to add code to manage
that.

Useful :class:`InteractiveShell` methods include :meth:`~IPython.core.interactiveshell.InteractiveShell.define_magic`, 
:meth:`~IPython.core.interactiveshell.InteractiveShell.push` (to add variables to the user namespace) and 
:meth:`~IPython.core.interactiveshell.InteractiveShell.drop_by_id` (to remove variables on unloading).

You can put your extension modules anywhere you want, as long as they can be
imported by Python's standard import mechanism. However, to make it easy to
write extensions, you can also put your extensions in
``os.path.join(ip.ipython_dir, 'extensions')``. This directory is added to
``sys.path`` automatically.

When your extension is ready for general use, please add it to the `extensions
index <https://github.com/ipython/ipython/wiki/Extensions-Index>`_.

.. _bundled_extensions:

Extensions bundled with IPython
===============================

.. toctree::
   :maxdepth: 1

   autoreload
   cythonmagic
   octavemagic
   rmagic
   storemagic
   sympyprinting

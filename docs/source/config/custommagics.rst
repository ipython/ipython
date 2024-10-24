.. _defining_magics:

Defining custom magics
======================

There are two main ways to define your own magic functions: from standalone
functions and by inheriting from a base class provided by IPython:
:class:`IPython.core.magic.Magics`. Below we show code you can place in a file
that you load from your configuration, such as any file in the ``startup``
subdirectory of your default IPython profile.

First, let us see the simplest case. The following shows how to create a line
magic, a cell one and one that works in both modes, using just plain functions:

.. sourcecode:: python

    from IPython.core.magic import (register_line_magic, register_cell_magic,
                                    register_line_cell_magic)

    @register_line_magic
    def lmagic(line):
        "my line magic"
        return line

    @register_cell_magic
    def cmagic(line, cell):
        "my cell magic"
        return line, cell

    @register_line_cell_magic
    def lcmagic(line, cell=None):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            print("Called as line magic")
            return line
        else:
            print("Called as cell magic")
            return line, cell

    # In an interactive session, we need to delete these to avoid
    # name conflicts for automagic to work on line magics.
    del lmagic, lcmagic


You can also create magics of all three kinds by inheriting from the
:class:`IPython.core.magic.Magics` class.  This lets you create magics that can
potentially hold state in between calls, and that have full access to the main
IPython object:
    
.. sourcecode:: python

    # This code can be put in any Python module, it does not require IPython
    # itself to be running already.  It only creates the magics subclass but
    # doesn't instantiate it yet.
    from __future__ import print_function
    from IPython.core.magic import (Magics, magics_class, line_magic,
                                    cell_magic, line_cell_magic)

    # The class MUST call this class decorator at creation time
    @magics_class
    class MyMagics(Magics):

        @line_magic
        def lmagic(self, line):
            "my line magic"
            print("Full access to the main IPython object:", self.shell)
            print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
            return line

        @cell_magic
        def cmagic(self, line, cell):
            "my cell magic"
            return line, cell

        @line_cell_magic
        def lcmagic(self, line, cell=None):
            "Magic that works both as %lcmagic and as %%lcmagic"
            if cell is None:
                print("Called as line magic")
                return line
            else:
                print("Called as cell magic")
                return line, cell


    # In order to actually use these magics, you must register them with a
    # running IPython.

    def load_ipython_extension(ipython):
        """
        Any module file that define a function named `load_ipython_extension`
        can be loaded via `%load_ext module.path` or be configured to be
        autoloaded by IPython at startup time.
        """
        # You can register the class itself without instantiating it.  IPython will
        # call the default constructor on it.
        ipython.register_magics(MyMagics)

If you want to create a class with a different constructor that holds
additional state, then you should always call the parent constructor and
instantiate the class yourself before registration:

.. sourcecode:: python

    @magics_class
    class StatefulMagics(Magics):
        "Magics that hold additional state"

        def __init__(self, shell, data):
            # You must call the parent constructor
            super(StatefulMagics, self).__init__(shell)
            self.data = data
        
        # etc...

    def load_ipython_extension(ipython):
        """
        Any module file that define a function named `load_ipython_extension`
        can be loaded via `%load_ext module.path` or be configured to be
        autoloaded by IPython at startup time.
        """
        # This class must then be registered with a manually created instance,
        # since its constructor has different arguments from the default:
        magics = StatefulMagics(ipython, some_data)
        ipython.register_magics(magics)


.. note::

   In early IPython versions 0.12 and before the line magics were
   created using a :func:`define_magic` API function.  This API has been
   replaced with the above in IPython 0.13 and then completely removed
   in IPython 5.  Maintainers of IPython extensions that still use the
   :func:`define_magic` function are advised to adjust their code
   for the current API.


Accessing user namespace and local scope
========================================

When creating line magics, you may need to access surrounding scope  to get user
variables (e.g when called inside functions). IPython provides the
``@needs_local_scope`` decorator that can be imported from
``IPython.core.magic``. When decorated with ``@needs_local_scope`` a magic will
be passed ``local_ns`` as an argument. As a convenience ``@needs_local_scope``
can also be applied to cell magics even if cell magics cannot appear at local
scope context.

Silencing the magic output
==========================

Sometimes it may be useful to define a magic that can be silenced the same way
that non-magic expressions can, i.e., by appending a semicolon at the end of the Python
code to be executed. That can be achieved by decorating the magic function with
the decorator ``@output_can_be_silenced`` that can be imported from
``IPython.core.magic``. When this decorator is used, IPython will parse the Python
code used by the magic and, if the last token is a ``;``, the output created by the
magic will not show up on the screen. If you want to see an example of this decorator
in action, take a look on the ``time`` magic defined in
``IPython.core.magics.execution.py``.

Complete Example
================

Here is a full example of a magic package. You can distribute magics using
setuptools, distutils, or any other distribution tools like `flit
<https://flit.readthedocs.io>`_ for pure Python packages.

When distributing magics as part of a package, recommended best practice is to
execute the registration inside the `load_ipython_extension` as demonstrated in
the example below, instead of directly in the module (as in the initial example
with the ``@register_*`` decorators). This means a user will need to explicitly
choose to load your magic with ``%load_ext``. instead implicitly getting it when
importing the module. This is particularly relevant if loading your magic has 
side effects, if it is slow to load, or if it might override another magic with
the same name. 

.. sourcecode:: bash

   .
   ├── example_magic
   │   ├── __init__.py
   │   └── abracadabra.py
   └── setup.py

.. sourcecode:: bash

   $ cat example_magic/__init__.py
   """An example magic"""
   __version__ = '0.0.1'
   
   from .abracadabra import Abracadabra
   
   def load_ipython_extension(ipython):
       ipython.register_magics(Abracadabra)

.. sourcecode:: bash

    $ cat example_magic/abracadabra.py
    from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic)

    @magics_class
    class Abracadabra(Magics):

        @line_magic
        def abra(self, line):
            return line

        @cell_magic
        def cadabra(self, line, cell):
            return line, cell


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

    # We delete these to avoid name conflicts for automagic to work
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
    # running IPython.  This code must be placed in a file that is loaded once
    # IPython is up and running:
    ip = get_ipython()
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ip.register_magics(MyMagics)

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

    # This class must then be registered with a manually created instance,
    # since its constructor has different arguments from the default:
    ip = get_ipython()
    magics = StatefulMagics(ip, some_data)
    ip.register_magics(magics)
    

In earlier versions, IPython had an API for the creation of line magics (cell
magics did not exist at the time) that required you to create functions with a
method-looking signature and to manually pass both the function and the name.
While this API is no longer recommended, it remains indefinitely supported for
backwards compatibility purposes.  With the old API, you'd create a magic as
follows:

.. sourcecode:: python

    def func(self, line):
        print("Line magic called with line:", line)
        print("IPython object:", self.shell)

    ip = get_ipython()
    # Declare this function as the magic %mycommand
    ip.define_magic('mycommand', func)

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

Complete Example
================

Here is a full example of a magic package. You can distribute magics using
setuptools, distutils, or any other distribution tools like `flit
<http://flit.readthedocs.io>` for pure Python packages.


.. sourcecode::

   .
   ├── example_magic
   │   ├── __init__.py
   │   └── abracadabra.py
   └── setup.py

.. sourcecode::

   $ cat example_magic/__init__.py
   """An example magic"""
   __version__ = '0.0.1'
   
   from .abracadabra import Abracadabra
   
   def load_ipython_extension(ipython):
       ipython.register_magics(Abracadabra)

.. sourcecode::

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

Defining completer for cell magics
----------------------------------

A number of magics allow to embed non-python code in Python documents. It can
thus be useful to define custom completer which provide completion for the user.
Since IPython 6.2 this is possible when Defining custom magic classes, and using
the ``@complete_for`` decorator.

Let's extend our above magic with completions:

.. sourcecode::

    from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, completer_for)
    from IPython.core.completer import Completion

    words = ['Supercalifragilisticexpialidocious', 'Alakazam', 'Shazam']

    @magics_class
    class Abracadabra(Magics):

        @line_magic
        def abra(self, line):
            return line

        @cell_magic
        def cadabra(self, line, cell):
            return line, cell
        
        @completer_for('cadabra')
        def complete(self, line:str, cell:str, offset:int):
            """
            `line` will be the first line of the cell, `cell`
            the rest of the body starting at the second line,
            `offset` the position of the cursor in the cell, starting
            at the beginning of `line` (incuding the % or %%) character
            in unicode codepoints.
            
            The end of line ned tobe explicitly take care of.
            
            This function should `yield` a set of `IPython.core.completer.Completions(start, end, text)`
            telling IPython to replace the text between `start` and `end` by `text`.
            """
            
            # get the full body and text until the cursor
            # there can be some text after the cusrsor we should
            take care of that but keep the example simple.
            full_body = line + '\n'+cell
            text_until_cursor = full_body[:offset]
            
            # split on whitespace and get last token:
            token_before_cursor = text_until_cursor.split()[-1].lower()
            
            for w in words:
                if w.lower().startswith(token_before_cursor):
                    # We'll replace the current token so replace
                    # from the position of the cursor back len of token.
                    start = offset-len(token_before_cursor)
                    end = offset
                    yield Completion(start, end, w)
        
We  can optionally register them live in an IPython shell of notebook::

    ip = get_ipython()
    ip.register_magics(Abracadabra)

Now try the following::

    %%cadabra
    s<tab>

You should get ``Shazam`` and ``Supercalifragilisticexpialidocious`` as
potential completions.

Limitations
~~~~~~~~~~~

The ability to complete magics is still limited but should improve with time,
here are a number of current limitations:

  - Completion will not work while the kernel is busy.
  - Completions are registered for a given magic, but the magics may be renamed
    by the user in which case the completion will not dispatch correctly.
  - If a custom completer is added to a magic, there the normal Python
    completions will not be triggered.


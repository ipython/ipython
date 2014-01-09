.. _tips:

=====================
IPython Tips & Tricks
=====================

The `IPython cookbook
<https://github.com/ipython/ipython/wiki?path=Cookbook>`_ details more things
you can do with IPython.

.. This is not in the current version:


Embed IPython in your programs
------------------------------

A few lines of code are enough to load a complete IPython inside your own
programs, giving you the ability to work with your data interactively after
automatic processing has been completed. See :ref:`the embedding section <embedding>`.

Run doctests
------------

Run your doctests from within IPython for development and debugging. The
special %doctest_mode command toggles a mode where the prompt, output and
exceptions display matches as closely as possible that of the default Python
interpreter. In addition, this mode allows you to directly paste in code that
contains leading '>>>' prompts, even if they have extra leading whitespace
(as is common in doctest files). This combined with the ``%history -t`` call
to see your translated history allows for an easy doctest workflow, where you
can go from doctest to interactive execution to pasting into valid Python code
as needed.

Use IPython to present interactive demos
----------------------------------------

Use the :class:`IPython.lib.demo.Demo` class to load any Python script as an interactive
demo. With a minimal amount of simple markup, you can control the execution of
the script, stopping as needed. See :ref:`here <interactive_demos>` for more.

Suppress output
---------------

Put a ';' at the end of a line to suppress the printing of output. This is
useful when doing calculations which generate long output you are not
interested in seeing. It also keeps the object out of the output cache, so if
you're working with large temporary objects, they'll be released from memory sooner.

Lightweight 'version control'
-----------------------------

When you call ``%edit`` with no arguments, IPython opens an empty editor
with a temporary file, and it returns the contents of your editing
session as a string variable. Thanks to IPython's output caching
mechanism, this is automatically stored::

    In [1]: %edit

    IPython will make a temporary file named: /tmp/ipython_edit_yR-HCN.py

    Editing... done. Executing edited code...

    hello - this is a temporary file

    Out[1]: "print('hello - this is a temporary file')\n"

Now, if you call ``%edit -p``, IPython tries to open an editor with the
same data as the last time you used %edit. So if you haven't used %edit
in the meantime, this same contents will reopen; however, it will be
done in a new file. This means that if you make changes and you later
want to find an old version, you can always retrieve it by using its
output number, via '%edit _NN', where NN is the number of the output
prompt.

Continuing with the example above, this should illustrate this idea::

    In [2]: edit -p

    IPython will make a temporary file named: /tmp/ipython_edit_nA09Qk.py

    Editing... done. Executing edited code...

    hello - now I made some changes

    Out[2]: "print('hello - now I made some changes')\n"

    In [3]: edit _1

    IPython will make a temporary file named: /tmp/ipython_edit_gy6-zD.py

    Editing... done. Executing edited code...

    hello - this is a temporary file

    IPython version control at work :)

    Out[3]: "print('hello - this is a temporary file')\nprint('IPython version control at work :)')\n"


This section was written after a contribution by Alexander Belchenko on
the IPython user list.


.. _ipython_as_shell:

=========================
IPython as a system shell
=========================



Overview
========

It is possible to adapt IPython for system shell usage. In the past, IPython
shipped a special 'sh' profile for this purpose, but it had been quarantined
since 0.11 release, and in 1.0 it was removed altogether. Nevertheless, much
of this section relies on machinery which does not require a custom profile.

You can set up your own 'sh' :ref:`profile <Profiles>` to be different from
the default profile such that:

 * Prompt shows the current directory (see `Prompt customization`_)
 * Make system commands directly available (in alias table) by running the
   ``%rehashx`` magic. If you install new programs along your PATH, you might
   want to run ``%rehashx`` to update the alias table
 * turn ``%autocall`` to full mode


Environment variables
=====================

Rather than manipulating os.environ directly, you may like to use the magic
`%env` command.  With no arguments, this displays all environment variables
and values.  To get the value of a specific variable, use `%env var`.  To set
the value of a specific variable, use `%env foo bar`, `%env foo=bar`.  By
default values are considered to be strings so quoting them is unnecessary.
However, Python variables are expanded as usual in the magic command, so
`%env foo=$bar` means "set the environment variable foo to the value of the
Python variable `bar`".

Aliases
=======

Once you run ``%rehashx``, all of your $PATH has been loaded as IPython aliases,
so you should be able to type any normal system command and have it executed.
See ``%alias?``  and ``%unalias?`` for details on the alias facilities. See also
``%rehashx?`` for details on the mechanism used to load $PATH.


Directory management
====================

Since each command passed by IPython to the underlying system is executed
in a subshell which exits immediately, you can NOT use !cd to navigate
the filesystem.

IPython provides its own builtin ``%cd`` magic command to move in the
filesystem (the % is not required with automagic on). It also maintains
a list of visited directories (use ``%dhist`` to see it) and allows direct
switching to any of them. Type ``cd?`` for more details.

``%pushd``, ``%popd`` and ``%dirs`` are provided for directory stack handling.


Prompt customization
====================

Here are some prompt configurations you can try out interactively by using the
``%config`` magic::
    
    %config PromptManager.in_template = r'{color.LightGreen}\u@\h{color.LightBlue}[{color.LightCyan}\Y1{color.LightBlue}]{color.Green}|\#> '
    %config PromptManager.in2_template = r'{color.Green}|{color.LightGreen}\D{color.Green}> '
    %config PromptManager.out_template = r'<\#> '


You can change the prompt configuration to your liking permanently by editing
``ipython_config.py``::
    
    c.PromptManager.in_template = r'{color.LightGreen}\u@\h{color.LightBlue}[{color.LightCyan}\Y1{color.LightBlue}]{color.Green}|\#> '
    c.PromptManager.in2_template = r'{color.Green}|{color.LightGreen}\D{color.Green}> '
    c.PromptManager.out_template = r'<\#> '

Read more about the :ref:`configuration system <config_overview>` for details
on how to find ``ipython_config.py``.

.. _string_lists:

String lists
============

String lists (IPython.utils.text.SList) are handy way to process output
from system commands. They are produced by ``var = !cmd`` syntax.

First, we acquire the output of 'ls -l'::

    [Q:doc/examples]|2> lines = !ls -l
     ==
    ['total 23',
     '-rw-rw-rw- 1 ville None 1163 Sep 30  2006 example-demo.py',
     '-rw-rw-rw- 1 ville None 1927 Sep 30  2006 example-embed-short.py',
     '-rwxrwxrwx 1 ville None 4606 Sep  1 17:15 example-embed.py',
     '-rwxrwxrwx 1 ville None 1017 Sep 30  2006 example-gnuplot.py',
     '-rwxrwxrwx 1 ville None  339 Jun 11 18:01 extension.py',
     '-rwxrwxrwx 1 ville None  113 Dec 20  2006 seteditor.py',
     '-rwxrwxrwx 1 ville None  245 Dec 12  2006 seteditor.pyc']

Now, let's take a look at the contents of 'lines' (the first number is
the list element number)::

    [Q:doc/examples]|3> lines
                    <3> SList (.p, .n, .l, .s, .grep(), .fields() available). Value:

    0: total 23
    1: -rw-rw-rw- 1 ville None 1163 Sep 30  2006 example-demo.py
    2: -rw-rw-rw- 1 ville None 1927 Sep 30  2006 example-embed-short.py
    3: -rwxrwxrwx 1 ville None 4606 Sep  1 17:15 example-embed.py
    4: -rwxrwxrwx 1 ville None 1017 Sep 30  2006 example-gnuplot.py
    5: -rwxrwxrwx 1 ville None  339 Jun 11 18:01 extension.py
    6: -rwxrwxrwx 1 ville None  113 Dec 20  2006 seteditor.py
    7: -rwxrwxrwx 1 ville None  245 Dec 12  2006 seteditor.pyc

Now, let's filter out the 'embed' lines::

    [Q:doc/examples]|4> l2 = lines.grep('embed',prune=1)
    [Q:doc/examples]|5> l2
                    <5> SList (.p, .n, .l, .s, .grep(), .fields() available). Value:

    0: total 23
    1: -rw-rw-rw- 1 ville None 1163 Sep 30  2006 example-demo.py
    2: -rwxrwxrwx 1 ville None 1017 Sep 30  2006 example-gnuplot.py
    3: -rwxrwxrwx 1 ville None  339 Jun 11 18:01 extension.py
    4: -rwxrwxrwx 1 ville None  113 Dec 20  2006 seteditor.py
    5: -rwxrwxrwx 1 ville None  245 Dec 12  2006 seteditor.pyc

Now, we want strings having just file names and permissions::

    [Q:doc/examples]|6> l2.fields(8,0)
                    <6> SList (.p, .n, .l, .s, .grep(), .fields() available). Value:

    0: total
    1: example-demo.py -rw-rw-rw-
    2: example-gnuplot.py -rwxrwxrwx
    3: extension.py -rwxrwxrwx
    4: seteditor.py -rwxrwxrwx
    5: seteditor.pyc -rwxrwxrwx

Note how the line with 'total' does not raise IndexError.

If you want to split these (yielding lists), call fields() without
arguments::

    [Q:doc/examples]|7> _.fields()
                    <7>
    [['total'],
     ['example-demo.py', '-rw-rw-rw-'],
     ['example-gnuplot.py', '-rwxrwxrwx'],
     ['extension.py', '-rwxrwxrwx'],
     ['seteditor.py', '-rwxrwxrwx'],
     ['seteditor.pyc', '-rwxrwxrwx']]

If you want to pass these separated with spaces to a command (typical
for lists if files), use the .s property::


    [Q:doc/examples]|13> files = l2.fields(8).s
    [Q:doc/examples]|14> files
                    <14> 'example-demo.py example-gnuplot.py extension.py seteditor.py seteditor.pyc'
    [Q:doc/examples]|15> ls $files
    example-demo.py  example-gnuplot.py  extension.py  seteditor.py  seteditor.pyc

SLists are inherited from normal Python lists, so every list method is
available::

    [Q:doc/examples]|21> lines.append('hey')


Real world example: remove all files outside version control
------------------------------------------------------------

First, capture output of "hg status"::

    [Q:/ipython]|28> out = !hg status
     ==
    ['M IPython\\extensions\\ipy_kitcfg.py',
     'M IPython\\extensions\\ipy_rehashdir.py',
    ...
     '? build\\lib\\IPython\\Debugger.py',
     '? build\\lib\\IPython\\extensions\\InterpreterExec.py',
     '? build\\lib\\IPython\\extensions\\InterpreterPasteInput.py',
    ...

(lines starting with ? are not under version control).

::

    [Q:/ipython]|35> junk = out.grep(r'^\?').fields(1)
    [Q:/ipython]|36> junk
                <36> SList (.p, .n, .l, .s, .grep(), .fields() availab
    ...
    10: build\bdist.win32\winexe\temp\_ctypes.py
    11: build\bdist.win32\winexe\temp\_hashlib.py
    12: build\bdist.win32\winexe\temp\_socket.py

Now we can just remove these files by doing 'rm $junk.s'. 

The .s, .n, .p properties
-------------------------

The ``.s`` property returns one string where lines are separated by
single space (for convenient passing to system commands). The ``.n``
property return one string where the lines are separated by a newline
(i.e. the original output of the function). If the items in string
list are file names, ``.p`` can be used to get a list of "path" objects
for convenient file manipulation.


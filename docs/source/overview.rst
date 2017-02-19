.. _overview:

========
Overview
========

One of Python's most useful features is its interactive interpreter.
It allows for very fast testing of ideas without the overhead of
creating test files as is typical in most programming languages.
However, the interpreter supplied with the standard Python distribution
is somewhat limited for extended interactive use.

The goal of IPython is to create a comprehensive environment for
interactive and exploratory computing.  To support this goal, IPython
has three main components:

* An enhanced interactive Python shell.

* A decoupled :ref:`two-process communication model <ipythonzmq>`, which
  allows for multiple clients to connect to a computation kernel, most notably
  the web-based notebook provided with `Jupyter <https://jupyter.org>`_.

* An architecture for interactive parallel computing now part of the
  `ipyparallel` package.

All of IPython is open source (released under the revised BSD license).

Enhanced interactive Python shell
=================================

IPython's interactive shell (:command:`ipython`), has the following goals,
amongst others:

1. Provide an interactive shell superior to Python's default. IPython
   has many features for tab-completion, object introspection, system shell
   access, command history retrieval across sessions, and its own special
   command system for adding functionality when working interactively. It
   tries to be a very efficient environment both for Python code development
   and for exploration of problems using Python objects (in situations like
   data analysis).
  
2. Serve as an embeddable, ready to use interpreter for your own
   programs. An interactive IPython shell can be started with a single call
   from inside another program, providing access to the current namespace.
   This can be very useful both for debugging purposes and for situations
   where a blend of batch-processing and interactive exploration are needed.
  
3. Offer a flexible framework which can be used as the base
   environment for working with other systems, with Python as the underlying
   bridge language. Specifically scientific environments like Mathematica,
   IDL and Matlab inspired its design, but similar ideas can be
   useful in many fields.
  
4. Allow interactive testing of threaded graphical toolkits. IPython
   has support for interactive, non-blocking control of GTK, Qt, WX, GLUT, and
   OS X applications via special threading flags. The normal Python
   shell can only do this for Tkinter applications.

Main features of the interactive shell
--------------------------------------

* Dynamic object introspection. One can access docstrings, function
  definition prototypes, source code, source files and other details
  of any object accessible to the interpreter with a single
  keystroke (:samp:`?`, and using :samp:`??` provides additional detail).
  
* Searching through modules and namespaces with :samp:`*` wildcards, both
  when using the :samp:`?` system and via the :samp:`%psearch` command.

* Completion in the local namespace, by typing :kbd:`TAB` at the prompt.
  This works for keywords, modules, methods, variables and files in the
  current directory. This is supported via the ``prompt_toolkit`` library.
  Custom completers can be implemented easily for different purposes
  (system commands, magic arguments etc.)

* Numbered input/output prompts with command history (persistent
  across sessions and tied to each profile), full searching in this
  history and caching of all input and output.

* User-extensible 'magic' commands. A set of commands prefixed with
  :samp:`%`  or :samp:`%%` is available for controlling IPython itself and provides
  directory control, namespace information and many aliases to
  common system shell commands.

* Alias facility for defining your own system aliases.

* Complete system shell access. Lines starting with :samp:`!` are passed
  directly to the system shell, and using :samp:`!!` or :samp:`var = !cmd` 
  captures shell output into python variables for further use.

* The ability to expand python variables when calling the system shell. In a
  shell command, any python variable prefixed with :samp:`$` is expanded. A
  double :samp:`$$` allows passing a literal :samp:`$` to the shell (for access
  to shell and environment variables like :envvar:`PATH`).

* Filesystem navigation, via a magic :samp:`%cd` command, along with a
  persistent bookmark system (using :samp:`%bookmark`) for fast access to
  frequently visited directories.

* A lightweight persistence framework via the :samp:`%store` command, which
  allows you to save arbitrary Python variables. These get restored
  when you run the :samp:`%store -r` command.

* Automatic indentation and highlighting of code as you type (through the
  `prompt_toolkit` library).

* Macro system for quickly re-executing multiple lines of previous
  input with a single name via the :samp:`%macro` command. Macros can be
  stored persistently via :samp:`%store` and edited via :samp:`%edit`.

* Session logging (you can then later use these logs as code in your
  programs). Logs can optionally timestamp all input, and also store
  session output (marked as comments, so the log remains valid
  Python source code).

* Session restoring: logs can be replayed to restore a previous
  session to the state where you left it.

* Verbose and colored exception traceback printouts. Easier to parse
  visually, and in verbose mode they produce a lot of useful
  debugging information (basically a terminal version of the cgitb
  module).

* Auto-parentheses via the :samp:`%autocall` command: callable objects can be
  executed without parentheses: :samp:`sin 3` is automatically converted to
  :samp:`sin(3)`

* Auto-quoting: using :samp:`,`, or :samp:`;` as the first character forces
  auto-quoting of the rest of the line: :samp:`,my_function a b` becomes
  automatically :samp:`my_function("a","b")`, while :samp:`;my_function a b`
  becomes :samp:`my_function("a b")`.

* Extensible input syntax. You can define filters that pre-process
  user input to simplify input in special situations. This allows
  for example pasting multi-line code fragments which start with
  :samp:`>>>` or :samp:`...` such as those from other python sessions or the
  standard Python documentation.

* Flexible :ref:`configuration system <config_overview>`. It uses a
  configuration file which allows permanent setting of all command-line
  options, module loading, code and file execution. The system allows
  recursive file inclusion, so you can have a base file with defaults and
  layers which load other customizations for particular projects.

* Embeddable. You can call IPython as a python shell inside your own
  python programs. This can be used both for debugging code or for
  providing interactive abilities to your programs with knowledge
  about the local namespaces (very useful in debugging and data
  analysis situations).

* Easy debugger access. You can set IPython to call up an enhanced version of
  the Python debugger (pdb) every time there is an uncaught exception. This
  drops you inside the code which triggered the exception with all the data
  live and it is possible to navigate the stack to rapidly isolate the source
  of a bug. The :samp:`%run` magic command (with the :samp:`-d` option) can run
  any script under pdb's control, automatically setting initial breakpoints for
  you.  This version of pdb has IPython-specific improvements, including
  tab-completion and traceback coloring support. For even easier debugger
  access, try :samp:`%debug` after seeing an exception.

* Profiler support. You can run single statements (similar to
  :samp:`profile.run()`) or complete programs under the profiler's control.
  While this is possible with standard cProfile or profile modules,
  IPython wraps this functionality with magic commands (see :samp:`%prun`
  and :samp:`%run -p`) convenient for rapid interactive work.

* Simple timing information. You can use the :samp:`%timeit` command to get
  the execution time of a Python statement or expression. This machinery is
  intelligent enough to do more repetitions for commands that finish very
  quickly in order to get a better estimate of their running time. 

.. sourcecode:: ipython

    In [1]: %timeit 1+1
    10000000 loops, best of 3: 25.5 ns per loop

    In [2]: %timeit [math.sin(x) for x in range(5000)]
    1000 loops, best of 3: 719 µs per loop

.. 

  To get the timing information for more than one expression, use the
  :samp:`%%timeit` cell magic command.
  

* Doctest support. The special :samp:`%doctest_mode` command toggles a mode
  to use doctest-compatible prompts, so you can use IPython sessions as
  doctest code. By default, IPython also allows you to paste existing
  doctests, and strips out the leading :samp:`>>>` and :samp:`...` prompts in
  them.

.. _ipythonzmq:

Decoupled two-process model
==============================

IPython has abstracted and extended the notion of a traditional
*Read-Evaluate-Print Loop* (REPL) environment by decoupling the *evaluation*
into its own process. We call this process a **kernel**: it receives execution
instructions from clients and communicates the results back to them.

This decoupling allows us to have several clients connected to the same
kernel, and even allows clients and kernels to live on different machines.
With the exclusion of the traditional single process terminal-based IPython
(what you start if you run ``ipython`` without any subcommands), all
other IPython machinery uses this two-process model. Most of this is now part
of the `Jupyter` project, which includes ``jupyter console``,  ``jupyter
qtconsole``, and ``jupyter notebook``.

As an example, this means that when you start ``jupyter qtconsole``, you're
really starting two processes, a kernel and a Qt-based client can send
commands to and receive results from that kernel. If there is already a kernel
running that you want to connect to, you can pass the  ``--existing`` flag
which will skip initiating a new kernel and connect to the most recent kernel,
instead. To connect to a specific kernel once you have several kernels
running, use the ``%connect_info`` magic to get the unique connection file,
which will be something like ``--existing kernel-19732.json`` but with
different numbers which correspond to the Process ID of the kernel.

You can read more about using `jupyter qtconsole 
<http://jupyter.org/qtconsole/>`_, and
`jupyter notebook <http://jupyter-notebook.readthedocs.io/en/latest/>`_. There
is also a :ref:`message spec <messaging>` which documents the protocol for 
communication between kernels
and clients.

.. seealso::
    
    `Frontend/Kernel Model`_ example notebook


Interactive parallel computing
==============================

    
This functionality is optional and now part of the `ipyparallel
<http://ipyparallel.readthedocs.io/>`_ project.

Portability and Python requirements
-----------------------------------

Version 6.0+ supports compatibility with Python 3.3 and higher.
Versions 2.0 to 5.x work with Python 2.7.x releases and Python 3.3 and higher.
Version 1.0 additionally worked with Python 2.6 and 3.2.
Version 0.12 was the first version to fully support Python 3.

IPython is known to work on the following operating systems:

	* Linux
	* Most other Unix-like OSs (AIX, Solaris, BSD, etc.)
	* Mac OS X
	* Windows (CygWin, XP, Vista, etc.)

See :ref:`here <install_index>` for instructions on how to install IPython.

.. include:: links.txt

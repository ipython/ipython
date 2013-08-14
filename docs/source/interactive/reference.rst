=================
IPython reference
=================

.. _command_line_options:

Command-line usage
==================

You start IPython with the command::

    $ ipython [options] files

.. note::

  For IPython on Python 3, use ``ipython3`` in place of ``ipython``.

If invoked with no options, it executes all the files listed in sequence
and drops you into the interpreter while still acknowledging any options
you may have set in your ipython_config.py. This behavior is different from
standard Python, which when called as python -i will only execute one
file and ignore your configuration setup.

Please note that some of the configuration options are not available at
the command line, simply because they are not practical here. Look into
your configuration files for details on those. There are separate configuration 
files for each profile, and the files look like "ipython_config.py" or 
"ipython_config_<frontendname>.py".  Profile directories look like 
"profile_profilename" and are typically installed in the IPYTHONDIR directory.
For Linux users, this will be $HOME/.config/ipython, and for other users it 
will be $HOME/.ipython.  For Windows users, $HOME resolves to C:\\Documents and
Settings\\YourUserName in most instances.


Eventloop integration
---------------------

Previously IPython had command line options for controlling GUI event loop
integration (-gthread, -qthread, -q4thread, -wthread, -pylab). As of IPython
version 0.11, these have been removed. Please see the new ``%gui``
magic command or :ref:`this section <gui_support>` for details on the new
interface, or specify the gui at the commandline::

    $ ipython --gui=qt


Command-line Options
--------------------

To see the options IPython accepts, use ``ipython --help`` (and you probably
should run the output through a pager such as ``ipython --help | less`` for
more convenient reading).  This shows all the options that have a single-word
alias to control them, but IPython lets you configure all of its objects from
the command-line by passing the full class name and a corresponding value; type
``ipython --help-all`` to see this full list.  For example::

  ipython --matplotlib qt

is equivalent to::

  ipython --TerminalIPythonApp.matplotlib='qt'

Note that in the second form, you *must* use the equal sign, as the expression
is evaluated as an actual Python assignment.  While in the above example the
short form is more convenient, only the most common options have a short form,
while any configurable variable in IPython can be set at the command-line by
using the long form.  This long form is the same syntax used in the
configuration files, if you want to set these options permanently.


Interactive use
===============

IPython is meant to work as a drop-in replacement for the standard interactive
interpreter. As such, any code which is valid python should execute normally
under IPython (cases where this is not true should be reported as bugs). It
does, however, offer many features which are not available at a standard python
prompt. What follows is a list of these.


Caution for Windows users
-------------------------

Windows, unfortunately, uses the '\\' character as a path separator. This is a
terrible choice, because '\\' also represents the escape character in most
modern programming languages, including Python. For this reason, using '/'
character is recommended if you have problems with ``\``.  However, in Windows
commands '/' flags options, so you can not use it for the root directory. This
means that paths beginning at the root must be typed in a contrived manner
like: ``%copy \opt/foo/bar.txt \tmp``

.. _magic:

Magic command system
--------------------

IPython will treat any line whose first character is a % as a special
call to a 'magic' function. These allow you to control the behavior of
IPython itself, plus a lot of system-type features. They are all
prefixed with a % character, but parameters are given without
parentheses or quotes.

Lines that begin with ``%%`` signal a *cell magic*: they take as arguments not
only the rest of the current line, but all lines below them as well, in the
current execution block.  Cell magics can in fact make arbitrary modifications
to the input they receive, which need not even be valid Python code at all.
They receive the whole block as a single string.

As a line magic example, the ``%cd`` magic works just like the OS command of
the same name::

      In [8]: %cd
      /home/fperez

The following uses the builtin ``timeit`` in cell mode::
  
  In [10]: %%timeit x = range(10000)
      ...: min(x)
      ...: max(x)
      ...: 
  1000 loops, best of 3: 438 us per loop

In this case, ``x = range(10000)`` is called as the line argument, and the
block with ``min(x)`` and ``max(x)`` is called as the cell body.  The
``timeit`` magic receives both.
  
If you have 'automagic' enabled (as it by default), you don't need to type in
the single ``%`` explicitly for line magics; IPython will scan its internal
list of magic functions and call one if it exists. With automagic on you can
then just type ``cd mydir`` to go to directory 'mydir'::

      In [9]: cd mydir
      /home/fperez/mydir

Note that cell magics *always* require an explicit ``%%`` prefix, automagic
calling only works for line magics.
      
The automagic system has the lowest possible precedence in name searches, so
defining an identifier with the same name as an existing magic function will
shadow it for automagic use. You can still access the shadowed magic function
by explicitly using the ``%`` character at the beginning of the line.

An example (with automagic on) should clarify all this:

.. sourcecode:: ipython

    In [1]: cd ipython     # %cd is called by automagic
    /home/fperez/ipython

    In [2]: cd=1 	   # now cd is just a variable

    In [3]: cd .. 	   # and doesn't work as a function anymore
    File "<ipython-input-3-9fedb3aff56c>", line 1
      cd ..
          ^
    SyntaxError: invalid syntax


    In [4]: %cd .. 	   # but %cd always works
    /home/fperez

    In [5]: del cd     # if you remove the cd variable, automagic works again

    In [6]: cd ipython

    /home/fperez/ipython

Defining your own magics
++++++++++++++++++++++++

There are two main ways to define your own magic functions: from standalone
functions and by inheriting from a base class provided by IPython:
:class:`IPython.core.magic.Magics`.  Below we show code you can place in a file
that you load from your configuration, such as any file in the ``startup``
subdirectory of your default IPython profile.

First, let us see the simplest case.  The following shows how to create a line
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
	    print "Called as line magic"
	    return line
	else:
	    print "Called as cell magic"
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
    from IPython.core.magic import (Magics, magics_class, line_magic,
                                    cell_magic, line_cell_magic)

    # The class MUST call this class decorator at creation time
    @magics_class
    class MyMagics(Magics):

        @line_magic
        def lmagic(self, line):
            "my line magic"
            print "Full access to the main IPython object:", self.shell
            print "Variables in the user namespace:", self.shell.user_ns.keys()
            return line

        @cell_magic
        def cmagic(self, line, cell):
            "my cell magic"
            return line, cell

        @line_cell_magic
        def lcmagic(self, line, cell=None):
            "Magic that works both as %lcmagic and as %%lcmagic"
            if cell is None:
                print "Called as line magic"
                return line
            else:
                print "Called as cell magic"
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
        print "Line magic called with line:", line
	print "IPython object:", self.shell

    ip = get_ipython()
    # Declare this function as the magic %mycommand
    ip.define_magic('mycommand', func)

Type ``%magic`` for more information, including a list of all available magic
functions at any time and their docstrings. You can also type
``%magic_function_name?`` (see :ref:`below <dynamic_object_info>` for
information on the '?' system) to get information about any particular magic
function you are interested in.

The API documentation for the :mod:`IPython.core.magic` module contains the full
docstrings of all currently available magic commands.


Access to the standard Python help
----------------------------------

Simply type ``help()`` to access Python's standard help system. You can
also type ``help(object)`` for information about a given object, or
``help('keyword')`` for information on a keyword. You may need to configure your
PYTHONDOCS environment variable for this feature to work correctly.

.. _dynamic_object_info:

Dynamic object information
--------------------------

Typing ``?word`` or ``word?`` prints detailed information about an object. If
certain strings in the object are too long (e.g. function signatures) they get
snipped in the center for brevity. This system gives access variable types and
values, docstrings, function prototypes and other useful information.

If the information will not fit in the terminal, it is displayed in a pager
(``less`` if available, otherwise a basic internal pager).

Typing ``??word`` or ``word??`` gives access to the full information, including
the source code where possible. Long strings are not snipped.

The following magic functions are particularly useful for gathering
information about your working environment. You can get more details by
typing ``%magic`` or querying them individually (``%function_name?``);
this is just a summary:

    * **%pdoc <object>**: Print (or run through a pager if too long) the
      docstring for an object. If the given object is a class, it will
      print both the class and the constructor docstrings.
    * **%pdef <object>**: Print the call signature for any callable
      object. If the object is a class, print the constructor information.
    * **%psource <object>**: Print (or run through a pager if too long)
      the source code for an object.
    * **%pfile <object>**: Show the entire source file where an object was
      defined via a pager, opening it at the line where the object
      definition begins.
    * **%who/%whos**: These functions give information about identifiers
      you have defined interactively (not things you loaded or defined
      in your configuration files). %who just prints a list of
      identifiers and %whos prints a table with some basic details about
      each identifier.

Note that the dynamic object information functions (?/??, ``%pdoc``,
``%pfile``, ``%pdef``, ``%psource``) work on object attributes, as well as
directly on variables. For example, after doing ``import os``, you can use
``os.path.abspath??``.

.. _readline:

Readline-based features
-----------------------

These features require the GNU readline library, so they won't work if your
Python installation lacks readline support. We will first describe the default
behavior IPython uses, and then how to change it to suit your preferences.


Command line completion
+++++++++++++++++++++++

At any time, hitting TAB will complete any available python commands or
variable names, and show you a list of the possible completions if
there's no unambiguous one. It will also complete filenames in the
current directory if no python names match what you've typed so far.


Search command history
++++++++++++++++++++++

IPython provides two ways for searching through previous input and thus
reduce the need for repetitive typing:

   1. Start typing, and then use Ctrl-p (previous,up) and Ctrl-n
      (next,down) to search through only the history items that match
      what you've typed so far. If you use Ctrl-p/Ctrl-n at a blank
      prompt, they just behave like normal arrow keys.
   2. Hit Ctrl-r: opens a search prompt. Begin typing and the system
      searches your history for lines that contain what you've typed so
      far, completing as much as it can.


Persistent command history across sessions
++++++++++++++++++++++++++++++++++++++++++

IPython will save your input history when it leaves and reload it next
time you restart it. By default, the history file is named
$IPYTHONDIR/profile_<name>/history.sqlite. This allows you to keep
separate histories related to various tasks: commands related to
numerical work will not be clobbered by a system shell history, for
example.


Autoindent
++++++++++

IPython can recognize lines ending in ':' and indent the next line,
while also un-indenting automatically after 'raise' or 'return'.

This feature uses the readline library, so it will honor your
:file:`~/.inputrc` configuration (or whatever file your INPUTRC variable points
to). Adding the following lines to your :file:`.inputrc` file can make
indenting/unindenting more convenient (M-i indents, M-u unindents)::

    # if you don't already have a ~/.inputrc file, you need this include:
    $include /etc/inputrc
    
    $if Python 
    "\M-i": "    "  
    "\M-u": "\d\d\d\d"  
    $endif

Note that there are 4 spaces between the quote marks after "M-i" above.

.. warning::

    Setting the above indents will cause problems with unicode text entry in
    the terminal.

.. warning::

    Autoindent is ON by default, but it can cause problems with the pasting of
    multi-line indented code (the pasted code gets re-indented on each line). A
    magic function %autoindent allows you to toggle it on/off at runtime. You
    can also disable it permanently on in your :file:`ipython_config.py` file
    (set TerminalInteractiveShell.autoindent=False).
    
    If you want to paste multiple lines in the terminal, it is recommended that
    you use ``%paste``.


Customizing readline behavior
+++++++++++++++++++++++++++++

All these features are based on the GNU readline library, which has an
extremely customizable interface. Normally, readline is configured via a
file which defines the behavior of the library; the details of the
syntax for this can be found in the readline documentation available
with your system or on the Internet. IPython doesn't read this file (if
it exists) directly, but it does support passing to readline valid
options via a simple interface. In brief, you can customize readline by
setting the following options in your configuration file (note
that these options can not be specified at the command line):

    * **readline_parse_and_bind**: this holds a list of strings to be executed
      via a readline.parse_and_bind() command. The syntax for valid commands
      of this kind can be found by reading the documentation for the GNU
      readline library, as these commands are of the kind which readline
      accepts in its configuration file.
    * **readline_remove_delims**: a string of characters to be removed
      from the default word-delimiters list used by readline, so that
      completions may be performed on strings which contain them. Do not
      change the default value unless you know what you're doing.

You will find the default values in your configuration file.


Session logging and restoring
-----------------------------

You can log all input from a session either by starting IPython with the
command line switch ``--logfile=foo.py`` (see :ref:`here <command_line_options>`)
or by activating the logging at any moment with the magic function %logstart.

Log files can later be reloaded by running them as scripts and IPython
will attempt to 'replay' the log by executing all the lines in it, thus
restoring the state of a previous session. This feature is not quite
perfect, but can still be useful in many cases.

The log files can also be used as a way to have a permanent record of
any code you wrote while experimenting. Log files are regular text files
which you can later open in your favorite text editor to extract code or
to 'clean them up' before using them to replay a session.

The `%logstart` function for activating logging in mid-session is used as
follows::

    %logstart [log_name [log_mode]]

If no name is given, it defaults to a file named 'ipython_log.py' in your
current working directory, in 'rotate' mode (see below).

'%logstart name' saves to file 'name' in 'backup' mode. It saves your
history up to that point and then continues logging.

%logstart takes a second optional parameter: logging mode. This can be
one of (note that the modes are given unquoted):

    * [over:] overwrite existing log_name.
    * [backup:] rename (if exists) to log_name~ and start log_name.
    * [append:] well, that says it.
    * [rotate:] create rotating logs log_name.1~, log_name.2~, etc.

The %logoff and %logon functions allow you to temporarily stop and
resume logging to a file which had previously been started with
%logstart. They will fail (with an explanation) if you try to use them
before logging has been started.

.. _system_shell_access:

System shell access
-------------------

Any input line beginning with a ! character is passed verbatim (minus
the !, of course) to the underlying operating system. For example,
typing ``!ls`` will run 'ls' in the current directory.

Manual capture of command output
--------------------------------

You can assign the result of a system command to a Python variable with the
syntax ``myfiles = !ls``. This gets machine readable output from stdout 
(e.g. without colours), and splits on newlines. To explicitly get this sort of
output without assigning to a variable, use two exclamation marks (``!!ls``) or
the ``%sx`` magic command.

The captured list has some convenience features. ``myfiles.n`` or ``myfiles.s``
returns a string delimited by newlines or spaces, respectively. ``myfiles.p``
produces `path objects <http://pypi.python.org/pypi/path.py>`_ from the list items.
See :ref:`string_lists` for details.

IPython also allows you to expand the value of python variables when
making system calls. Wrap variables or expressions in {braces}::

    In [1]: pyvar = 'Hello world' 
    In [2]: !echo "A python variable: {pyvar}"  
    A python variable: Hello world
    In [3]: import math
    In [4]: x = 8
    In [5]: !echo {math.factorial(x)}
    40320

For simple cases, you can alternatively prepend $ to a variable name::

    In [6]: !echo $sys.argv  
    [/home/fperez/usr/bin/ipython]
    In [7]: !echo "A system variable: $$HOME"  # Use $$ for literal $
    A system variable: /home/fperez

System command aliases
----------------------

The %alias magic function allows you to define magic functions which are in fact
system shell commands. These aliases can have parameters.

``%alias alias_name cmd`` defines 'alias_name' as an alias for 'cmd'

Then, typing ``alias_name params`` will execute the system command 'cmd
params' (from your underlying operating system).

You can also define aliases with parameters using %s specifiers (one per
parameter). The following example defines the parts function as an
alias to the command 'echo first %s second %s' where each %s will be
replaced by a positional parameter to the call to %parts::

    In [1]: %alias parts echo first %s second %s
    In [2]: parts A B
    first A second B
    In [3]: parts A  
    ERROR: Alias <parts> requires 2 arguments, 1 given.

If called with no parameters, %alias prints the table of currently
defined aliases.

The %rehashx magic allows you to load your entire $PATH as
ipython aliases. See its docstring for further details.


.. _dreload:

Recursive reload
----------------

The :mod:`IPython.lib.deepreload` module allows you to recursively reload a
module: changes made to any of its dependencies will be reloaded without
having to exit. To start using it, do::

    from IPython.lib.deepreload import reload as dreload


Verbose and colored exception traceback printouts
-------------------------------------------------

IPython provides the option to see very detailed exception tracebacks,
which can be especially useful when debugging large programs. You can
run any Python file with the %run function to benefit from these
detailed tracebacks. Furthermore, both normal and verbose tracebacks can
be colored (if your terminal supports it) which makes them much easier
to parse visually.

See the magic xmode and colors functions for details (just type %magic).

These features are basically a terminal version of Ka-Ping Yee's cgitb
module, now part of the standard Python library.


.. _input_caching:

Input caching system
--------------------

IPython offers numbered prompts (In/Out) with input and output caching
(also referred to as 'input history'). All input is saved and can be 
retrieved as variables (besides the usual arrow key recall), in 
addition to the %rep magic command that brings a history entry
up for editing on the next  command line.

The following GLOBAL variables always exist (so don't overwrite them!):

* _i, _ii, _iii: store previous, next previous and next-next previous inputs.
* In, _ih : a list of all inputs; _ih[n] is the input from line n. If you
  overwrite In with a variable of your own, you can remake the assignment to the
  internal list with a simple ``In=_ih``.

Additionally, global variables named _i<n> are dynamically created (<n>
being the prompt counter), so ``_i<n> == _ih[<n>] == In[<n>]``.

For example, what you typed at prompt 14 is available as _i14, _ih[14]
and In[14].

This allows you to easily cut and paste multi line interactive prompts
by printing them out: they print like a clean string, without prompt
characters. You can also manipulate them like regular variables (they
are strings), modify or exec them (typing ``exec _i9`` will re-execute the
contents of input prompt 9.

You can also re-execute multiple lines of input easily by using the
magic %rerun or %macro functions. The macro system also allows you to re-execute
previous lines which include magic function calls (which require special
processing). Type %macro? for more details on the macro system.

A history function %hist allows you to see any part of your input
history by printing a range of the _i variables.

You can also search ('grep') through your history by typing 
``%hist -g somestring``. This is handy for searching for URLs, IP addresses,
etc. You can bring history entries listed by '%hist -g' up for editing
with the %recall command, or run them immediately with %rerun.

.. _output_caching:

Output caching system
---------------------

For output that is returned from actions, a system similar to the input
cache exists but using _ instead of _i. Only actions that produce a
result (NOT assignments, for example) are cached. If you are familiar
with Mathematica, IPython's _ variables behave exactly like
Mathematica's % variables.

The following GLOBAL variables always exist (so don't overwrite them!):

    * [_] (a single underscore) : stores previous output, like Python's
      default interpreter.
    * [__] (two underscores): next previous.
    * [___] (three underscores): next-next previous.

Additionally, global variables named _<n> are dynamically created (<n>
being the prompt counter), such that the result of output <n> is always
available as _<n> (don't use the angle brackets, just the number, e.g.
_21).

These variables are also stored in a global dictionary (not a
list, since it only has entries for lines which returned a result)
available under the names _oh and Out (similar to _ih and In). So the
output from line 12 can be obtained as _12, Out[12] or _oh[12]. If you
accidentally overwrite the Out variable you can recover it by typing
'Out=_oh' at the prompt.

This system obviously can potentially put heavy memory demands on your
system, since it prevents Python's garbage collector from removing any
previously computed results. You can control how many results are kept
in memory with the option (at the command line or in your configuration
file) cache_size. If you set it to 0, the whole system is completely
disabled and the prompts revert to the classic '>>>' of normal Python.


Directory history
-----------------

Your history of visited directories is kept in the global list _dh, and
the magic %cd command can be used to go to any entry in that list. The
%dhist command allows you to view this history. Do ``cd -<TAB>`` to
conveniently view the directory history.


Automatic parentheses and quotes
--------------------------------

These features were adapted from Nathan Gray's LazyPython. They are
meant to allow less typing for common situations.


Automatic parentheses
+++++++++++++++++++++

Callable objects (i.e. functions, methods, etc) can be invoked like this
(notice the commas between the arguments)::

    In [1]: callable_ob arg1, arg2, arg3
    ------> callable_ob(arg1, arg2, arg3)

You can force automatic parentheses by using '/' as the first character
of a line. For example::

    In [2]: /globals # becomes 'globals()'

Note that the '/' MUST be the first character on the line! This won't work::

    In [3]: print /globals # syntax error

In most cases the automatic algorithm should work, so you should rarely
need to explicitly invoke /. One notable exception is if you are trying
to call a function with a list of tuples as arguments (the parenthesis
will confuse IPython)::

    In [4]: zip (1,2,3),(4,5,6) # won't work

but this will work::

    In [5]: /zip (1,2,3),(4,5,6) 
    ------> zip ((1,2,3),(4,5,6))  
    Out[5]: [(1, 4), (2, 5), (3, 6)]

IPython tells you that it has altered your command line by displaying
the new command line preceded by ->. e.g.::

    In [6]: callable list 
    ------> callable(list)


Automatic quoting
+++++++++++++++++

You can force automatic quoting of a function's arguments by using ','
or ';' as the first character of a line. For example::

    In [1]: ,my_function /home/me  # becomes my_function("/home/me")

If you use ';' the whole argument is quoted as a single string, while ',' splits
on whitespace::

    In [2]: ,my_function a b c    # becomes my_function("a","b","c")

    In [3]: ;my_function a b c    # becomes my_function("a b c")

Note that the ',' or ';' MUST be the first character on the line! This
won't work::

    In [4]: x = ,my_function /home/me # syntax error

IPython as your default Python environment
==========================================

Python honors the environment variable PYTHONSTARTUP and will execute at
startup the file referenced by this variable. If you put the following code at
the end of that file, then IPython will be your working environment anytime you
start Python::

    from IPython.frontend.terminal.ipapp import launch_new_instance
    launch_new_instance()
    raise SystemExit

The ``raise SystemExit`` is needed to exit Python when
it finishes, otherwise you'll be back at the normal Python '>>>'
prompt.

This is probably useful to developers who manage multiple Python
versions and don't want to have correspondingly multiple IPython
versions. Note that in this mode, there is no way to pass IPython any
command-line options, as those are trapped first by Python itself.

.. _Embedding:

Embedding IPython
=================

You can start a regular IPython session with

.. sourcecode:: python

    import IPython
    IPython.start_ipython()

at any point in your program.  This will load IPython configuration,
startup files, and everything, just as if it were a normal IPython session.
In addition to this,
it is possible to embed an IPython instance inside your own Python programs.
This allows you to evaluate dynamically the state of your code,
operate with your variables, analyze them, etc. Note however that
any changes you make to values while in the shell do not propagate back
to the running code, so it is safe to modify your values because you
won't break your code in bizarre ways by doing so.

.. note::

  At present, embedding IPython cannot be done from inside IPython.
  Run the code samples below outside IPython.

This feature allows you to easily have a fully functional python
environment for doing object introspection anywhere in your code with a
simple function call. In some cases a simple print statement is enough,
but if you need to do more detailed analysis of a code fragment this
feature can be very valuable.

It can also be useful in scientific computing situations where it is
common to need to do some automatic, computationally intensive part and
then stop to look at data, plots, etc.
Opening an IPython instance will give you full access to your data and
functions, and you can resume program execution once you are done with
the interactive part (perhaps to stop again later, as many times as
needed).

The following code snippet is the bare minimum you need to include in
your Python programs for this to work (detailed examples follow later)::

    from IPython import embed

    embed() # this call anywhere in your program will start IPython

.. note::

    As of 0.13, you can embed an IPython *kernel*, for use with qtconsole,
    etc. via ``IPython.embed_kernel()`` instead of ``IPython.embed()``.
    It should function just the same as regular embed, but you connect
    an external frontend rather than IPython starting up in the local
    terminal.

You can run embedded instances even in code which is itself being run at
the IPython interactive prompt with '%run <filename>'. Since it's easy
to get lost as to where you are (in your top-level IPython or in your
embedded one), it's a good idea in such cases to set the in/out prompts
to something different for the embedded instances. The code examples
below illustrate this.

You can also have multiple IPython instances in your program and open
them separately, for example with different options for data
presentation. If you close and open the same instance multiple times,
its prompt counters simply continue from each execution to the next.

Please look at the docstrings in the :mod:`~IPython.frontend.terminal.embed` 
module for more details on the use of this system.

The following sample file illustrating how to use the embedding
functionality is provided in the examples directory as example-embed.py.
It should be fairly self-explanatory:

.. literalinclude:: ../../../examples/core/example-embed.py
    :language: python

Once you understand how the system functions, you can use the following
code fragments in your programs which are ready for cut and paste:

.. literalinclude:: ../../../examples/core/example-embed-short.py
    :language: python

Using the Python debugger (pdb)
===============================

Running entire programs via pdb
-------------------------------

pdb, the Python debugger, is a powerful interactive debugger which
allows you to step through code, set breakpoints, watch variables,
etc.  IPython makes it very easy to start any script under the control
of pdb, regardless of whether you have wrapped it into a 'main()'
function or not. For this, simply type '%run -d myscript' at an
IPython prompt. See the %run command's documentation (via '%run?' or
in Sec. magic_ for more details, including how to control where pdb
will stop execution first.

For more information on the use of the pdb debugger, read the included
pdb.doc file (part of the standard Python distribution). On a stock
Linux system it is located at /usr/lib/python2.3/pdb.doc, but the
easiest way to read it is by using the help() function of the pdb module
as follows (in an IPython prompt)::

    In [1]: import pdb
    In [2]: pdb.help()

This will load the pdb.doc document in a file viewer for you automatically.


Automatic invocation of pdb on exceptions
-----------------------------------------

IPython, if started with the ``--pdb`` option (or if the option is set in
your config file) can call the Python pdb debugger every time your code
triggers an uncaught exception. This feature
can also be toggled at any time with the %pdb magic command. This can be
extremely useful in order to find the origin of subtle bugs, because pdb
opens up at the point in your code which triggered the exception, and
while your program is at this point 'dead', all the data is still
available and you can walk up and down the stack frame and understand
the origin of the problem.

Furthermore, you can use these debugging facilities both with the
embedded IPython mode and without IPython at all. For an embedded shell
(see sec. Embedding_), simply call the constructor with
``--pdb`` in the argument string and pdb will automatically be called if an
uncaught exception is triggered by your code.

For stand-alone use of the feature in your programs which do not use
IPython at all, put the following lines toward the top of your 'main'
routine::

    import sys
    from IPython.core import ultratb
    sys.excepthook = ultratb.FormattedTB(mode='Verbose',
    color_scheme='Linux', call_pdb=1)

The mode keyword can be either 'Verbose' or 'Plain', giving either very
detailed or normal tracebacks respectively. The color_scheme keyword can
be one of 'NoColor', 'Linux' (default) or 'LightBG'. These are the same
options which can be set in IPython with ``--colors`` and ``--xmode``.

This will give any of your programs detailed, colored tracebacks with
automatic invocation of pdb.


Extensions for syntax processing
================================

This isn't for the faint of heart, because the potential for breaking
things is quite high. But it can be a very powerful and useful feature.
In a nutshell, you can redefine the way IPython processes the user input
line to accept new, special extensions to the syntax without needing to
change any of IPython's own code.

In the IPython/extensions directory you will find some examples
supplied, which we will briefly describe now. These can be used 'as is'
(and both provide very useful functionality), or you can use them as a
starting point for writing your own extensions.

.. _pasting_with_prompts:

Pasting of code starting with Python or IPython prompts
-------------------------------------------------------

IPython is smart enough to filter out input prompts, be they plain Python ones
(``>>>`` and ``...``) or IPython ones (``In [N]:`` and ``...:``).  You can
therefore copy and paste from existing interactive sessions without worry.

The following is a 'screenshot' of how things work, copying an example from the
standard Python tutorial::

    In [1]: >>> # Fibonacci series:

    In [2]: ... # the sum of two elements defines the next

    In [3]: ... a, b = 0, 1

    In [4]: >>> while b < 10:
       ...:     ...     print b
       ...:     ...     a, b = b, a+b
       ...:     
    1
    1
    2
    3
    5
    8

And pasting from IPython sessions works equally well::

    In [1]: In [5]: def f(x):
       ...:        ...:     "A simple function"
       ...:        ...:     return x**2
       ...:    ...: 

    In [2]: f(3)
    Out[2]: 9

.. _gui_support:

GUI event loop support
======================

.. versionadded:: 0.11
    The ``%gui`` magic and :mod:`IPython.lib.inputhook`.

IPython has excellent support for working interactively with Graphical User
Interface (GUI) toolkits, such as wxPython, PyQt4/PySide, PyGTK and Tk. This is
implemented using Python's builtin ``PyOSInputHook`` hook. This implementation
is extremely robust compared to our previous thread-based version. The
advantages of this are:

* GUIs can be enabled and disabled dynamically at runtime.
* The active GUI can be switched dynamically at runtime.
* In some cases, multiple GUIs can run simultaneously with no problems.
* There is a developer API in :mod:`IPython.lib.inputhook` for customizing 
  all of these things.

For users, enabling GUI event loop integration is simple.  You simple use the
``%gui`` magic as follows::

    %gui [GUINAME]

With no arguments, ``%gui`` removes all GUI support.  Valid ``GUINAME``
arguments are ``wx``, ``qt``, ``gtk`` and ``tk``.

Thus, to use wxPython interactively and create a running :class:`wx.App`
object, do::

    %gui wx

For information on IPython's matplotlib_ integration (and the ``matplotlib``
mode) see :ref:`this section <matplotlib_support>`.

For developers that want to use IPython's GUI event loop integration in the
form of a library, these capabilities are exposed in library form in the
:mod:`IPython.lib.inputhook` and :mod:`IPython.lib.guisupport` modules.
Interested developers should see the module docstrings for more information,
but there are a few points that should be mentioned here.

First, the ``PyOSInputHook`` approach only works in command line settings 
where readline is activated.  The integration with various eventloops
is handled somewhat differently (and more simply) when using the standalone
kernel, as in the qtconsole and notebook.

Second, when using the ``PyOSInputHook`` approach, a GUI application should
*not* start its event loop. Instead all of this is handled by the
``PyOSInputHook``. This means that applications that are meant to be used both
in IPython and as standalone apps need to have special code to detects how the
application is being run. We highly recommend using IPython's support for this.
Since the details vary slightly between toolkits, we point you to the various
examples in our source directory :file:`examples/lib` that demonstrate
these capabilities.

Third, unlike previous versions of IPython, we no longer "hijack" (replace
them with no-ops) the event loops. This is done to allow applications that
actually need to run the real event loops to do so. This is often needed to
process pending events at critical points.

Finally, we also have a number of examples in our source directory
:file:`examples/lib` that demonstrate these capabilities.

PyQt and PySide
---------------

.. attempt at explanation of the complete mess that is Qt support

When you use ``--gui=qt`` or ``--matplotlib=qt``, IPython can work with either
PyQt4 or PySide.  There are three options for configuration here, because
PyQt4 has two APIs for QString and QVariant - v1, which is the default on
Python 2, and the more natural v2, which is the only API supported by PySide.
v2 is also the default for PyQt4 on Python 3.  IPython's code for the QtConsole
uses v2, but you can still use any interface in your code, since the
Qt frontend is in a different process.

The default will be to import PyQt4 without configuration of the APIs, thus
matching what most applications would expect. It will fall back of PySide if
PyQt4 is unavailable.

If specified, IPython will respect the environment variable ``QT_API`` used
by ETS.  ETS 4.0 also works with both PyQt4 and PySide, but it requires
PyQt4 to use its v2 API.  So if ``QT_API=pyside`` PySide will be used,
and if ``QT_API=pyqt`` then PyQt4 will be used *with the v2 API* for
QString and QVariant, so ETS codes like MayaVi will also work with IPython.

If you launch IPython in matplotlib mode with ``ipython --matplotlib=qt``,
then IPython will ask matplotlib which Qt library to use (only if QT_API is
*not set*), via the 'backend.qt4' rcParam.  If matplotlib is version 1.0.1 or
older, then IPython will always use PyQt4 without setting the v2 APIs, since
neither v2 PyQt nor PySide work.

.. warning::

    Note that this means for ETS 4 to work with PyQt4, ``QT_API`` *must* be set
    to work with IPython's qt integration, because otherwise PyQt4 will be
    loaded in an incompatible mode.
    
    It also means that you must *not* have ``QT_API`` set if you want to
    use ``--gui=qt`` with code that requires PyQt4 API v1.


.. _matplotlib_support:

Plotting with matplotlib
========================

matplotlib_ provides high quality 2D and 3D plotting for Python. matplotlib_
can produce plots on screen using a variety of GUI toolkits, including Tk,
PyGTK, PyQt4 and wxPython. It also provides a number of commands useful for
scientific computing, all with a syntax compatible with that of the popular
Matlab program.

To start IPython with matplotlib support, use the ``--matplotlib`` switch. If
IPython is already running, you can run the ``%matplotlib`` magic.  If no
arguments are given, IPython will automatically detect your choice of
matplotlib backend.  You can also request a specific backend with
``%matplotlib backend``, where ``backend`` must be one of: 'tk', 'qt', 'wx',
'gtk', 'osx'.  In the web notebook and Qt console, 'inline' is also a valid
backend value, which produces static figures inlined inside the application
window instead of matplotlib's interactive figures that live in separate
windows.

.. _interactive_demos:

Interactive demos with IPython
==============================

IPython ships with a basic system for running scripts interactively in
sections, useful when presenting code to audiences. A few tags embedded
in comments (so that the script remains valid Python code) divide a file
into separate blocks, and the demo can be run one block at a time, with
IPython printing (with syntax highlighting) the block before executing
it, and returning to the interactive prompt after each block. The
interactive namespace is updated after each block is run with the
contents of the demo's namespace.

This allows you to show a piece of code, run it and then execute
interactively commands based on the variables just created. Once you
want to continue, you simply execute the next block of the demo. The
following listing shows the markup necessary for dividing a script into
sections for execution as a demo:

.. literalinclude:: ../../../examples/lib/example-demo.py
    :language: python

In order to run a file as a demo, you must first make a Demo object out
of it. If the file is named myscript.py, the following code will make a
demo::

    from IPython.lib.demo import Demo

    mydemo = Demo('myscript.py')

This creates the mydemo object, whose blocks you run one at a time by
simply calling the object with no arguments. If you have autocall active
in IPython (the default), all you need to do is type::

    mydemo 

and IPython will call it, executing each block. Demo objects can be
restarted, you can move forward or back skipping blocks, re-execute the
last block, etc. Simply use the Tab key on a demo object to see its
methods, and call '?' on them to see their docstrings for more usage
details. In addition, the demo module itself contains a comprehensive
docstring, which you can access via::

    from IPython.lib import demo

    demo?

Limitations: It is important to note that these demos are limited to
fairly simple uses. In particular, you cannot break up sections within
indented code (loops, if statements, function definitions, etc.)
Supporting something like this would basically require tracking the
internal execution state of the Python interpreter, so only top-level
divisions are allowed. If you want to be able to open an IPython
instance at an arbitrary point in a program, you can use IPython's
embedding facilities, see :func:`IPython.embed` for details.

.. include:: ../links.txt

# -*- coding: utf-8 -*-
"""Usage information for the main IPython applications.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys
from IPython.core import release

cl_usage = """\
=========
 IPython
=========

Tools for Interactive Computing in Python
=========================================

    A Python shell with automatic history (input and output), dynamic object
    introspection, easier configuration, command completion, access to the
    system shell and more.  IPython can also be embedded in running programs.


Usage

    ipython [subcommand] [options] [-c cmd | -m mod | file] [--] [arg] ...

    If invoked with no options, it executes the file and exits, passing the
    remaining arguments to the script, just as if you had specified the same
    command with python. You may need to specify `--` before args to be passed
    to the script, to prevent IPython from attempting to parse them. If you
    specify the option `-i` before the filename, it will enter an interactive
    IPython session after running the script, rather than exiting. Files ending
    in .py will be treated as normal Python, but files ending in .ipy can
    contain special IPython syntax (magic commands, shell expansions, etc.).

    Almost all configuration in IPython is available via the command-line. Do
    `ipython --help-all` to see all available options.  For persistent
    configuration, look into your `ipython_config.py` configuration file for
    details.

    This file is typically installed in the `IPYTHONDIR` directory, and there
    is a separate configuration directory for each profile. The default profile
    directory will be located in $IPYTHONDIR/profile_default. For Linux users,
    IPYTHONDIR defaults to `$HOME/.config/ipython`, and for other Unix systems
    to `$HOME/.ipython`.  For Windows users, $HOME resolves to C:\\Documents
    and Settings\\YourUserName in most instances.

    To initialize a profile with the default configuration file, do::

      $> ipython profile create

    and start editing `IPYTHONDIR/profile_default/ipython_config.py`

    In IPython's documentation, we will refer to this directory as
    `IPYTHONDIR`, you can change its default location by creating an
    environment variable with this name and setting it to the desired path.

    For more information, see the manual available in HTML and PDF in your
    installation, or online at http://ipython.org/documentation.html.
"""

interactive_usage = """
IPython -- An enhanced Interactive Python
=========================================

IPython offers a combination of convenient shell features, special commands
and a history mechanism for both input (command history) and output (results
caching, similar to Mathematica). It is intended to be a fully compatible
replacement for the standard Python interpreter, while offering vastly
improved functionality and flexibility.

At your system command line, type 'ipython -h' to see the command line
options available. This document only describes interactive features.

MAIN FEATURES
-------------

* Access to the standard Python help. As of Python 2.1, a help system is
  available with access to object docstrings and the Python manuals. Simply
  type 'help' (no quotes) to access it.

* Magic commands: type %magic for information on the magic subsystem.

* System command aliases, via the %alias command or the configuration file(s).

* Dynamic object information:

  Typing ?word or word? prints detailed information about an object.  If
  certain strings in the object are too long (docstrings, code, etc.) they get
  snipped in the center for brevity.

  Typing ??word or word?? gives access to the full information without
  snipping long strings. Long strings are sent to the screen through the less
  pager if longer than the screen, printed otherwise.

  The ?/?? system gives access to the full source code for any object (if
  available), shows function prototypes and other useful information.

  If you just want to see an object's docstring, type '%pdoc object' (without
  quotes, and without % if you have automagic on).

  Both %pdoc and ?/?? give you access to documentation even on things which are
  not explicitely defined. Try for example typing {}.get? or after import os,
  type os.path.abspath??. The magic functions %pdef, %source and %file operate
  similarly.

* Completion in the local namespace, by typing TAB at the prompt.

  At any time, hitting tab will complete any available python commands or
  variable names, and show you a list of the possible completions if there's
  no unambiguous one. It will also complete filenames in the current directory.

  This feature requires the readline and rlcomplete modules, so it won't work
  if your Python lacks readline support (such as under Windows).

* Search previous command history in two ways (also requires readline):

  - Start typing, and then use Ctrl-p (previous,up) and Ctrl-n (next,down) to
    search through only the history items that match what you've typed so
    far. If you use Ctrl-p/Ctrl-n at a blank prompt, they just behave like
    normal arrow keys.

  - Hit Ctrl-r: opens a search prompt. Begin typing and the system searches
    your history for lines that match what you've typed so far, completing as
    much as it can.

  - %hist: search history by index (this does *not* require readline).

* Persistent command history across sessions.

* Logging of input with the ability to save and restore a working session.

* System escape with !. Typing !ls will run 'ls' in the current directory.

* The reload command does a 'deep' reload of a module: changes made to the
  module since you imported will actually be available without having to exit.

* Verbose and colored exception traceback printouts. See the magic xmode and
  xcolor functions for details (just type %magic).

* Input caching system:

  IPython offers numbered prompts (In/Out) with input and output caching. All
  input is saved and can be retrieved as variables (besides the usual arrow
  key recall).

  The following GLOBAL variables always exist (so don't overwrite them!):
  _i: stores previous input.
  _ii: next previous.
  _iii: next-next previous.
  _ih : a list of all input _ih[n] is the input from line n.

  Additionally, global variables named _i<n> are dynamically created (<n>
  being the prompt counter), such that _i<n> == _ih[<n>]

  For example, what you typed at prompt 14 is available as _i14 and _ih[14].

  You can create macros which contain multiple input lines from this history,
  for later re-execution, with the %macro function.

  The history function %hist allows you to see any part of your input history
  by printing a range of the _i variables. Note that inputs which contain
  magic functions (%) appear in the history with a prepended comment. This is
  because they aren't really valid Python code, so you can't exec them.

* Output caching system:

  For output that is returned from actions, a system similar to the input
  cache exists but using _ instead of _i. Only actions that produce a result
  (NOT assignments, for example) are cached. If you are familiar with
  Mathematica, IPython's _ variables behave exactly like Mathematica's %
  variables.

  The following GLOBAL variables always exist (so don't overwrite them!):
  _ (one underscore): previous output.
  __ (two underscores): next previous.
  ___ (three underscores): next-next previous.

  Global variables named _<n> are dynamically created (<n> being the prompt
  counter), such that the result of output <n> is always available as _<n>.

  Finally, a global dictionary named _oh exists with entries for all lines
  which generated output.

* Directory history:

  Your history of visited directories is kept in the global list _dh, and the
  magic %cd command can be used to go to any entry in that list.

* Auto-parentheses and auto-quotes (adapted from Nathan Gray's LazyPython)

  1. Auto-parentheses
        
     Callable objects (i.e. functions, methods, etc) can be invoked like
     this (notice the commas between the arguments)::
       
         In [1]: callable_ob arg1, arg2, arg3
       
     and the input will be translated to this::
       
         callable_ob(arg1, arg2, arg3)
       
     This feature is off by default (in rare cases it can produce
     undesirable side-effects), but you can activate it at the command-line
     by starting IPython with `--autocall 1`, set it permanently in your
     configuration file, or turn on at runtime with `%autocall 1`.

     You can force auto-parentheses by using '/' as the first character
     of a line.  For example::
       
          In [1]: /globals             # becomes 'globals()'
       
     Note that the '/' MUST be the first character on the line!  This
     won't work::
       
          In [2]: print /globals    # syntax error

     In most cases the automatic algorithm should work, so you should
     rarely need to explicitly invoke /. One notable exception is if you
     are trying to call a function with a list of tuples as arguments (the
     parenthesis will confuse IPython)::
       
          In [1]: zip (1,2,3),(4,5,6)  # won't work
       
     but this will work::
       
          In [2]: /zip (1,2,3),(4,5,6)
          ------> zip ((1,2,3),(4,5,6))
          Out[2]= [(1, 4), (2, 5), (3, 6)]

     IPython tells you that it has altered your command line by
     displaying the new command line preceded by -->.  e.g.::
       
          In [18]: callable list
          -------> callable (list)

  2. Auto-Quoting
    
     You can force auto-quoting of a function's arguments by using ',' as
     the first character of a line.  For example::
       
          In [1]: ,my_function /home/me   # becomes my_function("/home/me")

     If you use ';' instead, the whole argument is quoted as a single
     string (while ',' splits on whitespace)::
       
          In [2]: ,my_function a b c   # becomes my_function("a","b","c")
          In [3]: ;my_function a b c   # becomes my_function("a b c")

     Note that the ',' MUST be the first character on the line!  This
     won't work::
       
          In [4]: x = ,my_function /home/me    # syntax error
"""

interactive_usage_min =  """\
An enhanced console for Python.
Some of its features are:
- Readline support if the readline library is present.
- Tab completion in the local namespace.
- Logging of input, see command-line options.
- System shell escape via ! , eg !ls.
- Magic commands, starting with a % (like %ls, %pwd, %cd, etc.)
- Keeps track of locally defined variables via %who, %whos.
- Show object information with a ? eg ?x or x? (use ?? for more info).
"""

quick_reference = r"""
IPython -- An enhanced Interactive Python - Quick Reference Card
================================================================

obj?, obj??      : Get help, or more help for object (also works as
                   ?obj, ??obj).
?foo.*abc*       : List names in 'foo' containing 'abc' in them.
%magic           : Information about IPython's 'magic' % functions.

Magic functions are prefixed by % or %%, and typically take their arguments
without parentheses, quotes or even commas for convenience.  Line magics take a
single % and cell magics are prefixed with two %%.

Example magic function calls:

%alias d ls -F   : 'd' is now an alias for 'ls -F'
alias d ls -F    : Works if 'alias' not a python name
alist = %alias   : Get list of aliases to 'alist'
cd /usr/share    : Obvious. cd -<tab> to choose from visited dirs.
%cd??            : See help AND source for magic %cd
%timeit x=10     : time the 'x=10' statement with high precision.
%%timeit x=2**100
x**100           : time 'x*100' with a setup of 'x=2**100'; setup code is not
                   counted.  This is an example of a cell magic.

System commands:

!cp a.txt b/     : System command escape, calls os.system()
cp a.txt b/      : after %rehashx, most system commands work without !
cp ${f}.txt $bar : Variable expansion in magics and system commands
files = !ls /usr : Capture sytem command output
files.s, files.l, files.n: "a b c", ['a','b','c'], 'a\nb\nc'

History:

_i, _ii, _iii    : Previous, next previous, next next previous input
_i4, _ih[2:5]    : Input history line 4, lines 2-4
exec _i81        : Execute input history line #81 again
%rep 81          : Edit input history line #81
_, __, ___       : previous, next previous, next next previous output
_dh              : Directory history
_oh              : Output history
%hist            : Command history. '%hist -g foo' search history for 'foo'

Autocall:

f 1,2            : f(1,2)  # Off by default, enable with %autocall magic.
/f 1,2           : f(1,2) (forced autoparen)
,f 1 2           : f("1","2")
;f 1 2           : f("1 2")

Remember: TAB completion works in many contexts, not just file names
or python names.

The following magic functions are currently available:

"""

gui_reference = """\
===============================
 The graphical IPython console
===============================

This console is designed to emulate the look, feel and workflow of a terminal
environment, while adding a number of enhancements that are simply not possible
in a real terminal, such as inline syntax highlighting, true multiline editing,
inline graphics and much more.

This quick reference document contains the basic information you'll need to
know to make the most efficient use of it.  For the various command line
options available at startup, type ``ipython qtconsole --help`` at the command line.


Multiline editing
=================

The graphical console is capable of true multiline editing, but it also tries
to behave intuitively like a terminal when possible.  If you are used to
IPython's old terminal behavior, you should find the transition painless, and
once you learn a few basic keybindings it will be a much more efficient
environment.

For single expressions or indented blocks, the console behaves almost like the
terminal IPython: single expressions are immediately evaluated, and indented
blocks are evaluated once a single blank line is entered::

    In [1]: print "Hello IPython!"  # Enter was pressed at the end of the line
    Hello IPython!

    In [2]: for i in range(10):
       ...: 	print i,
       ...:
    0 1 2 3 4 5 6 7 8 9

If you want to enter more than one expression in a single input block
(something not possible in the terminal), you can use ``Control-Enter`` at the
end of your first line instead of ``Enter``.  At that point the console goes
into 'cell mode' and even if your inputs are not indented, it will continue
accepting arbitrarily many lines until either you enter an extra blank line or
you hit ``Shift-Enter`` (the key binding that forces execution).  When a
multiline cell is entered, IPython analyzes it and executes its code producing
an ``Out[n]`` prompt only for the last expression in it, while the rest of the
cell is executed as if it was a script.  An example should clarify this::

    In [3]: x=1  # Hit C-Enter here
       ...: y=2  # from now on, regular Enter is sufficient
       ...: z=3
       ...: x**2  # This does *not* produce an Out[] value
       ...: x+y+z  # Only the last expression does
       ...:
    Out[3]: 6

The behavior where an extra blank line forces execution is only active if you
are actually typing at the keyboard each line, and is meant to make it mimic
the IPython terminal behavior.  If you paste a long chunk of input (for example
a long script copied form an editor or web browser), it can contain arbitrarily
many intermediate blank lines and they won't cause any problems.  As always,
you can then make it execute by appending a blank line *at the end* or hitting
``Shift-Enter`` anywhere within the cell.

With the up arrow key, you can retrieve previous blocks of input that contain
multiple lines.  You can move inside of a multiline cell like you would in any
text editor.  When you want it executed, the simplest thing to do is to hit the
force execution key, ``Shift-Enter`` (though you can also navigate to the end
and append a blank line by using ``Enter`` twice).

If you've edited a multiline cell and accidentally navigate out of it with the
up or down arrow keys, IPython will clear the cell and replace it with the
contents of the one above or below that you navigated to.  If this was an
accident and you want to retrieve the cell you were editing, use the Undo
keybinding, ``Control-z``.


Key bindings
============

The IPython console supports most of the basic Emacs line-oriented keybindings,
in addition to some of its own.

The keybinding prefixes mean:

- ``C``: Control
- ``S``: Shift
- ``M``: Meta (typically the Alt key)

The keybindings themselves are:

- ``Enter``: insert new line (may cause execution, see above).
- ``C-Enter``: *force* new line, *never* causes execution.
- ``S-Enter``: *force* execution regardless of where cursor is, no newline added.
- ``Up``: step backwards through the history.
- ``Down``: step forwards through the history.
- ``S-Up``: search backwards through the history (like ``C-r`` in bash).
- ``S-Down``: search forwards through the history.
- ``C-c``: copy highlighted text to clipboard (prompts are automatically stripped).
- ``C-S-c``: copy highlighted text to clipboard (prompts are not stripped).
- ``C-v``: paste text from clipboard.
- ``C-z``: undo (retrieves lost text if you move out of a cell with the arrows).
- ``C-S-z``: redo.
- ``C-o``: move to 'other' area, between pager and terminal.
- ``C-l``: clear terminal.
- ``C-a``: go to beginning of line.
- ``C-e``: go to end of line.
- ``C-u``: kill from cursor to the begining of the line.
- ``C-k``: kill from cursor to the end of the line.
- ``C-y``: yank (paste)
- ``C-p``: previous line (like up arrow)
- ``C-n``: next line (like down arrow)
- ``C-f``: forward (like right arrow)
- ``C-b``: back (like left arrow)
- ``C-d``: delete next character, or exits if input is empty
- ``M-<``: move to the beginning of the input region.
- ``M->``: move to the end of the input region.
- ``M-d``: delete next word.
- ``M-Backspace``: delete previous word.
- ``C-.``: force a kernel restart (a confirmation dialog appears).
- ``C-+``: increase font size.
- ``C--``: decrease font size.
- ``C-M-Space``: toggle full screen. (Command-Control-Space on Mac OS X)

The IPython pager
=================

IPython will show long blocks of text from many sources using a builtin pager.
You can control where this pager appears with the ``--paging`` command-line
flag:

- ``inside`` [default]: the pager is overlaid on top of the main terminal. You
  must quit the pager to get back to the terminal (similar to how a pager such
  as ``less`` or ``more`` works).

- ``vsplit``: the console is made double-tall, and the pager appears on the
  bottom area when needed.  You can view its contents while using the terminal.

- ``hsplit``: the console is made double-wide, and the pager appears on the
  right area when needed.  You can view its contents while using the terminal.

- ``none``: the console never pages output.

If you use the vertical or horizontal paging modes, you can navigate between
terminal and pager as follows:

- Tab key: goes from pager to terminal (but not the other way around).
- Control-o: goes from one to another always.
- Mouse: click on either.

In all cases, the ``q`` or ``Escape`` keys quit the pager (when used with the
focus on the pager area).

Running subprocesses
====================

The graphical IPython console uses the ``pexpect`` module to run subprocesses
when you type ``!command``.  This has a number of advantages (true asynchronous
output from subprocesses as well as very robust termination of rogue
subprocesses with ``Control-C``), as well as some limitations.  The main
limitation is that you can *not* interact back with the subprocess, so anything
that invokes a pager or expects you to type input into it will block and hang
(you can kill it with ``Control-C``).

We have provided as magics ``%less`` to page files (aliased to ``%more``),
``%clear`` to clear the terminal, and ``%man`` on Linux/OSX.  These cover the
most common commands you'd want to call in your subshell and that would cause
problems if invoked via ``!cmd``, but you need to be aware of this limitation.

Display
=======

The IPython console can now display objects in a variety of formats, including
HTML, PNG and SVG. This is accomplished using the display functions in
``IPython.core.display``::

    In [4]: from IPython.core.display import display, display_html

    In [5]: from IPython.core.display import display_png, display_svg

Python objects can simply be passed to these functions and the appropriate
representations will be displayed in the console as long as the objects know
how to compute those representations. The easiest way of teaching objects how
to format themselves in various representations is to define special methods
such as: ``_repr_html_``, ``_repr_svg_`` and ``_repr_png_``. IPython's display formatters
can also be given custom formatter functions for various types::

    In [6]: ip = get_ipython()

    In [7]: html_formatter = ip.display_formatter.formatters['text/html']

    In [8]: html_formatter.for_type(Foo, foo_to_html)

For further details, see ``IPython.core.formatters``.

Inline matplotlib graphics
==========================

The IPython console is capable of displaying matplotlib figures inline, in SVG
or PNG format.  If started with the ``pylab=inline``, then all figures are
rendered inline automatically (PNG by default).  If started with ``--pylab``
or ``pylab=<your backend>``, then a GUI backend will be used, but IPython's
``display()`` and ``getfigs()`` functions can be used to view plots inline::

    In [9]: display(*getfigs())    # display all figures inline

    In[10]: display(*getfigs(1,2)) # display figures 1 and 2 inline
"""


quick_guide = """\
?         -> Introduction and overview of IPython's features.
%quickref -> Quick reference.
help      -> Python's own help system.
object?   -> Details about 'object', use 'object??' for extra details.
"""

gui_note = """\
%guiref   -> A brief reference about the graphical user interface.
"""

default_banner_parts = [
    'Python %s\n' % (sys.version.split('\n')[0],),
    'Type "copyright", "credits" or "license" for more information.\n\n',
    'IPython %s -- An enhanced Interactive Python.\n' % (release.version,),
    quick_guide
]

default_gui_banner_parts = default_banner_parts + [gui_note]

default_banner = ''.join(default_banner_parts)

default_gui_banner = ''.join(default_gui_banner_parts)

# page GUI Reference, for use as a magic:

def page_guiref(arg_s=None):
    """Show a basic reference about the GUI Console."""
    from IPython.core import page
    page.page(gui_reference, auto_html=True)


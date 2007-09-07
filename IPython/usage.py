# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# $Id: usage.py 2723 2007-09-07 07:44:16Z fperez $

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license
__version__ = Release.version

__doc__ = """
IPython -- An enhanced Interactive Python
=========================================

A Python shell with automatic history (input and output), dynamic object
introspection, easier configuration, command completion, access to the system
shell and more.

IPython can also be embedded in running programs. See EMBEDDING below.


USAGE
       ipython [options] files

       If invoked with no options, it executes all the files listed in
       sequence and drops you into the interpreter while still acknowledging
       any options you may have set in your ipythonrc file. This behavior is
       different from standard Python, which when called as python -i will
       only execute one file and will ignore your configuration setup.

       Please note that some of the configuration options are not available at
       the command line, simply because they are not practical here. Look into
       your ipythonrc configuration file for details on those. This file
       typically installed in the $HOME/.ipython directory.

       For Windows users, $HOME resolves to C:\\Documents and
       Settings\\YourUserName in most instances, and _ipython is used instead
       of .ipython, since some Win32 programs have problems with dotted names
       in directories.

       In the rest of this text, we will refer to this directory as
       IPYTHONDIR.


SPECIAL THREADING OPTIONS
       The following special options are ONLY valid at the  beginning  of  the
       command line, and not later.  This is because they control the initial-
       ization of ipython itself, before the normal option-handling  mechanism
       is active.

       -gthread, -qthread, -q4thread, -wthread, -pylab

              Only ONE of these can be given, and it can only be given as the
              first option passed to IPython (it will have no effect in any
              other position).  They provide threading support for the GTK, QT
              and WXWidgets toolkits, and for the matplotlib library.

              With any of the first four options, IPython starts running a
              separate thread for the graphical toolkit's operation, so that
              you can open and control graphical elements from within an
              IPython command line, without blocking.  All four provide
              essentially the same functionality, respectively for GTK, QT3,
              QT4 and WXWidgets (via their Python interfaces).

              Note that with -wthread, you can additionally use the -wxversion
              option to request a specific version of wx to be used.  This
              requires that you have the 'wxversion' Python module installed,
              which is part of recent wxPython distributions.

              If -pylab is given, IPython loads special support for the mat-
              plotlib library (http://matplotlib.sourceforge.net), allowing
              interactive usage of any of its backends as defined in the
              user's .matplotlibrc file.  It automatically activates GTK, QT
              or WX threading for IPyhton if the choice of matplotlib backend
              requires it.  It also modifies the %run command to correctly
              execute (without blocking) any matplotlib-based script which
              calls show() at the end.

       -tk    The -g/q/q4/wthread options, and -pylab (if matplotlib is
              configured to use GTK, QT or WX), will normally block Tk
              graphical interfaces.  This means that when GTK, QT or WX
              threading is active, any attempt to open a Tk GUI will result in
              a dead window, and possibly cause the Python interpreter to
              crash.  An extra option, -tk, is available to address this
              issue.  It can ONLY be given as a SECOND option after any of the
              above (-gthread, -qthread, q4thread, -wthread or -pylab).

              If -tk is given, IPython will try to coordinate Tk threading
              with GTK, QT or WX.  This is however potentially unreliable, and
              you will have to test on your platform and Python configuration
              to determine whether it works for you.  Debian users have
              reported success, apparently due to the fact that Debian builds
              all of Tcl, Tk, Tkinter and Python with pthreads support.  Under
              other Linux environments (such as Fedora Core 2/3), this option
              has caused random crashes and lockups of the Python interpreter.
              Under other operating systems (Mac OSX and Windows), you'll need
              to try it to find out, since currently no user reports are
              available.

              There is unfortunately no way for IPython to determine  at  run-
              time  whether -tk will work reliably or not, so you will need to
              do some experiments before relying on it for regular work.

A WARNING ABOUT SIGNALS AND THREADS

       When any of the thread systems (GTK, QT or WX) are active, either
       directly or via -pylab with a threaded backend, it is impossible to
       interrupt long-running Python code via Ctrl-C.  IPython can not pass
       the KeyboardInterrupt exception (or the underlying SIGINT) across
       threads, so any long-running process started from IPython will run to
       completion, or will have to be killed via an external (OS-based)
       mechanism.

       To the best of my knowledge, this limitation is imposed by the Python
       interpreter itself, and it comes from the difficulty of writing
       portable signal/threaded code.  If any user is an expert on this topic
       and can suggest a better solution, I would love to hear about it.  In
       the IPython sources, look at the Shell.py module, and in particular at
       the runcode() method.

REGULAR OPTIONS
       After the above threading options have been given, regular options  can
       follow  in any order.  All options can be abbreviated to their shortest
       non-ambiguous form and are case-sensitive.  One or two  dashes  can  be
       used.   Some options have an alternate short form, indicated after a |.

       Most options can also be set from your  ipythonrc  configuration  file.
       See the provided examples for assistance.  Options given on the comman-
       dline override the values set in the ipythonrc file.

       All options with a [no] prepended can be specified in negated form
       (using -nooption instead of -option) to turn the feature off.

       -h, --help
              Show summary of options.

       -pylab This can only be given as the first option passed to IPython (it
              will have no effect in any other position). It adds special sup-
              port   for  the  matplotlib  library  (http://matplotlib.source-
              forge.net), allowing interactive usage of any of its backends as
              defined  in  the  user's  .matplotlibrc  file.  It automatically
              activates GTK or WX threading for IPyhton if the choice of  mat-
              plotlib  backend requires it.  It also modifies the @run command
              to correctly execute  (without  blocking)  any  matplotlib-based
              script which calls show() at the end.

       -autocall <val>
              Make IPython automatically call any callable object even if you
              didn't type explicit parentheses. For example, 'str 43' becomes
              'str(43)' automatically.  The value can be '0' to disable the
              feature, '1' for 'smart' autocall, where it is not applied if
              there are no more arguments on the line, and '2' for 'full'
              autocall, where all callable objects are automatically called
              (even if no arguments are present).  The default is '1'.

       -[no]autoindent
              Turn automatic indentation on/off.

       -[no]automagic
              Make magic commands automatic (without needing their first char-
              acter to be %).  Type %magic at  the  IPython  prompt  for  more
              information.

       -[no]autoedit_syntax
              When a syntax error occurs after editing a file, automatically
              open the file to the trouble causing line for convenient fixing.

       -[no]banner
              Print the intial information banner (default on).

       -c <command>
              Execute  the  given  command  string, and set sys.argv to ['c'].
              This is similar to the -c option in  the  normal  Python  inter-
              preter.

       -cache_size|cs <n>
              Size  of  the output cache (maximum number of entries to hold in
              memory).  The default is 1000, you can change it permanently  in
              your  config  file.   Setting  it  to  0 completely disables the
              caching system, and the minimum value accepted  is  20  (if  you
              provide  a value less than 20, it is reset to 0 and a warning is
              issued).  This limit is defined because otherwise  you'll  spend
              more time re-flushing a too small cache than working.

       -classic|cl
              Gives IPython a similar feel to the classic Python prompt.

       -colors <scheme>
              Color  scheme  for  prompts  and exception reporting.  Currently
              implemented: NoColor, Linux, and LightBG.

       -[no]color_info
              IPython can display information about objects via a set of func-
              tions, and optionally can use colors for this, syntax highlight-
              ing source code and various other  elements.   However,  because
              this  information  is  passed  through a pager (like 'less') and
              many pagers get confused with color codes, this option is off by
              default.   You  can  test  it and turn it on permanently in your
              ipythonrc file if it works for you.  As a reference, the  'less'
              pager  supplied  with  Mandrake 8.2 works ok, but that in RedHat
              7.2 doesn't.

              Test it and turn it on permanently if it works with your system.
              The  magic function @color_info allows you to toggle this inter-
              actively for testing.

       -[no]confirm_exit
              Set to confirm when you try to exit IPython with  an  EOF  (Con-
              trol-D in Unix, Control-Z/Enter in Windows). Note that using the
              magic functions @Exit or @Quit you  can  force  a  direct  exit,
              bypassing any confirmation.

       -[no]debug
              Show  information  about the loading process. Very useful to pin
              down problems with your configuration files or  to  get  details
              about session restores.

       -[no]deep_reload
              IPython  can use the deep_reload module which reloads changes in
              modules recursively (it replaces the reload() function,  so  you
              don't need to change anything to use it). deep_reload() forces a
              full reload of modules whose code may have  changed,  which  the
              default reload() function does not.

              When  deep_reload  is off, IPython will use the normal reload(),
              but deep_reload will still be available as dreload(). This  fea-
              ture  is  off  by default [which means that you have both normal
              reload() and dreload()].

       -editor <name>
              Which editor to use with the @edit command. By default,  IPython
              will  honor  your EDITOR environment variable (if not set, vi is
              the Unix default and notepad the Windows one). Since this editor
              is  invoked on the fly by IPython and is meant for editing small
              code snippets, you may want to use a small,  lightweight  editor
              here (in case your default EDITOR is something like Emacs).

       -ipythondir <name>
              The  name  of  your  IPython configuration directory IPYTHONDIR.
              This can also be  specified  through  the  environment  variable
              IPYTHONDIR.

       -log|l Generate  a log file of all input. The file is named
              ipython_log.py in your current directory (which prevents logs
              from multiple IPython sessions from trampling each other). You
              can use this to later restore a session by loading your logfile
              as a file to be executed with option -logplay (see below).

       -logfile|lf
              Specify the name of your logfile.

       -logplay|lp
              Replay  a previous log. For restoring a session as close as pos-
              sible to the state you left it in, use this option  (don't  just
              run the logfile). With -logplay, IPython will try to reconstruct
              the previous working environment in full, not just  execute  the
              commands in the logfile.
              When  a  session is restored, logging is automatically turned on
              again with the name of the logfile it was invoked  with  (it  is
              read  from the log header). So once you've turned logging on for
              a session, you can quit IPython and reload it as many  times  as
              you  want  and  it  will continue to log its history and restore
              from the beginning every time.

              Caveats: there are limitations in this option. The history vari-
              ables  _i*,_* and _dh don't get restored properly. In the future
              we will try to implement full  session  saving  by  writing  and
              retrieving  a failed because of inherent limitations of Python's
              Pickle module, so this may have to wait.

       -[no]messages
              Print messages which IPython collects about its startup  process
              (default on).

       -[no]pdb
              Automatically  call the pdb debugger after every uncaught excep-
              tion. If you are used to debugging  using  pdb,  this  puts  you
              automatically  inside of it after any call (either in IPython or
              in code called by it) which triggers  an  exception  which  goes
              uncaught.

       -[no]pprint
              IPython  can  optionally  use the pprint (pretty printer) module
              for displaying results. pprint tends to give a nicer display  of
              nested  data structures. If you like it, you can turn it on per-
              manently in your config file (default off).

       -profile|p <name>
              Assume that your config file is ipythonrc-<name> (looks in  cur-
              rent dir first, then in IPYTHONDIR). This is a quick way to keep
              and load multiple config files for different  tasks,  especially
              if  you  use  the include option of config files. You can keep a
              basic IPYTHONDIR/ipythonrc file and then have  other  'profiles'
              which  include  this  one  and  load extra things for particular
              tasks. For example:

              1) $HOME/.ipython/ipythonrc : load basic things you always want.
              2)  $HOME/.ipython/ipythonrc-math  :  load  (1)  and basic math-
              related modules.
              3) $HOME/.ipython/ipythonrc-numeric : load (1) and  Numeric  and
              plotting modules.

              Since  it is possible to create an endless loop by having circu-
              lar file inclusions, IPython will stop if it reaches  15  recur-
              sive inclusions.

       -prompt_in1|pi1 <string>
              Specify  the string used for input prompts. Note that if you are
              using numbered prompts, the number is represented with a '\#' in
              the  string.  Don't forget to quote strings with spaces embedded
              in them. Default: 'In [\#]: '.

              Most bash-like  escapes  can  be  used  to  customize  IPython's
              prompts, as well as a few additional ones which are IPython-spe-
              cific.  All valid prompt escapes are described in detail in  the
              Customization section of the IPython HTML/PDF manual.

       -prompt_in2|pi2 <string>
              Similar to the previous option, but used for the continuation
              prompts. The special sequence '\D' is similar to '\#', but with
              all digits replaced dots (so you can have your continuation
              prompt aligned with your input prompt).  Default: ' .\D.: '
              (note three spaces at the start for alignment with 'In [\#]').

       -prompt_out|po <string>
              String   used   for  output  prompts,  also  uses  numbers  like
              prompt_in1.  Default: 'Out[\#]:'.

       -quick Start in bare bones mode (no config file loaded).

       -rcfile <name>
              Name of your  IPython  resource  configuration  file.   normally
              IPython    loads   ipythonrc   (from   current   directory)   or
              IPYTHONDIR/ipythonrc.  If the loading of your config file fails,
              IPython  starts  with  a  bare  bones  configuration (no modules
              loaded at all).

       -[no]readline
              Use the readline library, which is needed to support  name  com-
              pletion  and  command history, among other things. It is enabled
              by default, but may cause  problems  for  users  of  X/Emacs  in
              Python comint or shell buffers.

              Note  that  emacs 'eterm' buffers (opened with M-x term) support
              IPython's readline and syntax coloring fine, only  'emacs'  (M-x
              shell and C-c !)  buffers do not.

       -screen_length|sl <n>
              Number  of lines of your screen.  This is used to control print-
              ing of very long strings.  Strings longer than  this  number  of
              lines  will be sent through a pager instead of directly printed.

              The default value for this is 0, which means IPython will  auto-
              detect  your  screen  size  every time it needs to print certain
              potentially long strings (this doesn't change  the  behavior  of
              the  'print'  keyword,  it's  only triggered internally). If for
              some reason this isn't working well (it needs  curses  support),
              specify it yourself. Otherwise don't change the default.

       -separate_in|si <string>
              Separator before input prompts.  Default '0.

       -separate_out|so <string>
              Separator before output prompts.  Default: 0 (nothing).

       -separate_out2|so2 <string>
              Separator after output prompts.  Default: 0 (nothing).

       -nosep Shorthand for '-separate_in 0 -separate_out 0 -separate_out2 0'.
              Simply removes all input/output separators.

       -upgrade
              Allows you to upgrade your  IPYTHONDIR  configuration  when  you
              install  a  new  version  of  IPython.   Since  new versions may
              include new command lines options or example files, this  copies
              updated ipythonrc-type files.  However, it backs up (with a .old
              extension) all files which it overwrites so that you  can  merge
              back any custimizations you might have in your personal files.

       -Version
              Print version information and exit.

       -wxversion <string>
              Select a specific version of wxPython (used in conjunction with
              -wthread). Requires the wxversion module, part of recent
              wxPython distributions.

       -xmode <modename>
              Mode  for  exception reporting.  The valid modes are Plain, Con-
              text, and Verbose.

              - Plain: similar to python's normal traceback printing.

              - Context: prints 5 lines of context  source  code  around  each
              line in the traceback.

              - Verbose: similar to Context, but additionally prints the vari-
              ables currently visible where the exception happened (shortening
              their  strings if too long).  This can potentially be very slow,
              if you happen to have a huge data structure whose string  repre-
              sentation  is  complex  to compute.  Your computer may appear to
              freeze for a while with cpu usage at 100%.  If this occurs,  you
              can cancel the traceback with Ctrl-C (maybe hitting it more than
              once).


EMBEDDING
       It is possible to start an IPython instance inside your own Python pro-
       grams.  In the documentation example files there are some illustrations
       on how to do this.

       This feature allows you to evalutate  dynamically  the  state  of  your
       code,  operate  with  your  variables, analyze them, etc.  Note however
       that any changes you make to values while in the shell do NOT propagate
       back  to  the running code, so it is safe to modify your values because
       you won't break your code in bizarre ways by doing so.
"""

cmd_line_usage = __doc__

#---------------------------------------------------------------------------
interactive_usage = """
IPython -- An enhanced Interactive Python
=========================================

IPython offers a combination of convenient shell features, special commands
and a history mechanism for both input (command history) and output (results
caching, similar to Mathematica). It is intended to be a fully compatible
replacement for the standard Python interpreter, while offering vastly
improved functionality and flexibility.

At your system command line, type 'ipython -help' to see the command line
options available. This document only describes interactive features.

Warning: IPython relies on the existence of a global variable called __IP which
controls the shell itself. If you redefine __IP to anything, bizarre behavior
will quickly occur.

MAIN FEATURES

* Access to the standard Python help. As of Python 2.1, a help system is
  available with access to object docstrings and the Python manuals. Simply
  type 'help' (no quotes) to access it.

* Magic commands: type %magic for information on the magic subsystem.

* System command aliases, via the %alias command or the ipythonrc config file.

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

* Persistent command history across sessions (readline required).

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
        this (notice the commas between the arguments):
            >>> callable_ob arg1, arg2, arg3
        and the input will be translated to this:
            --> callable_ob(arg1, arg2, arg3)
        You can force auto-parentheses by using '/' as the first character
        of a line.  For example:
            >>> /globals             # becomes 'globals()'
        Note that the '/' MUST be the first character on the line!  This
        won't work:
            >>> print /globals    # syntax error
            
        In most cases the automatic algorithm should work, so you should
        rarely need to explicitly invoke /. One notable exception is if you
        are trying to call a function with a list of tuples as arguments (the
        parenthesis will confuse IPython):
            In [1]: zip (1,2,3),(4,5,6)  # won't work
        but this will work:
            In [2]: /zip (1,2,3),(4,5,6)
            ------> zip ((1,2,3),(4,5,6))
            Out[2]= [(1, 4), (2, 5), (3, 6)]        

        IPython tells you that it has altered your command line by
        displaying the new command line preceded by -->.  e.g.:
            In [18]: callable list
            -------> callable (list) 

    2. Auto-Quoting
        You can force auto-quoting of a function's arguments by using ',' as
        the first character of a line.  For example:
            >>> ,my_function /home/me   # becomes my_function("/home/me")

        If you use ';' instead, the whole argument is quoted as a single
        string (while ',' splits on whitespace):
            >>> ,my_function a b c   # becomes my_function("a","b","c")
            >>> ;my_function a b c   # becomes my_function("a b c")

        Note that the ',' MUST be the first character on the line!  This
        won't work:
            >>> x = ,my_function /home/me    # syntax error
"""

quick_reference = r"""
IPython -- An enhanced Interactive Python - Quick Reference Card
================================================================

obj?, obj??      : Get help, or more help for object (also works as
                   ?obj, ??obj).
?foo.*abc*       : List names in 'foo' containing 'abc' in them.
%magic           : Information about IPython's 'magic' % functions.

Magic functions are prefixed by %, and typically take their arguments without
parentheses, quotes or even commas for convenience.
 
Example magic function calls:

%alias d ls -F   : 'd' is now an alias for 'ls -F'
alias d ls -F    : Works if 'alias' not a python name
alist = %alias   : Get list of aliases to 'alist'
cd /usr/share    : Obvious. cd -<tab> to choose from visited dirs.
%cd??            : See help AND source for magic %cd

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

f 1,2            : f(1,2)
/f 1,2           : f(1,2) (forced autoparen)
,f 1 2           : f("1","2")
;f 1 2           : f("1 2")

Remember: TAB completion works in many contexts, not just file names
or python names.

The following magic functions are currently available:

"""



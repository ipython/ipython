# -*- coding: utf-8 -*-
"""Modified input prompt for executing files.

We define a special input line filter to allow typing lines which begin with
'~', '/' or '.'. If one of those strings is encountered, it is automatically
executed.
"""

#*****************************************************************************
#       Copyright (C) 2004 W.J. van der Laan <gnufnork@hetdigitalegat.nl>
#       Copyright (C) 2004-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************


def prefilter_shell(self,line,continuation):
    """Alternate prefilter, modified for shell-like functionality.

    - Execute all lines beginning with '~', '/' or '.'
    - $var=cmd <=> %sc var=cmd
    - $$var=cmd <=> %sc -l var=cmd
    """

    if line:
        l0 = line[0]
        if l0 in '~/.':
            return self._prefilter("!%s"%line,continuation)
        elif l0=='$':
            lrest = line[1:]
            if lrest.startswith('$'):
                # $$var=cmd <=> %sc -l var=cmd
                return self._prefilter("%ssc -l %s" % (self.ESC_MAGIC,lrest[1:]),
                                       continuation)
            else:
                # $var=cmd <=> %sc var=cmd
                return self._prefilter("%ssc %s" % (self.ESC_MAGIC,lrest),
                                       continuation)
        else:
            return self._prefilter(line,continuation)
    else:
        return self._prefilter(line,continuation)

# Rebind this to be the new IPython prefilter:
from IPython.core.iplib import InteractiveShell
InteractiveShell.prefilter = prefilter_shell
# Clean up the namespace.
del InteractiveShell,prefilter_shell

# Provide pysh and further shell-oriented services
import os,sys,shutil
from IPython.utils.process import system,shell,getoutput,getoutputerror

# Short aliases for getting shell output as a string and a list
sout = getoutput
lout = lambda cmd: getoutput(cmd,split=1)

# Empty function, meant as a docstring holder so help(pysh) works.
def pysh():
    """Pysh is a set of modules and extensions to IPython which make shell-like
    usage with Python syntax more convenient.  Keep in mind that pysh is NOT a
    full-blown shell, so don't try to make it your /etc/passwd entry!

    In particular, it has no job control, so if you type Ctrl-Z (under Unix),
    you'll suspend pysh itself, not the process you just started.

    Since pysh is really nothing but a customized IPython, you should
    familiarize yourself with IPython's features.  This brief help mainly
    documents areas in which pysh differs from the normal IPython.

    ALIASES
    -------
    All of your $PATH has been loaded as IPython aliases, so you should be
    able to type any normal system command and have it executed.  See %alias?
    and %unalias? for details on the alias facilities.

    SPECIAL SYNTAX
    --------------
    Any lines which begin with '~', '/' and '.' will be executed as shell
    commands instead of as Python code. The special escapes below are also
    recognized.  !cmd is valid in single or multi-line input, all others are
    only valid in single-line input:

    !cmd      - pass 'cmd' directly to the shell
    !!cmd     - execute 'cmd' and return output as a list (split on '\\n')
    $var=cmd  - capture output of cmd into var, as a string
    $$var=cmd - capture output of cmd into var, as a list (split on '\\n')

    The $/$$ syntaxes make Python variables from system output, which you can
    later use for further scripting.  The converse is also possible: when
    executing an alias or calling to the system via !/!!, you can expand any
    python variable or expression by prepending it with $.  Full details of
    the allowed syntax can be found in Python's PEP 215.

    A few brief examples will illustrate these:

        fperez[~/test]|3> !ls *s.py
        scopes.py  strings.py

    ls is an internal alias, so there's no need to use !:
        fperez[~/test]|4> ls *s.py
        scopes.py*  strings.py

    !!ls will return the output into a Python variable:
        fperez[~/test]|5> !!ls *s.py
                      <5> ['scopes.py', 'strings.py']
        fperez[~/test]|6> print _5
        ['scopes.py', 'strings.py']

    $ and $$ allow direct capture to named variables:
        fperez[~/test]|7> $astr = ls *s.py
        fperez[~/test]|8> astr
                      <8> 'scopes.py\\nstrings.py'

        fperez[~/test]|9> $$alist = ls *s.py
        fperez[~/test]|10> alist
                      <10> ['scopes.py', 'strings.py']

    alist is now a normal python list you can loop over.  Using $ will expand
    back the python values when alias calls are made:
        fperez[~/test]|11> for f in alist:
                      |..>     print 'file',f,
                      |..>     wc -l $f
                      |..>
        file scopes.py     13 scopes.py
        file strings.py      4 strings.py

    Note that you may need to protect your variables with braces if you want
    to append strings to their names.  To copy all files in alist to .bak
    extensions, you must use:
        fperez[~/test]|12> for f in alist:
                      |..>     cp $f ${f}.bak

    If you try using $f.bak, you'll get an AttributeError exception saying
    that your string object doesn't have a .bak attribute.  This is because
    the $ expansion mechanism allows you to expand full Python expressions:
        fperez[~/test]|13> echo "sys.platform is: $sys.platform"
        sys.platform is: linux2

    IPython's input history handling is still active, which allows you to
    rerun a single block of multi-line input by simply using exec:
        fperez[~/test]|14> $$alist = ls *.eps
        fperez[~/test]|15> exec _i11
        file image2.eps    921 image2.eps
        file image.eps    921 image.eps

    While these are new special-case syntaxes, they are designed to allow very
    efficient use of the shell with minimal typing.  At an interactive shell
    prompt, conciseness of expression wins over readability.

    USEFUL FUNCTIONS AND MODULES
    ----------------------------
    The os, sys and shutil modules from the Python standard library are
    automatically loaded.  Some additional functions, useful for shell usage,
    are listed below.  You can request more help about them with '?'.

    shell   - execute a command in the underlying system shell
    system  - like shell(), but return the exit status of the command
    sout    - capture the output of a command as a string
    lout    - capture the output of a command as a list (split on '\\n')
    getoutputerror - capture (output,error) of a shell command

    sout/lout are the functional equivalents of $/$$.  They are provided to
    allow you to capture system output in the middle of true python code,
    function definitions, etc (where $ and $$ are invalid).

    DIRECTORY MANAGEMENT
    --------------------
    Since each command passed by pysh to the underlying system is executed in
    a subshell which exits immediately, you can NOT use !cd to navigate the
    filesystem.

    Pysh provides its own builtin '%cd' magic command to move in the
    filesystem (the % is not required with automagic on).  It also maintains a
    list of visited directories (use %dhist to see it) and allows direct
    switching to any of them.  Type 'cd?' for more details.

    %pushd, %popd and %dirs are provided for directory stack handling.

    PROMPT CUSTOMIZATION
    --------------------

    The supplied ipythonrc-pysh profile comes with an example of a very
    colored and detailed prompt, mainly to serve as an illustration.  The
    valid escape sequences, besides color names, are:

        \\#  - Prompt number.
        \\D  - Dots, as many as there are digits in \\# (so they align).
        \\w  - Current working directory (cwd).
        \\W  - Basename of current working directory.
        \\XN - Where N=0..5. N terms of the cwd, with $HOME written as ~.
        \\YN - Where N=0..5. Like XN, but if ~ is term N+1 it's also shown.
        \\u  - Username.
        \\H  - Full hostname.
        \\h  - Hostname up to first '.'
        \\$  - Root symbol ($ or #).
        \\t  - Current time, in H:M:S format.
        \\v  - IPython release version.
        \\n  - Newline.
        \\r  - Carriage return.
        \\\\ - An explicitly escaped '\\'.

    You can configure your prompt colors using any ANSI color escape.  Each
    color escape sets the color for any subsequent text, until another escape
    comes in and changes things.  The valid color escapes are:

        \\C_Black
        \\C_Blue
        \\C_Brown
        \\C_Cyan
        \\C_DarkGray
        \\C_Green
        \\C_LightBlue
        \\C_LightCyan
        \\C_LightGray
        \\C_LightGreen
        \\C_LightPurple
        \\C_LightRed
        \\C_Purple
        \\C_Red
        \\C_White
        \\C_Yellow
        \\C_Normal - Stop coloring, defaults to your terminal settings.
    """
    pass

# Configure a few things.  Much of this is fairly hackish, since IPython
# doesn't really expose a clean API for it.  Be careful if you start making
# many modifications here.


#  Set the 'cd' command to quiet mode, a more shell-like behavior
__IPYTHON__.default_option('cd','-q')

# This is redundant, ipy_user_conf.py will determine this
# Load all of $PATH as aliases
__IPYTHON__.magic_rehashx()

# Remove %sc,%sx if present as aliases
__IPYTHON__.magic_unalias('sc')
__IPYTHON__.magic_unalias('sx')

# We need different criteria for line-splitting, so that aliases such as
# 'gnome-terminal' are interpreted as a single alias instead of variable
# 'gnome' minus variable 'terminal'.
import re
__IPYTHON__.line_split = re.compile(r'^([\s*,;/])'
                                    r'([\?\w\.\-\+]+\w*\s*)'
                                    r'(\(?.*$)')

# Namespace cleanup
del re

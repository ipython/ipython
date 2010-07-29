# encoding: utf-8
"""
Utilities for working with external processes.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
import shlex
import subprocess

from IPython.utils.terminal import set_term_title

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class FindCmdError(Exception):
    pass


def _find_cmd(cmd):
    """Find the full path to a command using which."""
    return os.popen('which %s' % cmd).read().strip()


if os.name == 'posix':
    def _find_cmd(cmd):
        """Find the full path to a command using which."""
        return getoutputerror('/usr/bin/env which %s' % cmd)[0]


if sys.platform == 'win32':
    def _find_cmd(cmd):
        """Find the full path to a .bat or .exe using the win32api module."""
        try:
            from win32api import SearchPath
        except ImportError:
            raise ImportError('you need to have pywin32 installed for this to work')
        else:
            PATH = os.environ['PATH']
            extensions = ['.exe', '.com', '.bat', '.py']
            path = None
            for ext in extensions:
                try:
                    path = SearchPath(PATH,cmd + ext)[0]
                except:
                    pass
            if path is None:
                raise OSError("command %r not found" % cmd)
            else:
                return path


def find_cmd(cmd):
    """Find absolute path to executable cmd in a cross platform manner.
    
    This function tries to determine the full path to a command line program
    using `which` on Unix/Linux/OS X and `win32api` on Windows.  Most of the
    time it will use the version that is first on the users `PATH`.  If
    cmd is `python` return `sys.executable`.

    Warning, don't use this to find IPython command line programs as there
    is a risk you will find the wrong one.  Instead find those using the
    following code and looking for the application itself::
    
        from IPython.utils.path import get_ipython_module_path
        from IPython.utils.process import pycmd2argv
        argv = pycmd2argv(get_ipython_module_path('IPython.core.ipapp'))

    Parameters
    ----------
    cmd : str
        The command line program to look for.
    """
    if cmd == 'python':
        return os.path.abspath(sys.executable)
    try:
        path = _find_cmd(cmd)
    except OSError:
        raise FindCmdError('command could not be found: %s' % cmd)
    # which returns empty if not found
    if path == '':
        raise FindCmdError('command could not be found: %s' % cmd)
    return os.path.abspath(path)


def pycmd2argv(cmd):
    r"""Take the path of a python command and return a list (argv-style).

    This only works on Python based command line programs and will find the
    location of the ``python`` executable using ``sys.executable`` to make
    sure the right version is used.

    For a given path ``cmd``, this returns [cmd] if cmd's extension is .exe,
    .com or .bat, and [, cmd] otherwise.  

    Parameters
    ----------
    cmd : string
      The path of the command.

    Returns
    -------
    argv-style list.
    """
    ext = os.path.splitext(cmd)[1]
    if ext in ['.exe', '.com', '.bat']:
        return [cmd]
    else:
        if sys.platform == 'win32':
            # The -u option here turns on unbuffered output, which is required
            # on Win32 to prevent wierd conflict and problems with Twisted.
            # Also, use sys.executable to make sure we are picking up the 
            # right python exe.
            return [sys.executable, '-u', cmd]
        else:
            return [sys.executable, cmd]


def arg_split(s, posix=False):
    """Split a command line's arguments in a shell-like manner.

    This is a modified version of the standard library's shlex.split()
    function, but with a default of posix=False for splitting, so that quotes
    in inputs are respected."""

    # Unfortunately, python's shlex module is buggy with unicode input:
    # http://bugs.python.org/issue1170
    # At least encoding the input when it's unicode seems to help, but there
    # may be more problems lurking.  Apparently this is fixed in python3.
    if isinstance(s, unicode):
        s = s.encode(sys.stdin.encoding)
    lex = shlex.shlex(s, posix=posix)
    lex.whitespace_split = True
    return list(lex)


def system(cmd, verbose=0, debug=0, header=''):
    """Execute a system command, return its exit status.

    Options:

    - verbose (0): print the command to be executed.

    - debug (0): only print, do not actually execute.

    - header (''): Header to print on screen prior to the executed command (it
    is only prepended to the command, no newlines are added).

    Note: a stateful version of this function is available through the
    SystemExec class."""

    stat = 0
    if verbose or debug: print header+cmd
    sys.stdout.flush()
    if not debug: stat = os.system(cmd)
    return stat


def abbrev_cwd():
    """ Return abbreviated version of cwd, e.g. d:mydir """
    cwd = os.getcwd().replace('\\','/')
    drivepart = ''
    tail = cwd
    if sys.platform == 'win32':
        if len(cwd) < 4:
            return cwd
        drivepart,tail = os.path.splitdrive(cwd)


    parts = tail.split('/')
    if len(parts) > 2:
        tail = '/'.join(parts[-2:])

    return (drivepart + (
        cwd == '/' and '/' or tail))


# This function is used by ipython in a lot of places to make system calls.
# We need it to be slightly different under win32, due to the vagaries of
# 'network shares'.  A win32 override is below.

def shell(cmd, verbose=0, debug=0, header=''):
    """Execute a command in the system shell, always return None.

    Options:

    - verbose (0): print the command to be executed.

    - debug (0): only print, do not actually execute.

    - header (''): Header to print on screen prior to the executed command (it
    is only prepended to the command, no newlines are added).

    Note: this is similar to system(), but it returns None so it can
    be conveniently used in interactive loops without getting the return value
    (typically 0) printed many times."""

    stat = 0
    if verbose or debug: print header+cmd
    # flush stdout so we don't mangle python's buffering
    sys.stdout.flush()

    if not debug:
        set_term_title("IPy " + cmd)
        os.system(cmd)
        set_term_title("IPy " + abbrev_cwd())

# override shell() for win32 to deal with network shares
if os.name in ('nt','dos'):

    shell_ori = shell

    def shell(cmd, verbose=0, debug=0, header=''):
        if os.getcwd().startswith(r"\\"):
            path = os.getcwd()
            # change to c drive (cannot be on UNC-share when issuing os.system,
            # as cmd.exe cannot handle UNC addresses)
            os.chdir("c:")
            # issue pushd to the UNC-share and then run the command
            try:
                shell_ori('"pushd %s&&"'%path+cmd,verbose,debug,header)
            finally:
                os.chdir(path)
        else:
            shell_ori(cmd,verbose,debug,header)

    shell.__doc__ = shell_ori.__doc__

    
def getoutput(cmd, verbose=0, debug=0, header='', split=0):
    """Dummy substitute for perl's backquotes.

    Executes a command and returns the output.

    Accepts the same arguments as system(), plus:

    - split(0): if true, the output is returned as a list split on newlines.

    Note: a stateful version of this function is available through the
    SystemExec class.

    This is pretty much deprecated and rarely used, getoutputerror may be 
    what you need.

    """

    if verbose or debug: print header+cmd
    if not debug:
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout
        output = pipe.read()
        # stipping last \n is here for backwards compat.
        if output.endswith('\n'):
            output = output[:-1]
        if split:
            return output.split('\n')
        else:
            return output


# for compatibility with older naming conventions
xsys = system


def getoutputerror(cmd, verbose=0, debug=0, header='', split=0):
    """Return (standard output,standard error) of executing cmd in a shell.

    Accepts the same arguments as system(), plus:

    - split(0): if true, each of stdout/err is returned as a list split on
    newlines.

    Note: a stateful version of this function is available through the
    SystemExec class."""

    if verbose or debug: print header+cmd
    if not cmd:
        if split:
            return [],[]
        else:
            return '',''
    if not debug:
        p = subprocess.Popen(cmd, shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
        pin, pout, perr = (p.stdin, p.stdout, p.stderr)

        tout = pout.read().rstrip()
        terr = perr.read().rstrip()
        pin.close()
        pout.close()
        perr.close()
        if split:
            return tout.split('\n'),terr.split('\n')
        else:
            return tout,terr


class SystemExec:
    """Access the system and getoutput functions through a stateful interface.

    Note: here we refer to the system and getoutput functions from this
    library, not the ones from the standard python library.

    This class offers the system and getoutput functions as methods, but the
    verbose, debug and header parameters can be set for the instance (at
    creation time or later) so that they don't need to be specified on each
    call.

    For efficiency reasons, there's no way to override the parameters on a
    per-call basis other than by setting instance attributes. If you need
    local overrides, it's best to directly call system() or getoutput().

    The following names are provided as alternate options:
     - xsys: alias to system
     - bq: alias to getoutput

    An instance can then be created as:
    >>> sysexec = SystemExec(verbose=1,debug=0,header='Calling: ')
    """

    def __init__(self, verbose=0, debug=0, header='', split=0):
        """Specify the instance's values for verbose, debug and header."""
        self.verbose = verbose
        self.debug = debug
        self.header = header
        self.split = split

    def system(self, cmd):
        """Stateful interface to system(), with the same keyword parameters."""

        system(cmd, self.verbose, self.debug, self.header)

    def shell(self, cmd):
        """Stateful interface to shell(), with the same keyword parameters."""

        shell(cmd, self.verbose, self.debug, self.header)

    xsys = system  # alias

    def getoutput(self, cmd):
        """Stateful interface to getoutput()."""

        return getoutput(cmd, self.verbose, self.debug, self.header, self.split)

    def getoutputerror(self, cmd):
        """Stateful interface to getoutputerror()."""

        return getoutputerror(cmd, self.verbose, self.debug, self.header, self.split)

    bq = getoutput  # alias



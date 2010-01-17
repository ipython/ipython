# -*- coding: utf-8 -*-
"""General purpose utilities.

This is a grab-bag of stuff I find useful in most programs I write. Some of
these things are also convenient when working at the command line.
"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
from __future__ import absolute_import

#****************************************************************************
# required modules from the Python standard library
import __main__

import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
import types
import warnings

# Curses and termios are Unix-only modules
try:
    import curses
    # We need termios as well, so if its import happens to raise, we bail on
    # using curses altogether.
    import termios
except ImportError:
    USE_CURSES = False
else:
    # Curses on Solaris may not be complete, so we can't use it there
    USE_CURSES = hasattr(curses,'initscr')

# Other IPython utilities
import IPython
from IPython.core import release
from IPython.external.Itpl import itpl,printpl
from IPython.utils import platutils
from IPython.utils.generics import result_display
from IPython.external.path import path
from .baseutils import getoutputerror

#****************************************************************************
# Exceptions
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

#----------------------------------------------------------------------------
class IOStream:
    def __init__(self,stream,fallback):
        if not hasattr(stream,'write') or not hasattr(stream,'flush'):
            stream = fallback
        self.stream = stream
        self._swrite = stream.write
        self.flush = stream.flush

    def write(self,data):
        try:
            self._swrite(data)
        except:
            try:
                # print handles some unicode issues which may trip a plain
                # write() call.  Attempt to emulate write() by using a
                # trailing comma
                print >> self.stream, data,
            except:
                # if we get here, something is seriously broken.
                print >> sys.stderr, \
                      'ERROR - failed to write data to stream:', self.stream

    def writeln(self, data):
        self.write(data)
        self.write('\n')        
                
    def close(self):
        pass


class IOTerm:
    """ Term holds the file or file-like objects for handling I/O operations.

    These are normally just sys.stdin, sys.stdout and sys.stderr but for
    Windows they can can replaced to allow editing the strings before they are
    displayed."""

    # In the future, having IPython channel all its I/O operations through
    # this class will make it easier to embed it into other environments which
    # are not a normal terminal (such as a GUI-based shell)
    def __init__(self,cin=None,cout=None,cerr=None):
        self.cin  = IOStream(cin,sys.stdin)
        self.cout = IOStream(cout,sys.stdout)
        self.cerr = IOStream(cerr,sys.stderr)

# Global variable to be used for all I/O
Term = IOTerm()

import IPython.utils.rlineimpl as readline
# Remake Term to use the readline i/o facilities
if sys.platform == 'win32' and readline.have_readline:

    Term = IOTerm(cout=readline._outputfile,cerr=readline._outputfile)


class Tee(object):
    """A class to duplicate an output stream to stdout/err.

    This works in a manner very similar to the Unix 'tee' command.

    When the object is closed or deleted, it closes the original file given to
    it for duplication.
    """
    # Inspired by:
    # http://mail.python.org/pipermail/python-list/2007-May/442737.html

    def __init__(self, file, mode=None, channel='stdout'):
        """Construct a new Tee object.

        Parameters
        ----------
        file : filename or open filehandle (writable)
          File that will be duplicated

        mode : optional, valid mode for open().
          If a filename was give, open with this mode.

        channel : str, one of ['stdout', 'stderr']  
        """
        if channel not in ['stdout', 'stderr']:
            raise ValueError('Invalid channel spec %s' % channel)
        
        if hasattr(file, 'write') and hasattr(file, 'seek'):
            self.file = file
        else:
            self.file = open(name, mode)
        self.channel = channel
        self.ostream = getattr(sys, channel)
        setattr(sys, channel, self)
        self._closed = False

    def close(self):
        """Close the file and restore the channel."""
        self.flush()
        setattr(sys, self.channel, self.ostream)
        self.file.close()
        self._closed = True

    def write(self, data):
        """Write data to both channels."""
        self.file.write(data)
        self.ostream.write(data)
        self.ostream.flush()

    def flush(self):
        """Flush both channels."""
        self.file.flush()
        self.ostream.flush()

    def __del__(self):
        if not self._closed:
            self.close()
        

#****************************************************************************
# Generic warning/error printer, used by everything else
def warn(msg,level=2,exit_val=1):
    """Standard warning printer. Gives formatting consistency.

    Output is sent to Term.cerr (sys.stderr by default).

    Options:

    -level(2): allows finer control:
      0 -> Do nothing, dummy function.
      1 -> Print message.
      2 -> Print 'WARNING:' + message. (Default level).
      3 -> Print 'ERROR:' + message.
      4 -> Print 'FATAL ERROR:' + message and trigger a sys.exit(exit_val).

    -exit_val (1): exit value returned by sys.exit() for a level 4
    warning. Ignored for all other levels."""

    if level>0:
        header = ['','','WARNING: ','ERROR: ','FATAL ERROR: ']
        print >> Term.cerr, '%s%s' % (header[level],msg)
        if level == 4:
            print >> Term.cerr,'Exiting.\n'
            sys.exit(exit_val)

            
def info(msg):
    """Equivalent to warn(msg,level=1)."""

    warn(msg,level=1)

    
def error(msg):
    """Equivalent to warn(msg,level=3)."""

    warn(msg,level=3)

    
def fatal(msg,exit_val=1):
    """Equivalent to warn(msg,exit_val=exit_val,level=4)."""

    warn(msg,exit_val=exit_val,level=4)

def sys_info():
    """Return useful information about IPython and the system, as a string.

    Examples
    --------
    In [1]: print(sys_info())
    IPython version: 0.11.bzr.r1340   # random
    BZR revision   : 1340
    Platform info  : os.name -> posix, sys.platform -> linux2
                   : Linux-2.6.31-17-generic-i686-with-Ubuntu-9.10-karmic
    Python info    : 2.6.4 (r264:75706, Dec  7 2009, 18:45:15) 
    [GCC 4.4.1]
    """
    import platform
    out = []
    out.append('IPython version: %s' % release.version)
    out.append('BZR revision   : %s' % release.revision)
    out.append('Platform info  : os.name -> %s, sys.platform -> %s' %
               (os.name,sys.platform) )
    out.append('               : %s' % platform.platform())
    out.append('Python info    : %s' % sys.version)
    out.append('')  # ensure closing newline
    return '\n'.join(out)
    

#---------------------------------------------------------------------------
# Debugging routines
#
def debugx(expr,pre_msg=''):
    """Print the value of an expression from the caller's frame.

    Takes an expression, evaluates it in the caller's frame and prints both
    the given expression and the resulting value (as well as a debug mark
    indicating the name of the calling function.  The input must be of a form
    suitable for eval().

    An optional message can be passed, which will be prepended to the printed
    expr->value pair."""

    cf = sys._getframe(1)
    print '[DBG:%s] %s%s -> %r' % (cf.f_code.co_name,pre_msg,expr,
                                   eval(expr,cf.f_globals,cf.f_locals))

# deactivate it by uncommenting the following line, which makes it a no-op
#def debugx(expr,pre_msg=''): pass

#----------------------------------------------------------------------------
StringTypes = types.StringTypes

# Basic timing functionality

# If possible (Unix), use the resource module instead of time.clock()
try:
    import resource
    def clocku():
        """clocku() -> floating point number

        Return the *USER* CPU time in seconds since the start of the process.
        This is done via a call to resource.getrusage, so it avoids the
        wraparound problems in time.clock()."""

        return resource.getrusage(resource.RUSAGE_SELF)[0]

    def clocks():
        """clocks() -> floating point number

        Return the *SYSTEM* CPU time in seconds since the start of the process.
        This is done via a call to resource.getrusage, so it avoids the
        wraparound problems in time.clock()."""

        return resource.getrusage(resource.RUSAGE_SELF)[1]

    def clock():
        """clock() -> floating point number

        Return the *TOTAL USER+SYSTEM* CPU time in seconds since the start of
        the process.  This is done via a call to resource.getrusage, so it
        avoids the wraparound problems in time.clock()."""

        u,s = resource.getrusage(resource.RUSAGE_SELF)[:2]
        return u+s

    def clock2():
        """clock2() -> (t_user,t_system)

        Similar to clock(), but return a tuple of user/system times."""
        return resource.getrusage(resource.RUSAGE_SELF)[:2]

except ImportError:
    # There is no distinction of user/system time under windows, so we just use
    # time.clock() for everything...
    clocku = clocks = clock = time.clock
    def clock2():
        """Under windows, system CPU time can't be measured.

        This just returns clock() and zero."""
        return time.clock(),0.0

    
def timings_out(reps,func,*args,**kw):
    """timings_out(reps,func,*args,**kw) -> (t_total,t_per_call,output)

    Execute a function reps times, return a tuple with the elapsed total
    CPU time in seconds, the time per call and the function's output.

    Under Unix, the return value is the sum of user+system time consumed by
    the process, computed via the resource module.  This prevents problems
    related to the wraparound effect which the time.clock() function has.

    Under Windows the return value is in wall clock seconds. See the
    documentation for the time module for more details."""

    reps = int(reps)
    assert reps >=1, 'reps must be >= 1'
    if reps==1:
        start = clock()
        out = func(*args,**kw)
        tot_time = clock()-start
    else:
        rng = xrange(reps-1) # the last time is executed separately to store output
        start = clock()
        for dummy in rng: func(*args,**kw)
        out = func(*args,**kw)  # one last time
        tot_time = clock()-start
    av_time = tot_time / reps
    return tot_time,av_time,out


def timings(reps,func,*args,**kw):
    """timings(reps,func,*args,**kw) -> (t_total,t_per_call)

    Execute a function reps times, return a tuple with the elapsed total CPU
    time in seconds and the time per call. These are just the first two values
    in timings_out()."""

    return timings_out(reps,func,*args,**kw)[0:2]


def timing(func,*args,**kw):
    """timing(func,*args,**kw) -> t_total

    Execute a function once, return the elapsed total CPU time in
    seconds. This is just the first value in timings_out()."""

    return timings_out(1,func,*args,**kw)[0]

#****************************************************************************
# file and system

def arg_split(s,posix=False):
    """Split a command line's arguments in a shell-like manner.

    This is a modified version of the standard library's shlex.split()
    function, but with a default of posix=False for splitting, so that quotes
    in inputs are respected."""

    # XXX - there may be unicode-related problems here!!!  I'm not sure that
    # shlex is truly unicode-safe, so it might be necessary to do
    #
    # s = s.encode(sys.stdin.encoding)
    #
    # first, to ensure that shlex gets a normal string.  Input from anyone who
    # knows more about unicode and shlex than I would be good to have here...
    lex = shlex.shlex(s, posix=posix)
    lex.whitespace_split = True
    return list(lex)


def system(cmd,verbose=0,debug=0,header=''):
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

def shell(cmd,verbose=0,debug=0,header=''):
    """Execute a command in the system shell, always return None.

    Options:

    - verbose (0): print the command to be executed.

    - debug (0): only print, do not actually execute.

    - header (''): Header to print on screen prior to the executed command (it
    is only prepended to the command, no newlines are added).

    Note: this is similar to genutils.system(), but it returns None so it can
    be conveniently used in interactive loops without getting the return value
    (typically 0) printed many times."""

    stat = 0
    if verbose or debug: print header+cmd
    # flush stdout so we don't mangle python's buffering
    sys.stdout.flush()

    if not debug:
        platutils.set_term_title("IPy " + cmd)
        os.system(cmd)
        platutils.set_term_title("IPy " + abbrev_cwd())

# override shell() for win32 to deal with network shares
if os.name in ('nt','dos'):

    shell_ori = shell

    def shell(cmd,verbose=0,debug=0,header=''):
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

    
def getoutput(cmd,verbose=0,debug=0,header='',split=0):
    """Dummy substitute for perl's backquotes.

    Executes a command and returns the output.

    Accepts the same arguments as system(), plus:

    - split(0): if true, the output is returned as a list split on newlines.

    Note: a stateful version of this function is available through the
    SystemExec class.

    This is pretty much deprecated and rarely used,
    genutils.getoutputerror may be what you need.

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
bq = getoutput


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

    def __init__(self,verbose=0,debug=0,header='',split=0):
        """Specify the instance's values for verbose, debug and header."""
        setattr_list(self,'verbose debug header split')

    def system(self,cmd):
        """Stateful interface to system(), with the same keyword parameters."""

        system(cmd,self.verbose,self.debug,self.header)

    def shell(self,cmd):
        """Stateful interface to shell(), with the same keyword parameters."""

        shell(cmd,self.verbose,self.debug,self.header)

    xsys = system  # alias

    def getoutput(self,cmd):
        """Stateful interface to getoutput()."""

        return getoutput(cmd,self.verbose,self.debug,self.header,self.split)

    def getoutputerror(self,cmd):
        """Stateful interface to getoutputerror()."""

        return getoutputerror(cmd,self.verbose,self.debug,self.header,self.split)

    bq = getoutput  # alias

#-----------------------------------------------------------------------------
def mutex_opts(dict,ex_op):
    """Check for presence of mutually exclusive keys in a dict.

    Call: mutex_opts(dict,[[op1a,op1b],[op2a,op2b]...]"""
    for op1,op2 in ex_op:
        if op1 in dict and op2 in dict:
            raise ValueError,'\n*** ERROR in Arguments *** '\
                  'Options '+op1+' and '+op2+' are mutually exclusive.'

#-----------------------------------------------------------------------------
def get_py_filename(name):
    """Return a valid python filename in the current directory.

    If the given name is not a file, it adds '.py' and searches again.
    Raises IOError with an informative message if the file isn't found."""

    name = os.path.expanduser(name)
    if not os.path.isfile(name) and not name.endswith('.py'):
        name += '.py'
    if os.path.isfile(name):
        return name
    else:
        raise IOError,'File `%s` not found.' % name

#-----------------------------------------------------------------------------


def filefind(filename, path_dirs=None):
    """Find a file by looking through a sequence of paths.

    This iterates through a sequence of paths looking for a file and returns
    the full, absolute path of the first occurence of the file.  If no set of
    path dirs is given, the filename is tested as is, after running through
    :func:`expandvars` and :func:`expanduser`.  Thus a simple call::

        filefind('myfile.txt')

    will find the file in the current working dir, but::

        filefind('~/myfile.txt')

    Will find the file in the users home directory.  This function does not
    automatically try any paths, such as the cwd or the user's home directory.
    
    Parameters
    ----------
    filename : str
        The filename to look for.
    path_dirs : str, None or sequence of str
        The sequence of paths to look for the file in.  If None, the filename
        need to be absolute or be in the cwd.  If a string, the string is
        put into a sequence and the searched.  If a sequence, walk through
        each element and join with ``filename``, calling :func:`expandvars`
        and :func:`expanduser` before testing for existence.
        
    Returns
    -------
    Raises :exc:`IOError` or returns absolute path to file.
    """
    
    # If paths are quoted, abspath gets confused, strip them...
    filename = filename.strip('"').strip("'")
    # If the input is an absolute path, just check it exists
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename
        
    if path_dirs is None:
        path_dirs = ("",)
    elif isinstance(path_dirs, basestring):
        path_dirs = (path_dirs,)
        
    for path in path_dirs:
        if path == '.': path = os.getcwd()
        testname = expand_path(os.path.join(path, filename))
        if os.path.isfile(testname):
            return os.path.abspath(testname)
        
    raise IOError("File %r does not exist in any of the search paths: %r" % 
                  (filename, path_dirs) )


#----------------------------------------------------------------------------
def file_read(filename):
    """Read a file and close it.  Returns the file source."""
    fobj = open(filename,'r');
    source = fobj.read();
    fobj.close()
    return source

def file_readlines(filename):
    """Read a file and close it.  Returns the file source using readlines()."""
    fobj = open(filename,'r');
    lines = fobj.readlines();
    fobj.close()
    return lines

#----------------------------------------------------------------------------
def target_outdated(target,deps):
    """Determine whether a target is out of date.

    target_outdated(target,deps) -> 1/0

    deps: list of filenames which MUST exist.
    target: single filename which may or may not exist.

    If target doesn't exist or is older than any file listed in deps, return
    true, otherwise return false.
    """
    try:
        target_time = os.path.getmtime(target)
    except os.error:
        return 1
    for dep in deps:
        dep_time = os.path.getmtime(dep)
        if dep_time > target_time:
            #print "For target",target,"Dep failed:",dep # dbg
            #print "times (dep,tar):",dep_time,target_time # dbg
            return 1
    return 0

#-----------------------------------------------------------------------------
def target_update(target,deps,cmd):
    """Update a target with a given command given a list of dependencies.

    target_update(target,deps,cmd) -> runs cmd if target is outdated.

    This is just a wrapper around target_outdated() which calls the given
    command if target is outdated."""

    if target_outdated(target,deps):
        xsys(cmd)

#----------------------------------------------------------------------------
def unquote_ends(istr):
    """Remove a single pair of quotes from the endpoints of a string."""

    if not istr:
        return istr
    if (istr[0]=="'" and istr[-1]=="'") or \
       (istr[0]=='"' and istr[-1]=='"'):
        return istr[1:-1]
    else:
        return istr

#----------------------------------------------------------------------------
def flag_calls(func):
    """Wrap a function to detect and flag when it gets called.

    This is a decorator which takes a function and wraps it in a function with
    a 'called' attribute. wrapper.called is initialized to False.

    The wrapper.called attribute is set to False right before each call to the
    wrapped function, so if the call fails it remains False.  After the call
    completes, wrapper.called is set to True and the output is returned.

    Testing for truth in wrapper.called allows you to determine if a call to
    func() was attempted and succeeded."""

    def wrapper(*args,**kw):
        wrapper.called = False
        out = func(*args,**kw)
        wrapper.called = True
        return out

    wrapper.called = False
    wrapper.__doc__ = func.__doc__
    return wrapper

#----------------------------------------------------------------------------
def dhook_wrap(func,*a,**k):
    """Wrap a function call in a sys.displayhook controller.

    Returns a wrapper around func which calls func, with all its arguments and
    keywords unmodified, using the default sys.displayhook.  Since IPython
    modifies sys.displayhook, it breaks the behavior of certain systems that
    rely on the default behavior, notably doctest.
    """

    def f(*a,**k):

        dhook_s = sys.displayhook
        sys.displayhook = sys.__displayhook__
        try:
            out = func(*a,**k)
        finally:
            sys.displayhook = dhook_s

        return out

    f.__doc__ = func.__doc__
    return f

#----------------------------------------------------------------------------
def doctest_reload():
    """Properly reload doctest to reuse it interactively.

    This routine:

      - imports doctest but does NOT reload it (see below).

      - resets its global 'master' attribute to None, so that multiple uses of
      the module interactively don't produce cumulative reports.

      - Monkeypatches its core test runner method to protect it from IPython's
      modified displayhook.  Doctest expects the default displayhook behavior
      deep down, so our modification breaks it completely.  For this reason, a
      hard monkeypatch seems like a reasonable solution rather than asking
      users to manually use a different doctest runner when under IPython.

    Notes
    -----

    This function *used to* reload doctest, but this has been disabled because
    reloading doctest unconditionally can cause massive breakage of other
    doctest-dependent modules already in memory, such as those for IPython's
    own testing system.  The name wasn't changed to avoid breaking people's
    code, but the reload call isn't actually made anymore."""

    import doctest
    doctest.master = None
    doctest.DocTestRunner.run = dhook_wrap(doctest.DocTestRunner.run)

#----------------------------------------------------------------------------
class HomeDirError(Error):
    pass

def get_home_dir():
    """Return the closest possible equivalent to a 'home' directory.

    * On POSIX, we try $HOME.
    * On Windows we try:
      - %HOME%: rare, but some people with unix-like setups may have defined it
      - %HOMESHARE%
      - %HOMEDRIVE\%HOMEPATH%
      - %USERPROFILE%
      - Registry hack
    * On Dos C:\
 
    Currently only Posix and NT are implemented, a HomeDirError exception is
    raised for all other OSes.
    """

    isdir = os.path.isdir
    env = os.environ

    # first, check py2exe distribution root directory for _ipython.
    # This overrides all. Normally does not exist.

    if hasattr(sys, "frozen"): #Is frozen by py2exe
        if '\\library.zip\\' in IPython.__file__.lower():#libraries compressed to zip-file
            root, rest = IPython.__file__.lower().split('library.zip')
        else: 
            root=os.path.join(os.path.split(IPython.__file__)[0],"../../")
        root=os.path.abspath(root).rstrip('\\')
        if isdir(os.path.join(root, '_ipython')):
            os.environ["IPYKITROOT"] = root
        return root.decode(sys.getfilesystemencoding())

    if os.name == 'posix':
        # Linux, Unix, AIX, OS X
        try:
            homedir = env['HOME']
        except KeyError:
            raise HomeDirError('Undefined $HOME, IPython cannot proceed.')
        else:
            return homedir.decode(sys.getfilesystemencoding())
    elif os.name == 'nt':
        # Now for win9x, XP, Vista, 7?
        # For some strange reason all of these return 'nt' for os.name.
        # First look for a network home directory. This will return the UNC
        # path (\\server\\Users\%username%) not the mapped path (Z:\). This
        # is needed when running IPython on cluster where all paths have to 
        # be UNC.
        try:
            # A user with a lot of unix tools in win32 may have defined $HOME,
            # honor it if it exists, but otherwise let the more typical
            # %HOMESHARE% variable be used.
            homedir = env.get('HOME')
            if homedir is None:
                homedir = env['HOMESHARE']
        except KeyError:
            pass
        else:
            if isdir(homedir):
                return homedir.decode(sys.getfilesystemencoding())

        # Now look for a local home directory
        try:
            homedir = os.path.join(env['HOMEDRIVE'],env['HOMEPATH'])
        except KeyError:
            pass
        else:
            if isdir(homedir):
                return homedir.decode(sys.getfilesystemencoding())

        # Now the users profile directory
        try:
            homedir = os.path.join(env['USERPROFILE'])
        except KeyError:
            pass
        else:
            if isdir(homedir):
                return homedir.decode(sys.getfilesystemencoding())

        # Use the registry to get the 'My Documents' folder.
        try:
            import _winreg as wreg
            key = wreg.OpenKey(
                wreg.HKEY_CURRENT_USER,
                "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            homedir = wreg.QueryValueEx(key,'Personal')[0]
            key.Close()
        except:
            pass
        else:
            if isdir(homedir):
                return homedir.decode(sys.getfilesystemencoding())

        # If all else fails, raise HomeDirError
        raise HomeDirError('No valid home directory could be found')
    elif os.name == 'dos':
        # Desperate, may do absurd things in classic MacOS. May work under DOS.
        return 'C:\\'.decode(sys.getfilesystemencoding())
    else:
        raise HomeDirError('No valid home directory could be found for your OS')


def get_ipython_dir():
    """Get the IPython directory for this platform and user.
    
    This uses the logic in `get_home_dir` to find the home directory
    and the adds .ipython to the end of the path.
    """
    ipdir_def = '.ipython'
    home_dir = get_home_dir()
    #import pdb; pdb.set_trace()  # dbg
    ipdir = os.environ.get(
        'IPYTHON_DIR', os.environ.get(
            'IPYTHONDIR', os.path.join(home_dir, ipdir_def)
        )
    )
    return ipdir.decode(sys.getfilesystemencoding())


def get_ipython_package_dir():
    """Get the base directory where IPython itself is installed."""
    ipdir = os.path.dirname(IPython.__file__)
    return ipdir.decode(sys.getfilesystemencoding())


#****************************************************************************
# strings and text

class LSString(str):
    """String derivative with a special access attributes.

    These are normal strings, but with the special attributes:

        .l (or .list) : value as list (split on newlines).
        .n (or .nlstr): original value (the string itself).
        .s (or .spstr): value as whitespace-separated string.
        .p (or .paths): list of path objects

    Any values which require transformations are computed only once and
    cached.

    Such strings are very useful to efficiently interact with the shell, which
    typically only understands whitespace-separated options for commands."""

    def get_list(self):
        try:
            return self.__list
        except AttributeError:
            self.__list = self.split('\n')
            return self.__list

    l = list = property(get_list)

    def get_spstr(self):
        try:
            return self.__spstr
        except AttributeError:
            self.__spstr = self.replace('\n',' ')
            return self.__spstr

    s = spstr = property(get_spstr)

    def get_nlstr(self):
        return self

    n = nlstr = property(get_nlstr)

    def get_paths(self):
        try:
            return self.__paths
        except AttributeError:
            self.__paths = [path(p) for p in self.split('\n') if os.path.exists(p)]
            return self.__paths

    p = paths = property(get_paths)

def print_lsstring(arg):
    """ Prettier (non-repr-like) and more informative printer for LSString """
    print "LSString (.p, .n, .l, .s available). Value:"
    print arg

print_lsstring = result_display.when_type(LSString)(print_lsstring)

#----------------------------------------------------------------------------
class SList(list):
    """List derivative with a special access attributes.

    These are normal lists, but with the special attributes:

        .l (or .list) : value as list (the list itself).
        .n (or .nlstr): value as a string, joined on newlines.
        .s (or .spstr): value as a string, joined on spaces.
        .p (or .paths): list of path objects

    Any values which require transformations are computed only once and
    cached."""

    def get_list(self):
        return self

    l = list = property(get_list)

    def get_spstr(self):
        try:
            return self.__spstr
        except AttributeError:
            self.__spstr = ' '.join(self)
            return self.__spstr

    s = spstr = property(get_spstr)

    def get_nlstr(self):
        try:
            return self.__nlstr
        except AttributeError:
            self.__nlstr = '\n'.join(self)
            return self.__nlstr

    n = nlstr = property(get_nlstr)

    def get_paths(self):
        try:
            return self.__paths
        except AttributeError:
            self.__paths = [path(p) for p in self if os.path.exists(p)]
            return self.__paths

    p = paths = property(get_paths)

    def grep(self, pattern, prune = False, field = None):
        """ Return all strings matching 'pattern' (a regex or callable)

        This is case-insensitive. If prune is true, return all items
        NOT matching the pattern.

        If field is specified, the match must occur in the specified
        whitespace-separated field.

        Examples::

            a.grep( lambda x: x.startswith('C') )
            a.grep('Cha.*log', prune=1)
            a.grep('chm', field=-1)
        """

        def match_target(s):
            if field is None:
                return s
            parts = s.split()
            try:
                tgt = parts[field]
                return tgt
            except IndexError:
                return ""

        if isinstance(pattern, basestring):
            pred = lambda x : re.search(pattern, x, re.IGNORECASE)
        else:
            pred = pattern
        if not prune:
            return SList([el for el in self if pred(match_target(el))])
        else:
            return SList([el for el in self if not pred(match_target(el))])
    def fields(self, *fields):
        """ Collect whitespace-separated fields from string list

        Allows quick awk-like usage of string lists.

        Example data (in var a, created by 'a = !ls -l')::
            -rwxrwxrwx  1 ville None      18 Dec 14  2006 ChangeLog
            drwxrwxrwx+ 6 ville None       0 Oct 24 18:05 IPython

        a.fields(0) is ['-rwxrwxrwx', 'drwxrwxrwx+']
        a.fields(1,0) is ['1 -rwxrwxrwx', '6 drwxrwxrwx+']
        (note the joining by space).
        a.fields(-1) is ['ChangeLog', 'IPython']

        IndexErrors are ignored.

        Without args, fields() just split()'s the strings.
        """
        if len(fields) == 0:
            return [el.split() for el in self]

        res = SList()
        for el in [f.split() for f in self]:
            lineparts = []

            for fd in fields:
                try:
                    lineparts.append(el[fd])
                except IndexError:
                    pass
            if lineparts:
                res.append(" ".join(lineparts))

        return res
    def sort(self,field= None,  nums = False):
        """ sort by specified fields (see fields())

        Example::
            a.sort(1, nums = True)

        Sorts a by second field, in numerical order (so that 21 > 3)

        """

        #decorate, sort, undecorate
        if field is not None:
            dsu = [[SList([line]).fields(field),  line] for line in self]
        else:
            dsu = [[line,  line] for line in self]
        if nums:
            for i in range(len(dsu)):
                numstr = "".join([ch for ch in dsu[i][0] if ch.isdigit()])
                try:
                    n = int(numstr)
                except ValueError:
                    n = 0;
                dsu[i][0] = n


        dsu.sort()
        return SList([t[1] for t in dsu])

def print_slist(arg):
    """ Prettier (non-repr-like) and more informative printer for SList """
    print "SList (.p, .n, .l, .s, .grep(), .fields(), sort() available):"
    if hasattr(arg,  'hideonce') and arg.hideonce:
        arg.hideonce = False
        return

    nlprint(arg)

print_slist = result_display.when_type(SList)(print_slist)



#----------------------------------------------------------------------------
def esc_quotes(strng):
    """Return the input string with single and double quotes escaped out"""

    return strng.replace('"','\\"').replace("'","\\'")

#----------------------------------------------------------------------------
def make_quoted_expr(s):
    """Return string s in appropriate quotes, using raw string if possible.

    XXX - example removed because it caused encoding errors in documentation
    generation.  We need a new example that doesn't contain invalid chars.

    Note the use of raw string and padding at the end to allow trailing
    backslash.
    """

    tail = ''
    tailpadding = ''
    raw  = ''
    if "\\" in s:
        raw = 'r'
        if s.endswith('\\'):
            tail = '[:-1]'
            tailpadding = '_'
    if '"' not in s:
        quote = '"'
    elif "'" not in s:
        quote = "'"
    elif '"""' not in s and not s.endswith('"'):
        quote = '"""'
    elif "'''" not in s and not s.endswith("'"):
        quote = "'''"
    else:
        # give up, backslash-escaped string will do
        return '"%s"' % esc_quotes(s)
    res = raw + quote + s + tailpadding + quote + tail
    return res


#----------------------------------------------------------------------------
def raw_input_multi(header='', ps1='==> ', ps2='..> ',terminate_str = '.'):
    """Take multiple lines of input.

    A list with each line of input as a separate element is returned when a
    termination string is entered (defaults to a single '.'). Input can also
    terminate via EOF (^D in Unix, ^Z-RET in Windows).

    Lines of input which end in \\ are joined into single entries (and a
    secondary continuation prompt is issued as long as the user terminates
    lines with \\). This allows entering very long strings which are still
    meant to be treated as single entities.
    """

    try:
        if header:
            header += '\n'
        lines = [raw_input(header + ps1)]
    except EOFError:
        return []
    terminate = [terminate_str]
    try:
        while lines[-1:] != terminate:
            new_line = raw_input(ps1)
            while new_line.endswith('\\'):
                new_line = new_line[:-1] + raw_input(ps2)
            lines.append(new_line)

        return lines[:-1]  # don't return the termination command
    except EOFError:
        print
        return lines

#----------------------------------------------------------------------------
def raw_input_ext(prompt='',  ps2='... '):
    """Similar to raw_input(), but accepts extended lines if input ends with \\."""

    line = raw_input(prompt)
    while line.endswith('\\'):
        line = line[:-1] + raw_input(ps2)
    return line

#----------------------------------------------------------------------------
def ask_yes_no(prompt,default=None):
    """Asks a question and returns a boolean (y/n) answer.

    If default is given (one of 'y','n'), it is used if the user input is
    empty. Otherwise the question is repeated until an answer is given.

    An EOF is treated as the default answer.  If there is no default, an
    exception is raised to prevent infinite loops.

    Valid answers are: y/yes/n/no (match is not case sensitive)."""

    answers = {'y':True,'n':False,'yes':True,'no':False}
    ans = None
    while ans not in answers.keys():
        try:
            ans = raw_input(prompt+' ').lower()
            if not ans:  # response was an empty string
                ans = default
        except KeyboardInterrupt:
            pass
        except EOFError:
            if default in answers.keys():
                ans = default
                print
            else:
                raise

    return answers[ans]

#----------------------------------------------------------------------------
class EvalDict:
    """
    Emulate a dict which evaluates its contents in the caller's frame.

    Usage:
    >>> number = 19

    >>> text = "python"

    >>> print "%(text.capitalize())s %(number/9.0).1f rules!" % EvalDict()
    Python 2.1 rules!
    """

    # This version is due to sismex01@hebmex.com on c.l.py, and is basically a
    # modified (shorter) version of:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66018 by
    # Skip Montanaro (skip@pobox.com).

    def __getitem__(self, name):
        frame = sys._getframe(1)
        return eval(name, frame.f_globals, frame.f_locals)

EvalString = EvalDict  # for backwards compatibility
#----------------------------------------------------------------------------
def qw(words,flat=0,sep=None,maxsplit=-1):
    """Similar to Perl's qw() operator, but with some more options.

    qw(words,flat=0,sep=' ',maxsplit=-1) -> words.split(sep,maxsplit)

    words can also be a list itself, and with flat=1, the output will be
    recursively flattened.

    Examples:

    >>> qw('1 2')
    ['1', '2']

    >>> qw(['a b','1 2',['m n','p q']])
    [['a', 'b'], ['1', '2'], [['m', 'n'], ['p', 'q']]]

    >>> qw(['a b','1 2',['m n','p q']],flat=1)
    ['a', 'b', '1', '2', 'm', 'n', 'p', 'q']
    """

    if type(words) in StringTypes:
        return [word.strip() for word in words.split(sep,maxsplit)
                if word and not word.isspace() ]
    if flat:
        return flatten(map(qw,words,[1]*len(words)))
    return map(qw,words)

#----------------------------------------------------------------------------
def qwflat(words,sep=None,maxsplit=-1):
    """Calls qw(words) in flat mode. It's just a convenient shorthand."""
    return qw(words,1,sep,maxsplit)

#----------------------------------------------------------------------------
def qw_lol(indata):
    """qw_lol('a b') -> [['a','b']],
    otherwise it's just a call to qw().

    We need this to make sure the modules_some keys *always* end up as a
    list of lists."""

    if type(indata) in StringTypes:
        return [qw(indata)]
    else:
        return qw(indata)

#----------------------------------------------------------------------------
def grep(pat,list,case=1):
    """Simple minded grep-like function.
    grep(pat,list) returns occurrences of pat in list, None on failure.

    It only does simple string matching, with no support for regexps. Use the
    option case=0 for case-insensitive matching."""

    # This is pretty crude. At least it should implement copying only references
    # to the original data in case it's big. Now it copies the data for output.
    out=[]
    if case:
        for term in list:
            if term.find(pat)>-1: out.append(term)
    else:
        lpat=pat.lower()
        for term in list:
            if term.lower().find(lpat)>-1: out.append(term)

    if len(out): return out
    else: return None

#----------------------------------------------------------------------------
def dgrep(pat,*opts):
    """Return grep() on dir()+dir(__builtins__).

    A very common use of grep() when working interactively."""

    return grep(pat,dir(__main__)+dir(__main__.__builtins__),*opts)

#----------------------------------------------------------------------------
def idgrep(pat):
    """Case-insensitive dgrep()"""

    return dgrep(pat,0)

#----------------------------------------------------------------------------
def igrep(pat,list):
    """Synonym for case-insensitive grep."""

    return grep(pat,list,case=0)

#----------------------------------------------------------------------------
def indent(str,nspaces=4,ntabs=0):
    """Indent a string a given number of spaces or tabstops.

    indent(str,nspaces=4,ntabs=0) -> indent str by ntabs+nspaces.
    """
    if str is None:
        return
    ind = '\t'*ntabs+' '*nspaces
    outstr = '%s%s' % (ind,str.replace(os.linesep,os.linesep+ind))
    if outstr.endswith(os.linesep+ind):
        return outstr[:-len(ind)]
    else:
        return outstr

#-----------------------------------------------------------------------------
def native_line_ends(filename,backup=1):
    """Convert (in-place) a file to line-ends native to the current OS.

    If the optional backup argument is given as false, no backup of the
    original file is left.  """

    backup_suffixes = {'posix':'~','dos':'.bak','nt':'.bak','mac':'.bak'}

    bak_filename = filename + backup_suffixes[os.name]

    original = open(filename).read()
    shutil.copy2(filename,bak_filename)
    try:
        new = open(filename,'wb')
        new.write(os.linesep.join(original.splitlines()))
        new.write(os.linesep) # ALWAYS put an eol at the end of the file
        new.close()
    except:
        os.rename(bak_filename,filename)
    if not backup:
        try:
            os.remove(bak_filename)
        except:
            pass

#****************************************************************************
# lists, dicts and structures

def belong(candidates,checklist):
    """Check whether a list of items appear in a given list of options.

    Returns a list of 1 and 0, one for each candidate given."""

    return [x in checklist for x in candidates]

#----------------------------------------------------------------------------
def uniq_stable(elems):
    """uniq_stable(elems) -> list

    Return from an iterable, a list of all the unique elements in the input,
    but maintaining the order in which they first appear.

    A naive solution to this problem which just makes a dictionary with the
    elements as keys fails to respect the stability condition, since
    dictionaries are unsorted by nature.

    Note: All elements in the input must be valid dictionary keys for this
    routine to work, as it internally uses a dictionary for efficiency
    reasons."""

    unique = []
    unique_dict = {}
    for nn in elems:
        if nn not in unique_dict:
            unique.append(nn)
            unique_dict[nn] = None
    return unique

#----------------------------------------------------------------------------
class NLprinter:
    """Print an arbitrarily nested list, indicating index numbers.

    An instance of this class called nlprint is available and callable as a
    function.

    nlprint(list,indent=' ',sep=': ') -> prints indenting each level by 'indent'
    and using 'sep' to separate the index from the value. """

    def __init__(self):
        self.depth = 0

    def __call__(self,lst,pos='',**kw):
        """Prints the nested list numbering levels."""
        kw.setdefault('indent',' ')
        kw.setdefault('sep',': ')
        kw.setdefault('start',0)
        kw.setdefault('stop',len(lst))
        # we need to remove start and stop from kw so they don't propagate
        # into a recursive call for a nested list.
        start = kw['start']; del kw['start']
        stop = kw['stop']; del kw['stop']
        if self.depth == 0 and 'header' in kw.keys():
            print kw['header']

        for idx in range(start,stop):
            elem = lst[idx]
            if type(elem)==type([]):
                self.depth += 1
                self.__call__(elem,itpl('$pos$idx,'),**kw)
                self.depth -= 1
            else:
                printpl(kw['indent']*self.depth+'$pos$idx$kw["sep"]$elem')

nlprint = NLprinter()
#----------------------------------------------------------------------------
def all_belong(candidates,checklist):
    """Check whether a list of items ALL appear in a given list of options.

    Returns a single 1 or 0 value."""

    return 1-(0 in [x in checklist for x in candidates])

#----------------------------------------------------------------------------
def sort_compare(lst1,lst2,inplace = 1):
    """Sort and compare two lists.

    By default it does it in place, thus modifying the lists. Use inplace = 0
    to avoid that (at the cost of temporary copy creation)."""
    if not inplace:
        lst1 = lst1[:]
        lst2 = lst2[:]
    lst1.sort(); lst2.sort()
    return lst1 == lst2

#----------------------------------------------------------------------------
def list2dict(lst):
    """Takes a list of (key,value) pairs and turns it into a dict."""

    dic = {}
    for k,v in lst: dic[k] = v
    return dic

#----------------------------------------------------------------------------
def list2dict2(lst,default=''):
    """Takes a list and turns it into a dict.
    Much slower than list2dict, but more versatile. This version can take
    lists with sublists of arbitrary length (including sclars)."""

    dic = {}
    for elem in lst:
        if type(elem) in (types.ListType,types.TupleType):
            size = len(elem)
            if  size == 0:
                pass
            elif size == 1:
                dic[elem] = default
            else:
                k,v = elem[0], elem[1:]
                if len(v) == 1: v = v[0]
                dic[k] = v
        else:
            dic[elem] = default
    return dic

#----------------------------------------------------------------------------
def flatten(seq):
    """Flatten a list of lists (NOT recursive, only works for 2d lists)."""

    return [x for subseq in seq for x in subseq]

#----------------------------------------------------------------------------
def get_slice(seq,start=0,stop=None,step=1):
    """Get a slice of a sequence with variable step. Specify start,stop,step."""
    if stop == None:
        stop = len(seq)
    item = lambda i: seq[i]
    return map(item,xrange(start,stop,step))

#----------------------------------------------------------------------------
def chop(seq,size):
    """Chop a sequence into chunks of the given size."""
    chunk = lambda i: seq[i:i+size]
    return map(chunk,xrange(0,len(seq),size))

#----------------------------------------------------------------------------
# with is a keyword as of python 2.5, so this function is renamed to withobj
# from its old 'with' name.
def with_obj(object, **args):
    """Set multiple attributes for an object, similar to Pascal's with.

    Example:
    with_obj(jim,
             born = 1960,
             haircolour = 'Brown',
             eyecolour = 'Green')

    Credit: Greg Ewing, in
    http://mail.python.org/pipermail/python-list/2001-May/040703.html.

    NOTE: up until IPython 0.7.2, this was called simply 'with', but 'with'
    has become a keyword for Python 2.5, so we had to rename it."""

    object.__dict__.update(args)

#----------------------------------------------------------------------------
def setattr_list(obj,alist,nspace = None):
    """Set a list of attributes for an object taken from a namespace.

    setattr_list(obj,alist,nspace) -> sets in obj all the attributes listed in
    alist with their values taken from nspace, which must be a dict (something
    like locals() will often do) If nspace isn't given, locals() of the
    *caller* is used, so in most cases you can omit it.

    Note that alist can be given as a string, which will be automatically
    split into a list on whitespace. If given as a list, it must be a list of
    *strings* (the variable names themselves), not of variables."""

    # this grabs the local variables from the *previous* call frame -- that is
    # the locals from the function that called setattr_list().
    # - snipped from weave.inline()
    if nspace is None:
        call_frame = sys._getframe().f_back
        nspace = call_frame.f_locals

    if type(alist) in StringTypes:
        alist = alist.split()
    for attr in alist:
        val = eval(attr,nspace)
        setattr(obj,attr,val)

#----------------------------------------------------------------------------
def getattr_list(obj,alist,*args):
    """getattr_list(obj,alist[, default]) -> attribute list.

    Get a list of named attributes for an object. When a default argument is
    given, it is returned when the attribute doesn't exist; without it, an
    exception is raised in that case.

    Note that alist can be given as a string, which will be automatically
    split into a list on whitespace. If given as a list, it must be a list of
    *strings* (the variable names themselves), not of variables."""

    if type(alist) in StringTypes:
        alist = alist.split()
    if args:
        if len(args)==1:
            default = args[0]
            return map(lambda attr: getattr(obj,attr,default),alist)
        else:
            raise ValueError,'getattr_list() takes only one optional argument'
    else:
        return map(lambda attr: getattr(obj,attr),alist)

#----------------------------------------------------------------------------
def map_method(method,object_list,*argseq,**kw):
    """map_method(method,object_list,*args,**kw) -> list

    Return a list of the results of applying the methods to the items of the
    argument sequence(s).  If more than one sequence is given, the method is
    called with an argument list consisting of the corresponding item of each
    sequence. All sequences must be of the same length.

    Keyword arguments are passed verbatim to all objects called.

    This is Python code, so it's not nearly as fast as the builtin map()."""

    out_list = []
    idx = 0
    for object in object_list:
        try:
            handler = getattr(object, method)
        except AttributeError:
            out_list.append(None)
        else:
            if argseq:
                args = map(lambda lst:lst[idx],argseq)
                #print 'ob',object,'hand',handler,'ar',args # dbg
                out_list.append(handler(args,**kw))
            else:
                out_list.append(handler(**kw))
        idx += 1
    return out_list

#----------------------------------------------------------------------------
def get_class_members(cls):
    ret = dir(cls)
    if hasattr(cls,'__bases__'):
        for base in cls.__bases__:
            ret.extend(get_class_members(base))
    return ret

#----------------------------------------------------------------------------
def dir2(obj):
    """dir2(obj) -> list of strings

    Extended version of the Python builtin dir(), which does a few extra
    checks, and supports common objects with unusual internals that confuse
    dir(), such as Traits and PyCrust.

    This version is guaranteed to return only a list of true strings, whereas
    dir() returns anything that objects inject into themselves, even if they
    are later not really valid for attribute access (many extension libraries
    have such bugs).
    """

    # Start building the attribute list via dir(), and then complete it
    # with a few extra special-purpose calls.
    words = dir(obj)

    if hasattr(obj,'__class__'):
        words.append('__class__')
        words.extend(get_class_members(obj.__class__))
    #if '__base__' in words: 1/0

    # Some libraries (such as traits) may introduce duplicates, we want to
    # track and clean this up if it happens
    may_have_dupes = False

    # this is the 'dir' function for objects with Enthought's traits
    if hasattr(obj, 'trait_names'):
        try:
            words.extend(obj.trait_names())
            may_have_dupes = True
        except TypeError:
            # This will happen if `obj` is a class and not an instance.
            pass

    # Support for PyCrust-style _getAttributeNames magic method.
    if hasattr(obj, '_getAttributeNames'):
        try:
            words.extend(obj._getAttributeNames())
            may_have_dupes = True
        except TypeError:
            # `obj` is a class and not an instance.  Ignore
            # this error.
            pass

    if may_have_dupes:
        # eliminate possible duplicates, as some traits may also
        # appear as normal attributes in the dir() call.
        words = list(set(words))
        words.sort()

    # filter out non-string attributes which may be stuffed by dir() calls
    # and poor coding in third-party modules
    return [w for w in words if isinstance(w, basestring)]

#----------------------------------------------------------------------------
def import_fail_info(mod_name,fns=None):
    """Inform load failure for a module."""

    if fns == None:
        warn("Loading of %s failed.\n" % (mod_name,))
    else:
        warn("Loading of %s from %s failed.\n" % (fns,mod_name))

#----------------------------------------------------------------------------
# Proposed popitem() extension, written as a method


class NotGiven: pass

def popkey(dct,key,default=NotGiven):
    """Return dct[key] and delete dct[key].

    If default is given, return it if dct[key] doesn't exist, otherwise raise
    KeyError.  """

    try:
        val = dct[key]
    except KeyError:
        if default is NotGiven:
            raise
        else:
            return default
    else:
        del dct[key]
        return val

def wrap_deprecated(func, suggest = '<nothing>'):
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s, use %s instead" %
                      ( func.__name__, suggest),
                      category=DeprecationWarning,
                      stacklevel = 2)
        return func(*args, **kwargs)
    return newFunc


def _num_cpus_unix():
    """Return the number of active CPUs on a Unix system."""
    return os.sysconf("SC_NPROCESSORS_ONLN")


def _num_cpus_darwin():
    """Return the number of active CPUs on a Darwin system."""
    p = subprocess.Popen(['sysctl','-n','hw.ncpu'],stdout=subprocess.PIPE)
    return p.stdout.read()


def _num_cpus_windows():
    """Return the number of active CPUs on a Windows system."""
    return os.environ.get("NUMBER_OF_PROCESSORS")


def num_cpus():
   """Return the effective number of CPUs in the system as an integer.

   This cross-platform function makes an attempt at finding the total number of
   available CPUs in the system, as returned by various underlying system and
   python calls.

   If it can't find a sensible answer, it returns 1 (though an error *may* make
   it return a large positive number that's actually incorrect).
   """

   # Many thanks to the Parallel Python project (http://www.parallelpython.com)
   # for the names of the keys we needed to look up for this function.  This
   # code was inspired by their equivalent function.

   ncpufuncs = {'Linux':_num_cpus_unix,
                'Darwin':_num_cpus_darwin,
                'Windows':_num_cpus_windows,
                # On Vista, python < 2.5.2 has a bug and returns 'Microsoft'
                # See http://bugs.python.org/issue1082 for details.
                'Microsoft':_num_cpus_windows,
                }

   ncpufunc = ncpufuncs.get(platform.system(),
                            # default to unix version (Solaris, AIX, etc)
                            _num_cpus_unix)

   try:
       ncpus = max(1,int(ncpufunc()))
   except:
       ncpus = 1
   return ncpus

def extract_vars(*names,**kw):
    """Extract a set of variables by name from another frame.

    :Parameters:
      - `*names`: strings
        One or more variable names which will be extracted from the caller's
    frame.

    :Keywords:
      - `depth`: integer (0)
        How many frames in the stack to walk when looking for your variables.


    Examples:

        In [2]: def func(x):
           ...:     y = 1
           ...:     print extract_vars('x','y')
           ...:

        In [3]: func('hello')
        {'y': 1, 'x': 'hello'}
    """

    depth = kw.get('depth',0)
    
    callerNS = sys._getframe(depth+1).f_locals
    return dict((k,callerNS[k]) for k in names)
    

def extract_vars_above(*names):
    """Extract a set of variables by name from another frame.

    Similar to extractVars(), but with a specified depth of 1, so that names
    are exctracted exactly from above the caller.

    This is simply a convenience function so that the very common case (for us)
    of skipping exactly 1 frame doesn't have to construct a special dict for
    keyword passing."""

    callerNS = sys._getframe(2).f_locals
    return dict((k,callerNS[k]) for k in names)

def expand_path(s):
    """Expand $VARS and ~names in a string, like a shell

    :Examples:
    
       In [2]: os.environ['FOO']='test'

       In [3]: expand_path('variable FOO is $FOO')
       Out[3]: 'variable FOO is test'
    """
    # This is a pretty subtle hack. When expand user is given a UNC path
    # on Windows (\\server\share$\%username%), os.path.expandvars, removes
    # the $ to get (\\server\share\%username%). I think it considered $
    # alone an empty var. But, we need the $ to remains there (it indicates
    # a hidden share).
    if os.name=='nt':
        s = s.replace('$\\', 'IPYTHON_TEMP')
    s = os.path.expandvars(os.path.expanduser(s))
    if os.name=='nt':
        s = s.replace('IPYTHON_TEMP', '$\\')
    return s

def list_strings(arg):
    """Always return a list of strings, given a string or list of strings
    as input.

    :Examples:

        In [7]: list_strings('A single string')
        Out[7]: ['A single string']

        In [8]: list_strings(['A single string in a list'])
        Out[8]: ['A single string in a list']

        In [9]: list_strings(['A','list','of','strings'])
        Out[9]: ['A', 'list', 'of', 'strings']
    """

    if isinstance(arg,basestring): return [arg]
    else: return arg


#----------------------------------------------------------------------------
def marquee(txt='',width=78,mark='*'):
    """Return the input string centered in a 'marquee'.

    :Examples:

        In [16]: marquee('A test',40)
        Out[16]: '**************** A test ****************'

        In [17]: marquee('A test',40,'-')
        Out[17]: '---------------- A test ----------------'

        In [18]: marquee('A test',40,' ')
        Out[18]: '                 A test                 '

    """
    if not txt:
        return (mark*width)[:width]
    nmark = (width-len(txt)-2)/len(mark)/2
    if nmark < 0: nmark =0
    marks = mark*nmark
    return '%s %s %s' % (marks,txt,marks)

#*************************** end of file <genutils.py> **********************

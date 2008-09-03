# -*- coding: utf-8 -*-
"""
General purpose utilities.

This is a grab-bag of stuff I find useful in most programs I write. Some of
these things are also convenient when working at the command line.

$Id: genutils.py 2998 2008-01-31 10:06:04Z vivainio $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

#****************************************************************************
# required modules from the Python standard library
import __main__
import commands
try:
    import doctest
except ImportError:
    pass
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
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
from IPython.Itpl import Itpl,itpl,printpl
from IPython import DPyGetOpt, platutils
from IPython.generics import result_display
import IPython.ipapi
from IPython.external.path import path
if os.name == "nt":
    from IPython.winconsole import get_console_size

try:
    set
except:
    from sets import Set as set


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

import IPython.rlineimpl as readline
# Remake Term to use the readline i/o facilities
if sys.platform == 'win32' and readline.have_readline:

    Term = IOTerm(cout=readline._outputfile,cerr=readline._outputfile)


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
        output = os.popen(cmd).read()
        # stipping last \n is here for backwards compat.
        if output.endswith('\n'):
            output = output[:-1]
        if split:
            return output.split('\n')
        else:
            return output

def getoutputerror(cmd,verbose=0,debug=0,header='',split=0):
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
        pin,pout,perr = os.popen3(cmd)
        tout = pout.read().rstrip()
        terr = perr.read().rstrip()
        pin.close()
        pout.close()
        perr.close()
        if split:
            return tout.split('\n'),terr.split('\n')
        else:
            return tout,terr

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
def filefind(fname,alt_dirs = None):
    """Return the given filename either in the current directory, if it
    exists, or in a specified list of directories.

    ~ expansion is done on all file and directory names.

    Upon an unsuccessful search, raise an IOError exception."""

    if alt_dirs is None:
        try:
            alt_dirs = get_home_dir()
        except HomeDirError:
            alt_dirs = os.getcwd()
    search = [fname] + list_strings(alt_dirs)
    search = map(os.path.expanduser,search)
    #print 'search list for',fname,'list:',search  # dbg
    fname = search[0]
    if os.path.isfile(fname):
        return fname
    for direc in search[1:]:
        testname = os.path.join(direc,fname)
        #print 'testname',testname  # dbg
        if os.path.isfile(testname):
            return testname
    raise IOError,'File' + `fname` + \
          ' not found in current or supplied directories:' + `alt_dirs`

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
def process_cmdline(argv,names=[],defaults={},usage=''):
    """ Process command-line options and arguments.

    Arguments:

    - argv: list of arguments, typically sys.argv.

    - names: list of option names. See DPyGetOpt docs for details on options
    syntax.

    - defaults: dict of default values.

    - usage: optional usage notice to print if a wrong argument is passed.

    Return a dict of options and a list of free arguments."""

    getopt = DPyGetOpt.DPyGetOpt()
    getopt.setIgnoreCase(0)
    getopt.parseConfiguration(names)

    try:
        getopt.processArguments(argv)
    except DPyGetOpt.ArgumentError, exc:
        print usage
        warn('"%s"' % exc,level=4)

    defaults.update(getopt.optionValues)
    args = getopt.freeValues

    return defaults,args

#----------------------------------------------------------------------------
def optstr2types(ostr):
    """Convert a string of option names to a dict of type mappings.

    optstr2types(str) -> {None:'string_opts',int:'int_opts',float:'float_opts'}

    This is used to get the types of all the options in a string formatted
    with the conventions of DPyGetOpt. The 'type' None is used for options
    which are strings (they need no further conversion). This function's main
    use is to get a typemap for use with read_dict().
    """

    typeconv = {None:'',int:'',float:''}
    typemap = {'s':None,'i':int,'f':float}
    opt_re = re.compile(r'([\w]*)([^:=]*:?=?)([sif]?)')

    for w in ostr.split():
        oname,alias,otype = opt_re.match(w).groups()
        if otype == '' or alias == '!':   # simple switches are integers too
            otype = 'i'
        typeconv[typemap[otype]] += oname + ' '
    return typeconv

#----------------------------------------------------------------------------
def read_dict(filename,type_conv=None,**opt):
    r"""Read a dictionary of key=value pairs from an input file, optionally
    performing conversions on the resulting values.

    read_dict(filename,type_conv,**opt) -> dict

    Only one value per line is accepted, the format should be
     # optional comments are ignored
     key value\n

    Args:

      - type_conv: A dictionary specifying which keys need to be converted to
      which types. By default all keys are read as strings. This dictionary
      should have as its keys valid conversion functions for strings
      (int,long,float,complex, or your own).  The value for each key
      (converter) should be a whitespace separated string containing the names
      of all the entries in the file to be converted using that function. For
      keys to be left alone, use None as the conversion function (only needed
      with purge=1, see below).

      - opt: dictionary with extra options as below (default in parens)

        purge(0): if set to 1, all keys *not* listed in type_conv are purged out
        of the dictionary to be returned. If purge is going to be used, the
        set of keys to be left as strings also has to be explicitly specified
        using the (non-existent) conversion function None.

        fs(None): field separator. This is the key/value separator to be used
        when parsing the file. The None default means any whitespace [behavior
        of string.split()].

        strip(0): if 1, strip string values of leading/trailinig whitespace.

        warn(1): warning level if requested keys are not found in file.
          - 0: silently ignore.
          - 1: inform but proceed.
          - 2: raise KeyError exception.

        no_empty(0): if 1, remove keys with whitespace strings as a value.

        unique([]): list of keys (or space separated string) which can't be
        repeated. If one such key is found in the file, each new instance
        overwrites the previous one. For keys not listed here, the behavior is
        to make a list of all appearances.

    Example:

    If the input file test.ini contains (we put it in a string to keep the test
    self-contained):

    >>> test_ini = '''\
    ... i 3
    ... x 4.5
    ... y 5.5
    ... s hi ho'''

    Then we can use it as follows:
    >>> type_conv={int:'i',float:'x',None:'s'}

    >>> d = read_dict(test_ini)

    >>> sorted(d.items())
    [('i', '3'), ('s', 'hi ho'), ('x', '4.5'), ('y', '5.5')]

    >>> d = read_dict(test_ini,type_conv)

    >>> sorted(d.items())
    [('i', 3), ('s', 'hi ho'), ('x', 4.5), ('y', '5.5')]

    >>> d = read_dict(test_ini,type_conv,purge=True)

    >>> sorted(d.items())
    [('i', 3), ('s', 'hi ho'), ('x', 4.5)]
    """

    # starting config
    opt.setdefault('purge',0)
    opt.setdefault('fs',None)  # field sep defaults to any whitespace
    opt.setdefault('strip',0)
    opt.setdefault('warn',1)
    opt.setdefault('no_empty',0)
    opt.setdefault('unique','')
    if type(opt['unique']) in StringTypes:
        unique_keys = qw(opt['unique'])
    elif type(opt['unique']) in (types.TupleType,types.ListType):
        unique_keys = opt['unique']
    else:
        raise ValueError, 'Unique keys must be given as a string, List or Tuple'

    dict = {}

    # first read in table of values as strings
    if '\n' in filename:
        lines = filename.splitlines()
        file = None
    else:
        file = open(filename,'r')
        lines = file.readlines()
    for line in lines:
        line = line.strip()
        if len(line) and line[0]=='#': continue
        if len(line)>0:
            lsplit = line.split(opt['fs'],1)
            try:
                key,val = lsplit
            except ValueError:
                key,val = lsplit[0],''
            key = key.strip()
            if opt['strip']: val = val.strip()
            if val == "''" or val == '""': val = ''
            if opt['no_empty'] and (val=='' or val.isspace()):
                continue
            # if a key is found more than once in the file, build a list
            # unless it's in the 'unique' list. In that case, last found in file
            # takes precedence. User beware.
            try:
                if dict[key] and key in unique_keys:
                    dict[key] = val
                elif type(dict[key]) is types.ListType:
                    dict[key].append(val)
                else:
                    dict[key] = [dict[key],val]
            except KeyError:
                dict[key] = val
    # purge if requested
    if opt['purge']:
        accepted_keys = qwflat(type_conv.values())
        for key in dict.keys():
            if key in accepted_keys: continue
            del(dict[key])
    # now convert if requested
    if type_conv==None: return dict
    conversions = type_conv.keys()
    try: conversions.remove(None)
    except: pass
    for convert in conversions:
        for val in qw(type_conv[convert]):
            try:
                dict[val] = convert(dict[val])
            except KeyError,e:
                if opt['warn'] == 0:
                    pass
                elif opt['warn'] == 1:
                    print >>sys.stderr, 'Warning: key',val,\
                          'not found in file',filename
                elif opt['warn'] == 2:
                    raise KeyError,e
                else:
                    raise ValueError,'Warning level must be 0,1 or 2'

    return dict

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

      - reloads doctest

      - resets its global 'master' attribute to None, so that multiple uses of
      the module interactively don't produce cumulative reports.

      - Monkeypatches its core test runner method to protect it from IPython's
      modified displayhook.  Doctest expects the default displayhook behavior
      deep down, so our modification breaks it completely.  For this reason, a
      hard monkeypatch seems like a reasonable solution rather than asking
      users to manually use a different doctest runner when under IPython."""

    import doctest
    reload(doctest)
    doctest.master=None

    try:
        doctest.DocTestRunner
    except AttributeError:
        # This is only for python 2.3 compatibility, remove once we move to
        # 2.4 only.
        pass
    else:
        doctest.DocTestRunner.run = dhook_wrap(doctest.DocTestRunner.run)

#----------------------------------------------------------------------------
class HomeDirError(Error):
    pass

def get_home_dir():
    """Return the closest possible equivalent to a 'home' directory.

    We first try $HOME.  Absent that, on NT it's $HOMEDRIVE\$HOMEPATH.

    Currently only Posix and NT are implemented, a HomeDirError exception is
    raised for all other OSes. """

    isdir = os.path.isdir
    env = os.environ

    # first, check py2exe distribution root directory for _ipython.
    # This overrides all. Normally does not exist.

    if '\\library.zip\\' in IPython.__file__.lower():
        root, rest = IPython.__file__.lower().split('library.zip')
        if isdir(root + '_ipython'):
            os.environ["IPYKITROOT"] = root.rstrip('\\')
            return root

    try:
        homedir = env['HOME']
        if not isdir(homedir):
            # in case a user stuck some string which does NOT resolve to a
            # valid path, it's as good as if we hadn't foud it
            raise KeyError
        return homedir
    except KeyError:
        if os.name == 'posix':
            raise HomeDirError,'undefined $HOME, IPython can not proceed.'
        elif os.name == 'nt':
            # For some strange reason, win9x returns 'nt' for os.name.
            try:
                homedir = os.path.join(env['HOMEDRIVE'],env['HOMEPATH'])
                if not isdir(homedir):
                    homedir = os.path.join(env['USERPROFILE'])
                    if not isdir(homedir):
                        raise HomeDirError
                return homedir
            except:
                try:
                    # Use the registry to get the 'My Documents' folder.
                    import _winreg as wreg
                    key = wreg.OpenKey(wreg.HKEY_CURRENT_USER,
                                       "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                    homedir = wreg.QueryValueEx(key,'Personal')[0]
                    key.Close()
                    if not isdir(homedir):
                        e = ('Invalid "Personal" folder registry key '
                             'typically "My Documents".\n'
                             'Value: %s\n'
                             'This is not a valid directory on your system.' %
                             homedir)
                        raise HomeDirError(e)
                    return homedir
                except HomeDirError:
                    raise
                except:
                    return 'C:\\'
        elif os.name == 'dos':
            # Desperate, may do absurd things in classic MacOS. May work under DOS.
            return 'C:\\'
        else:
            raise HomeDirError,'support for your operating system not implemented.'


def get_ipython_dir():
    """Get the IPython directory for this platform and user.
    
    This uses the logic in `get_home_dir` to find the home directory
    and the adds either .ipython or _ipython to the end of the path.
    """
    if os.name == 'posix':
         ipdir_def = '.ipython'
    else:
         ipdir_def = '_ipython'
    home_dir = get_home_dir()
    ipdir = os.path.abspath(os.environ.get('IPYTHONDIR',
                                           os.path.join(home_dir,ipdir_def)))
    return ipdir

def get_security_dir():
    """Get the IPython security directory.
    
    This directory is the default location for all security related files,
    including SSL/TLS certificates and FURL files.
    
    If the directory does not exist, it is created with 0700 permissions.
    If it exists, permissions are set to 0700.
    """
    security_dir = os.path.join(get_ipython_dir(), 'security')
    if not os.path.isdir(security_dir):
        os.mkdir(security_dir, 0700)
    else:
        os.chmod(security_dir, 0700)
    return security_dir
        
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

    Effectively this turns string: cd \ao\ao\
    to: r"cd \ao\ao\_"[:-1]

    Note the use of raw string and padding at the end to allow trailing backslash.

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
def marquee(txt='',width=78,mark='*'):
    """Return the input string centered in a 'marquee'."""
    if not txt:
        return (mark*width)[:width]
    nmark = (width-len(txt)-2)/len(mark)/2
    if nmark < 0: nmark =0
    marks = mark*nmark
    return '%s %s %s' % (marks,txt,marks)

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

#-----------------------------------------------------------------------------
def list_strings(arg):
    """Always return a list of strings, given a string or list of strings
    as input."""

    if type(arg) in StringTypes: return [arg]
    else: return arg

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

#----------------------------------------------------------------------------
def get_pager_cmd(pager_cmd = None):
    """Return a pager command.

    Makes some attempts at finding an OS-correct one."""

    if os.name == 'posix':
        default_pager_cmd = 'less -r'  # -r for color control sequences
    elif os.name in ['nt','dos']:
        default_pager_cmd = 'type'

    if pager_cmd is None:
        try:
            pager_cmd = os.environ['PAGER']
        except:
            pager_cmd = default_pager_cmd
    return pager_cmd

#-----------------------------------------------------------------------------
def get_pager_start(pager,start):
    """Return the string for paging files with an offset.

    This is the '+N' argument which less and more (under Unix) accept.
    """

    if pager in ['less','more']:
        if start:
            start_string = '+' + str(start)
        else:
            start_string = ''
    else:
        start_string = ''
    return start_string

#----------------------------------------------------------------------------
# (X)emacs on W32 doesn't like to be bypassed with msvcrt.getch()
if os.name == 'nt' and os.environ.get('TERM','dumb') != 'emacs':
    import msvcrt
    def page_more():
        """ Smart pausing between pages

        @return:    True if need print more lines, False if quit
        """
        Term.cout.write('---Return to continue, q to quit--- ')
        ans = msvcrt.getch()
        if ans in ("q", "Q"):
            result = False
        else:
            result = True
        Term.cout.write("\b"*37 + " "*37 + "\b"*37)
        return result
else:
    def page_more():
        ans = raw_input('---Return to continue, q to quit--- ')
        if ans.lower().startswith('q'):
            return False
        else:
            return True

esc_re = re.compile(r"(\x1b[^m]+m)")

def page_dumb(strng,start=0,screen_lines=25):
    """Very dumb 'pager' in Python, for when nothing else works.

    Only moves forward, same interface as page(), except for pager_cmd and
    mode."""

    out_ln  = strng.splitlines()[start:]
    screens = chop(out_ln,screen_lines-1)
    if len(screens) == 1:
        print >>Term.cout, os.linesep.join(screens[0])
    else:
        last_escape = ""
        for scr in screens[0:-1]:
            hunk = os.linesep.join(scr)
            print >>Term.cout, last_escape + hunk
            if not page_more():
                return
            esc_list = esc_re.findall(hunk)
            if len(esc_list) > 0:
                last_escape = esc_list[-1]
        print >>Term.cout, last_escape + os.linesep.join(screens[-1])

#----------------------------------------------------------------------------
def page(strng,start=0,screen_lines=0,pager_cmd = None):
    """Print a string, piping through a pager after a certain length.

    The screen_lines parameter specifies the number of *usable* lines of your
    terminal screen (total lines minus lines you need to reserve to show other
    information).

    If you set screen_lines to a number <=0, page() will try to auto-determine
    your screen size and will only use up to (screen_size+screen_lines) for
    printing, paging after that. That is, if you want auto-detection but need
    to reserve the bottom 3 lines of the screen, use screen_lines = -3, and for
    auto-detection without any lines reserved simply use screen_lines = 0.

    If a string won't fit in the allowed lines, it is sent through the
    specified pager command. If none given, look for PAGER in the environment,
    and ultimately default to less.

    If no system pager works, the string is sent through a 'dumb pager'
    written in python, very simplistic.
    """

    # Some routines may auto-compute start offsets incorrectly and pass a
    # negative value.  Offset to 0 for robustness.
    start = max(0,start)

    # first, try the hook
    ip = IPython.ipapi.get()
    if ip:
        try:
            ip.IP.hooks.show_in_pager(strng)
            return
        except IPython.ipapi.TryNext:
            pass

    # Ugly kludge, but calling curses.initscr() flat out crashes in emacs
    TERM = os.environ.get('TERM','dumb')
    if TERM in ['dumb','emacs'] and os.name != 'nt':
        print strng
        return
    # chop off the topmost part of the string we don't want to see
    str_lines = strng.split(os.linesep)[start:]
    str_toprint = os.linesep.join(str_lines)
    num_newlines = len(str_lines)
    len_str = len(str_toprint)

    # Dumb heuristics to guesstimate number of on-screen lines the string
    # takes.  Very basic, but good enough for docstrings in reasonable
    # terminals. If someone later feels like refining it, it's not hard.
    numlines = max(num_newlines,int(len_str/80)+1)

    if os.name == "nt":
        screen_lines_def = get_console_size(defaulty=25)[1]
    else:
        screen_lines_def = 25 # default value if we can't auto-determine

    # auto-determine screen size
    if screen_lines <= 0:
        if TERM=='xterm':
            use_curses = USE_CURSES
        else:
            # curses causes problems on many terminals other than xterm.
            use_curses = False
        if use_curses:
            # There is a bug in curses, where *sometimes* it fails to properly
            # initialize, and then after the endwin() call is made, the
            # terminal is left in an unusable state.  Rather than trying to
            # check everytime for this (by requesting and comparing termios
            # flags each time), we just save the initial terminal state and
            # unconditionally reset it every time.  It's cheaper than making
            # the checks.
            term_flags = termios.tcgetattr(sys.stdout)
            scr = curses.initscr()
            screen_lines_real,screen_cols = scr.getmaxyx()
            curses.endwin()
            # Restore terminal state in case endwin() didn't.
            termios.tcsetattr(sys.stdout,termios.TCSANOW,term_flags)
            # Now we have what we needed: the screen size in rows/columns
            screen_lines += screen_lines_real
            #print '***Screen size:',screen_lines_real,'lines x',\
            #screen_cols,'columns.' # dbg
        else:
            screen_lines += screen_lines_def

    #print 'numlines',numlines,'screenlines',screen_lines  # dbg
    if numlines <= screen_lines :
        #print '*** normal print'  # dbg
        print >>Term.cout, str_toprint
    else:
        # Try to open pager and default to internal one if that fails.
        # All failure modes are tagged as 'retval=1', to match the return
        # value of a failed system command.  If any intermediate attempt
        # sets retval to 1, at the end we resort to our own page_dumb() pager.
        pager_cmd = get_pager_cmd(pager_cmd)
        pager_cmd += ' ' + get_pager_start(pager_cmd,start)
        if os.name == 'nt':
            if pager_cmd.startswith('type'):
                # The default WinXP 'type' command is failing on complex strings.
                retval = 1
            else:
                tmpname = tempfile.mktemp('.txt')
                tmpfile = file(tmpname,'wt')
                tmpfile.write(strng)
                tmpfile.close()
                cmd = "%s < %s" % (pager_cmd,tmpname)
                if os.system(cmd):
                  retval = 1
                else:
                  retval = None
                os.remove(tmpname)
        else:
            try:
                retval = None
                # if I use popen4, things hang. No idea why.
                #pager,shell_out = os.popen4(pager_cmd)
                pager = os.popen(pager_cmd,'w')
                pager.write(strng)
                pager.close()
                retval = pager.close()  # success returns None
            except IOError,msg:  # broken pipe when user quits
                if msg.args == (32,'Broken pipe'):
                    retval = None
                else:
                    retval = 1
            except OSError:
                # Other strange problems, sometimes seen in Win2k/cygwin
                retval = 1
        if retval is not None:
            page_dumb(strng,screen_lines=screen_lines)

#----------------------------------------------------------------------------
def page_file(fname,start = 0, pager_cmd = None):
    """Page a file, using an optional pager command and starting line.
    """

    pager_cmd = get_pager_cmd(pager_cmd)
    pager_cmd += ' ' + get_pager_start(pager_cmd,start)

    try:
        if os.environ['TERM'] in ['emacs','dumb']:
            raise EnvironmentError
        xsys(pager_cmd + ' ' + fname)
    except:
        try:
            if start > 0:
                start -= 1
            page(open(fname).read(),start)
        except:
            print 'Unable to show file',`fname`


#----------------------------------------------------------------------------
def snip_print(str,width = 75,print_full = 0,header = ''):
    """Print a string snipping the midsection to fit in width.

    print_full: mode control:
      - 0: only snip long strings
      - 1: send to page() directly.
      - 2: snip long strings and ask for full length viewing with page()
    Return 1 if snipping was necessary, 0 otherwise."""

    if print_full == 1:
        page(header+str)
        return 0

    print header,
    if len(str) < width:
        print str
        snip = 0
    else:
        whalf = int((width -5)/2)
        print str[:whalf] + ' <...> ' + str[-whalf:]
        snip = 1
    if snip and print_full == 2:
        if raw_input(header+' Snipped. View (y/n)? [N]').lower() == 'y':
            page(str)
    return snip

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

#*************************** end of file <genutils.py> **********************

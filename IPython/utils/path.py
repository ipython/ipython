# encoding: utf-8
"""
Utilities for path handling.
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
from hashlib import md5

import IPython
from IPython.utils import warn
from IPython.utils.process import system
from IPython.utils.importstring import import_item

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

fs_encoding = sys.getfilesystemencoding()

def _cast_unicode(s, enc=None):
    """Turn 8-bit strings into unicode."""
    if isinstance(s, bytes):
        enc = enc or sys.getdefaultencoding()
        return s.decode(enc)
    return s


def _get_long_path_name(path):
    """Dummy no-op."""
    return path

if sys.platform == 'win32':
    def _get_long_path_name(path):
        """Get a long path name (expand ~) on Windows using ctypes.

        Examples
        --------

        >>> get_long_path_name('c:\\docume~1')
        u'c:\\\\Documents and Settings'

        """
        try:
            import ctypes
        except ImportError:
            raise ImportError('you need to have ctypes installed for this to work')
        _GetLongPathName = ctypes.windll.kernel32.GetLongPathNameW
        _GetLongPathName.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p,
            ctypes.c_uint ]

        buf = ctypes.create_unicode_buffer(260)
        rv = _GetLongPathName(path, buf, 260)
        if rv == 0 or rv > 260:
            return path
        else:
            return buf.value


def get_long_path_name(path):
    """Expand a path into its long form.

    On Windows this expands any ~ in the paths. On other platforms, it is
    a null operation.
    """
    return _get_long_path_name(path)


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
        if path == '.': path = os.getcwdu()
        testname = expand_path(os.path.join(path, filename))
        if os.path.isfile(testname):
            return os.path.abspath(testname)
        
    raise IOError("File %r does not exist in any of the search paths: %r" % 
                  (filename, path_dirs) )


class HomeDirError(Exception):
    pass


def get_home_dir():
    """Return the closest possible equivalent to a 'home' directory.

    * On POSIX, we try $HOME.
    * On Windows we try:
      - %HOMESHARE%
      - %HOMEDRIVE\%HOMEPATH%
      - %USERPROFILE%
      - Registry hack for My Documents
      - %HOME%: rare, but some people with unix-like setups may have defined it
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
        return _cast_unicode(root, fs_encoding)

    if os.name == 'posix':
        # Linux, Unix, AIX, OS X
        try:
            homedir = env['HOME']
        except KeyError:
            # Last-ditch attempt at finding a suitable $HOME, on systems where
            # it may not be defined in the environment but the system shell
            # still knows it - reported once as:
            # https://github.com/ipython/ipython/issues/154
            from subprocess import Popen, PIPE
            homedir = Popen('echo $HOME', shell=True, 
                            stdout=PIPE).communicate()[0].strip()
            if homedir:
                return _cast_unicode(homedir, fs_encoding)
            else:
                raise HomeDirError('Undefined $HOME, IPython cannot proceed.')
        else:
            return _cast_unicode(homedir, fs_encoding)
    elif os.name == 'nt':
        # Now for win9x, XP, Vista, 7?
        # For some strange reason all of these return 'nt' for os.name.
        # First look for a network home directory. This will return the UNC
        # path (\\server\\Users\%username%) not the mapped path (Z:\). This
        # is needed when running IPython on cluster where all paths have to 
        # be UNC.
        try:
            homedir = env['HOMESHARE']
        except KeyError:
            pass
        else:
            if isdir(homedir):
                return _cast_unicode(homedir, fs_encoding)

        # Now look for a local home directory
        try:
            homedir = os.path.join(env['HOMEDRIVE'],env['HOMEPATH'])
        except KeyError:
            pass
        else:
            if isdir(homedir):
                return _cast_unicode(homedir, fs_encoding)

        # Now the users profile directory
        try:
            homedir = os.path.join(env['USERPROFILE'])
        except KeyError:
            pass
        else:
            if isdir(homedir):
                return _cast_unicode(homedir, fs_encoding)

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
                return _cast_unicode(homedir, fs_encoding)

        # A user with a lot of unix tools in win32 may have defined $HOME.
        # Try this as a last ditch option.
        try:
            homedir = env['HOME']
        except KeyError:
            pass
        else:
            if isdir(homedir):
                return _cast_unicode(homedir, fs_encoding)

        # If all else fails, raise HomeDirError
        raise HomeDirError('No valid home directory could be found')
    elif os.name == 'dos':
        # Desperate, may do absurd things in classic MacOS. May work under DOS.
        return u'C:\\'
    else:
        raise HomeDirError('No valid home directory could be found for your OS')

def get_xdg_dir():
    """Return the XDG_CONFIG_HOME, if it is defined and exists, else None.
    
    This is only for posix (Linux,Unix,OS X, etc) systems.
    """

    isdir = os.path.isdir
    env = os.environ
    
    if os.name == 'posix':
        # Linux, Unix, AIX, OS X
        # use ~/.config if not set OR empty
        xdg = env.get("XDG_CONFIG_HOME", None) or os.path.join(get_home_dir(), '.config')
        if xdg and isdir(xdg):
            return _cast_unicode(xdg, fs_encoding)
    
    return None
    

def get_ipython_dir():
    """Get the IPython directory for this platform and user.
    
    This uses the logic in `get_home_dir` to find the home directory
    and the adds .ipython to the end of the path.
    """
    
    env = os.environ
    pjoin = os.path.join
    exists = os.path.exists
    
    ipdir_def = '.ipython'
    xdg_def = 'ipython'
    
    home_dir = get_home_dir()
    xdg_dir = get_xdg_dir()
    # import pdb; pdb.set_trace()  # dbg
    ipdir = env.get('IPYTHON_DIR', env.get('IPYTHONDIR', None))
    if ipdir is None:
        # not set explicitly, use XDG_CONFIG_HOME or HOME
        home_ipdir = pjoin(home_dir, ipdir_def)
        if xdg_dir:
            # use XDG, as long as the user isn't already
            # using $HOME/.ipython and *not* XDG/ipython
            
            xdg_ipdir = pjoin(xdg_dir, xdg_def)
        
            if exists(xdg_ipdir) or not exists(home_ipdir):
                ipdir = xdg_ipdir
        
        if ipdir is None:
            # not using XDG
            ipdir = home_ipdir

    ipdir = os.path.normpath(os.path.expanduser(ipdir))

    return _cast_unicode(ipdir, fs_encoding)


def get_ipython_package_dir():
    """Get the base directory where IPython itself is installed."""
    ipdir = os.path.dirname(IPython.__file__)
    return _cast_unicode(ipdir, fs_encoding)


def get_ipython_module_path(module_str):
    """Find the path to an IPython module in this version of IPython.

    This will always find the version of the module that is in this importable
    IPython package. This will always return the path to the ``.py``
    version of the module.
    """
    if module_str == 'IPython':
        return os.path.join(get_ipython_package_dir(), '__init__.py')
    mod = import_item(module_str)
    the_path = mod.__file__.replace('.pyc', '.py')
    the_path = the_path.replace('.pyo', '.py')
    return _cast_unicode(the_path, fs_encoding)


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


def target_update(target,deps,cmd):
    """Update a target with a given command given a list of dependencies.

    target_update(target,deps,cmd) -> runs cmd if target is outdated.

    This is just a wrapper around target_outdated() which calls the given
    command if target is outdated."""

    if target_outdated(target,deps):
        system(cmd)

def filehash(path):
    """Make an MD5 hash of a file, ignoring any differences in line
    ending characters."""
    with open(path, "rU") as f:
        return md5(f.read()).hexdigest()

# If the config is unmodified from the default, we'll just delete it.
# These are consistent for 0.10.x, thankfully. We're not going to worry about
# older versions.
old_config_md5 = {'ipy_user_conf.py': 'fc108bedff4b9a00f91fa0a5999140d3',
                  'ipythonrc': '12a68954f3403eea2eec09dc8fe5a9b5'}

def check_for_old_config(ipython_dir=None):
    """Check for old config files, and present a warning if they exist.

    A link to the docs of the new config is included in the message.

    This should mitigate confusion with the transition to the new
    config system in 0.11.
    """
    if ipython_dir is None:
        ipython_dir = get_ipython_dir()

    old_configs = ['ipy_user_conf.py', 'ipythonrc', 'ipython_config.py']
    warned = False
    for cfg in old_configs:
        f = os.path.join(ipython_dir, cfg)
        if os.path.exists(f):
            if filehash(f) == old_config_md5.get(cfg, ''):
                os.unlink(f)
            else:
                oldf = f+'.old'
                i = 0
                while os.path.exists(oldf):
                    oldf = f+'.old.%i'%i
                    i += 1
                os.rename(f, oldf)
                warn.warn("Renamed old IPython config file '%s' to '%s'." % (f, oldf))
                warned = True
    
    if warned:
        warn.info("""
  The IPython configuration system has changed as of 0.11, and these files will
  be ignored. See http://ipython.github.com/ipython-doc/dev/config for details
  of the new config system.
  To start configuring IPython, do `ipython profile create`, and edit
  `ipython_config.py` in <ipython_dir>/profile_default.
  If you need to leave the old config files in place for an older version of
  IPython, set `c.InteractiveShellApp.ignore_old_config=True` in the new config.""")
        


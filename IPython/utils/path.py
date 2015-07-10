# encoding: utf-8
"""
Utilities for path handling.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys
import errno
import shutil
import random
import tempfile
import glob
from warnings import warn
from hashlib import md5

import IPython
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.process import system
from IPython.utils.importstring import import_item
from IPython.utils import py3compat
#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

fs_encoding = sys.getfilesystemencoding()

def _writable_dir(path):
    """Whether `path` is a directory, to which the user has write access."""
    return os.path.isdir(path) and os.access(path, os.W_OK)

if sys.platform == 'win32':
    @skip_doctest
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
else:
    def _get_long_path_name(path):
        """Dummy no-op."""
        return path



def get_long_path_name(path):
    """Expand a path into its long form.

    On Windows this expands any ~ in the paths. On other platforms, it is
    a null operation.
    """
    return _get_long_path_name(path)


def unquote_filename(name, win32=(sys.platform=='win32')):
    """ On Windows, remove leading and trailing quotes from filenames.
    """
    if win32:
        if name.startswith(("'", '"')) and name.endswith(("'", '"')):
            name = name[1:-1]
    return name

def compress_user(path):
    """Reverse of :func:`os.path.expanduser`
    """    
    path = py3compat.unicode_to_str(path, sys.getfilesystemencoding())
    home = os.path.expanduser('~')
    if path.startswith(home):
        path =  "~" + path[len(home):]
    return path

def get_py_filename(name, force_win32=None):
    """Return a valid python filename in the current directory.

    If the given name is not a file, it adds '.py' and searches again.
    Raises IOError with an informative message if the file isn't found.

    On Windows, apply Windows semantics to the filename. In particular, remove
    any quoting that has been applied to it. This option can be forced for
    testing purposes.
    """

    name = os.path.expanduser(name)
    if force_win32 is None:
        win32 = (sys.platform == 'win32')
    else:
        win32 = force_win32
    name = unquote_filename(name, win32=win32)
    if not os.path.isfile(name) and not name.endswith('.py'):
        name += '.py'
    if os.path.isfile(name):
        return name
    else:
        raise IOError('File `%r` not found.' % name)


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
    elif isinstance(path_dirs, py3compat.string_types):
        path_dirs = (path_dirs,)

    for path in path_dirs:
        if path == '.': path = py3compat.getcwd()
        testname = expand_path(os.path.join(path, filename))
        if os.path.isfile(testname):
            return os.path.abspath(testname)

    raise IOError("File %r does not exist in any of the search paths: %r" %
                  (filename, path_dirs) )


class HomeDirError(Exception):
    pass


def get_home_dir(require_writable=False):
    """Return the 'home' directory, as a unicode string.

    Uses os.path.expanduser('~'), and checks for writability.

    See stdlib docs for how this is determined.
    $HOME is first priority on *ALL* platforms.

    Parameters
    ----------

    require_writable : bool [default: False]
        if True:
            guarantees the return value is a writable directory, otherwise
            raises HomeDirError
        if False:
            The path is resolved, but it is not guaranteed to exist or be writable.
    """

    homedir = os.path.expanduser('~')
    # Next line will make things work even when /home/ is a symlink to
    # /usr/home as it is on FreeBSD, for example
    homedir = os.path.realpath(homedir)

    if not _writable_dir(homedir) and os.name == 'nt':
        # expanduser failed, use the registry to get the 'My Documents' folder.
        try:
            try:
                import winreg as wreg  # Py 3
            except ImportError:
                import _winreg as wreg  # Py 2
            key = wreg.OpenKey(
                wreg.HKEY_CURRENT_USER,
                "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            homedir = wreg.QueryValueEx(key,'Personal')[0]
            key.Close()
        except:
            pass

    if (not require_writable) or _writable_dir(homedir):
        return py3compat.cast_unicode(homedir, fs_encoding)
    else:
        raise HomeDirError('%s is not a writable dir, '
                'set $HOME environment variable to override' % homedir)

def get_xdg_dir():
    """Return the XDG_CONFIG_HOME, if it is defined and exists, else None.

    This is only for non-OS X posix (Linux,Unix,etc.) systems.
    """

    env = os.environ

    if os.name == 'posix' and sys.platform != 'darwin':
        # Linux, Unix, AIX, etc.
        # use ~/.config if empty OR not set
        xdg = env.get("XDG_CONFIG_HOME", None) or os.path.join(get_home_dir(), '.config')
        if xdg and _writable_dir(xdg):
            return py3compat.cast_unicode(xdg, fs_encoding)

    return None


def get_xdg_cache_dir():
    """Return the XDG_CACHE_HOME, if it is defined and exists, else None.

    This is only for non-OS X posix (Linux,Unix,etc.) systems.
    """

    env = os.environ

    if os.name == 'posix' and sys.platform != 'darwin':
        # Linux, Unix, AIX, etc.
        # use ~/.cache if empty OR not set
        xdg = env.get("XDG_CACHE_HOME", None) or os.path.join(get_home_dir(), '.cache')
        if xdg and _writable_dir(xdg):
            return py3compat.cast_unicode(xdg, fs_encoding)

    return None


def get_ipython_dir():
    """Get the IPython directory for this platform and user.

    This uses the logic in `get_home_dir` to find the home directory
    and then adds .ipython to the end of the path.
    """

    env = os.environ
    pjoin = os.path.join


    ipdir_def = '.ipython'

    home_dir = get_home_dir()
    xdg_dir = get_xdg_dir()
    
    # import pdb; pdb.set_trace()  # dbg
    if 'IPYTHON_DIR' in env:
        warn('The environment variable IPYTHON_DIR is deprecated. '
                'Please use IPYTHONDIR instead.')
    ipdir = env.get('IPYTHONDIR', env.get('IPYTHON_DIR', None))
    if ipdir is None:
        # not set explicitly, use ~/.ipython
        ipdir = pjoin(home_dir, ipdir_def)
        if xdg_dir:
            # Several IPython versions (up to 1.x) defaulted to .config/ipython
            # on Linux. We have decided to go back to using .ipython everywhere
            xdg_ipdir = pjoin(xdg_dir, 'ipython')

            if _writable_dir(xdg_ipdir):
                cu = compress_user
                if os.path.exists(ipdir):
                    warn(('Ignoring {0} in favour of {1}. Remove {0} to '
                        'get rid of this message').format(cu(xdg_ipdir), cu(ipdir)))
                elif os.path.islink(xdg_ipdir):
                    warn(('{0} is deprecated. Move link to {1} to '
                        'get rid of this message').format(cu(xdg_ipdir), cu(ipdir)))
                else:
                    warn('Moving {0} to {1}'.format(cu(xdg_ipdir), cu(ipdir)))
                    shutil.move(xdg_ipdir, ipdir)

    ipdir = os.path.normpath(os.path.expanduser(ipdir))

    if os.path.exists(ipdir) and not _writable_dir(ipdir):
        # ipdir exists, but is not writable
        warn("IPython dir '{0}' is not a writable location,"
                " using a temp directory.".format(ipdir))
        ipdir = tempfile.mkdtemp()
    elif not os.path.exists(ipdir):
        parent = os.path.dirname(ipdir)
        if not _writable_dir(parent):
            # ipdir does not exist and parent isn't writable
            warn("IPython parent '{0}' is not a writable location,"
                    " using a temp directory.".format(parent))
            ipdir = tempfile.mkdtemp()

    return py3compat.cast_unicode(ipdir, fs_encoding)


def get_ipython_cache_dir():
    """Get the cache directory it is created if it does not exist."""
    xdgdir = get_xdg_cache_dir()
    if xdgdir is None:
        return get_ipython_dir()
    ipdir = os.path.join(xdgdir, "ipython")
    if not os.path.exists(ipdir) and _writable_dir(xdgdir):
        ensure_dir_exists(ipdir)
    elif not _writable_dir(xdgdir):
        return get_ipython_dir()

    return py3compat.cast_unicode(ipdir, fs_encoding)


def get_ipython_package_dir():
    """Get the base directory where IPython itself is installed."""
    ipdir = os.path.dirname(IPython.__file__)
    return py3compat.cast_unicode(ipdir, fs_encoding)


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
    return py3compat.cast_unicode(the_path, fs_encoding)

def locate_profile(profile='default'):
    """Find the path to the folder associated with a given profile.
    
    I.e. find $IPYTHONDIR/profile_whatever.
    """
    from IPython.core.profiledir import ProfileDir, ProfileDirError
    try:
        pd = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), profile)
    except ProfileDirError:
        # IOError makes more sense when people are expecting a path
        raise IOError("Couldn't find profile %r" % profile)
    return pd.location

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


def unescape_glob(string):
    """Unescape glob pattern in `string`."""
    def unescape(s):
        for pattern in '*[]!?':
            s = s.replace(r'\{0}'.format(pattern), pattern)
        return s
    return '\\'.join(map(unescape, string.split('\\\\')))


def shellglob(args):
    """
    Do glob expansion for each element in `args` and return a flattened list.

    Unmatched glob pattern will remain as-is in the returned list.

    """
    expanded = []
    # Do not unescape backslash in Windows as it is interpreted as
    # path separator:
    unescape = unescape_glob if sys.platform != 'win32' else lambda x: x
    for a in args:
        expanded.extend(glob.glob(a) or [unescape(a)])
    return expanded


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
        return md5(py3compat.str_to_bytes(f.read())).hexdigest()

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
                warn("Found old IPython config file {!r} (modified by user)".format(f))
                warned = True

    if warned:
        warn("""
  The IPython configuration system has changed as of 0.11, and these files will
  be ignored. See http://ipython.github.com/ipython-doc/dev/config for details
  of the new config system.
  To start configuring IPython, do `ipython profile create`, and edit
  `ipython_config.py` in <ipython_dir>/profile_default.
  If you need to leave the old config files in place for an older version of
  IPython and want to suppress this warning message, set
  `c.InteractiveShellApp.ignore_old_config=True` in the new config.""")

def get_security_file(filename, profile='default'):
    """Return the absolute path of a security file given by filename and profile
    
    This allows users and developers to find security files without
    knowledge of the IPython directory structure. The search path
    will be ['.', profile.security_dir]
    
    Parameters
    ----------
    
    filename : str
        The file to be found. If it is passed as an absolute path, it will
        simply be returned.
    profile : str [default: 'default']
        The name of the profile to search.  Leaving this unspecified
        The file to be found. If it is passed as an absolute path, fname will
        simply be returned.
    
    Returns
    -------
    Raises :exc:`IOError` if file not found or returns absolute path to file.
    """
    # import here, because profiledir also imports from utils.path
    from IPython.core.profiledir import ProfileDir
    try:
        pd = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), profile)
    except Exception:
        # will raise ProfileDirError if no such profile
        raise IOError("Profile %r not found")
    return filefind(filename, ['.', pd.security_dir])


ENOLINK = 1998

def link(src, dst):
    """Hard links ``src`` to ``dst``, returning 0 or errno.

    Note that the special errno ``ENOLINK`` will be returned if ``os.link`` isn't
    supported by the operating system.
    """

    if not hasattr(os, "link"):
        return ENOLINK
    link_errno = 0
    try:
        os.link(src, dst)
    except OSError as e:
        link_errno = e.errno
    return link_errno


def link_or_copy(src, dst):
    """Attempts to hardlink ``src`` to ``dst``, copying if the link fails.

    Attempts to maintain the semantics of ``shutil.copy``.

    Because ``os.link`` does not overwrite files, a unique temporary file
    will be used if the target already exists, then that file will be moved
    into place.
    """

    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))

    link_errno = link(src, dst)
    if link_errno == errno.EEXIST:
        if os.stat(src).st_ino == os.stat(dst).st_ino:
            # dst is already a hard link to the correct file, so we don't need
            # to do anything else. If we try to link and rename the file
            # anyway, we get duplicate files - see http://bugs.python.org/issue21876
            return

        new_dst = dst + "-temp-%04X" %(random.randint(1, 16**4), )
        try:
            link_or_copy(src, new_dst)
        except:
            try:
                os.remove(new_dst)
            except OSError:
                pass
            raise
        os.rename(new_dst, dst)
    elif link_errno != 0:
        # Either link isn't supported, or the filesystem doesn't support
        # linking, or 'src' and 'dst' are on different filesystems.
        shutil.copy(src, dst)

def ensure_dir_exists(path, mode=0o755):
    """ensure that a directory exists

    If it doesn't exist, try to create it and protect against a race condition
    if another process is doing the same.

    The default permissions are 755, which differ from os.makedirs default of 777.
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path, mode=mode)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    elif not os.path.isdir(path):
        raise IOError("%r exists but is not a directory" % path)

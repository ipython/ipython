# encoding: utf-8

"""Configuration-related utilities for all IPython."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os
import sys

#---------------------------------------------------------------------------
# Normal code begins
#---------------------------------------------------------------------------

class HomeDirError(Exception):
    pass

def get_home_dir():
    """Return the closest possible equivalent to a 'home' directory.

    We first try $HOME.  Absent that, on NT it's $HOMEDRIVE\$HOMEPATH.

    Currently only Posix and NT are implemented, a HomeDirError exception is
    raised for all other OSes. """

    isdir = os.path.isdir
    env = os.environ
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
    ipdir_def = '.ipython'
    home_dir = get_home_dir()
    ipdir = os.path.abspath(os.environ.get('IPYTHONDIR',
                                           os.path.join(home_dir,ipdir_def)))
    return ipdir

def import_item(key):
    """
    Import and return bar given the string foo.bar.
    """
    package = '.'.join(key.split('.')[0:-1])
    obj = key.split('.')[-1]
    execString = 'from %s import %s' % (package, obj)
    exec execString
    exec 'temp = %s' % obj 
    return temp

"""Connection file-related utilities for the kernel
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import absolute_import

import json
import sys
from subprocess import Popen, PIPE

from IPython.core.profiledir import ProfileDir
from IPython.utils.path import filefind, get_ipython_dir
from IPython.utils.py3compat import str_to_bytes

import jupyter_client
from jupyter_client import write_connection_file



def get_connection_file(app=None):
    """Return the path to the connection file of an app

    Parameters
    ----------
    app : IPKernelApp instance [optional]
        If unspecified, the currently running app will be used
    """
    if app is None:
        from ipython_kernel.kernelapp import IPKernelApp
        if not IPKernelApp.initialized():
            raise RuntimeError("app not specified, and not in a running Kernel")

        app = IPKernelApp.instance()
    return filefind(app.connection_file, ['.', app.profile_dir.security_dir])


def find_connection_file(filename='kernel-*.json', profile=None):
    """find a connection file, and return its absolute path.

    The current working directory and the profile's security
    directory will be searched for the file if it is not given by
    absolute path.

    If profile is unspecified, then the current running application's
    profile will be used, or 'default', if not run from IPython.

    If the argument does not match an existing file, it will be interpreted as a
    fileglob, and the matching file in the profile's security dir with
    the latest access time will be used.

    Parameters
    ----------
    filename : str
        The connection file or fileglob to search for.
    profile : str [optional]
        The name of the profile to use when searching for the connection file,
        if different from the current IPython session or 'default'.

    Returns
    -------
    str : The absolute path of the connection file.
    """
    from IPython.core.application import BaseIPythonApplication as IPApp
    try:
        # quick check for absolute path, before going through logic
        return filefind(filename)
    except IOError:
        pass

    if profile is None:
        # profile unspecified, check if running from an IPython app
        if IPApp.initialized():
            app = IPApp.instance()
            profile_dir = app.profile_dir
        else:
            # not running in IPython, use default profile
            profile_dir = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), 'default')
    else:
        # find profiledir by profile name:
        profile_dir = ProfileDir.find_profile_dir_by_name(get_ipython_dir(), profile)
    security_dir = profile_dir.security_dir
    
    return jupyter_client.find_connection_file(filename, path=['.', security_dir])


def get_connection_info(connection_file=None, unpack=False, profile=None):
    """Return the connection information for the current Kernel.

    Parameters
    ----------
    connection_file : str [optional]
        The connection file to be used. Can be given by absolute path, or
        IPython will search in the security directory of a given profile.
        If run from IPython,

        If unspecified, the connection file for the currently running
        IPython Kernel will be used, which is only allowed from inside a kernel.
    unpack : bool [default: False]
        if True, return the unpacked dict, otherwise just the string contents
        of the file.
    profile : str [optional]
        The name of the profile to use when searching for the connection file,
        if different from the current IPython session or 'default'.


    Returns
    -------
    The connection dictionary of the current kernel, as string or dict,
    depending on `unpack`.
    """
    if connection_file is None:
        # get connection file from current kernel
        cf = get_connection_file()
    else:
        # connection file specified, allow shortnames:
        cf = find_connection_file(connection_file, profile=profile)

    with open(cf) as f:
        info = f.read()

    if unpack:
        info = json.loads(info)
        # ensure key is bytes:
        info['key'] = str_to_bytes(info.get('key', ''))
    return info


def connect_qtconsole(connection_file=None, argv=None, profile=None):
    """Connect a qtconsole to the current kernel.

    This is useful for connecting a second qtconsole to a kernel, or to a
    local notebook.

    Parameters
    ----------
    connection_file : str [optional]
        The connection file to be used. Can be given by absolute path, or
        IPython will search in the security directory of a given profile.
        If run from IPython,

        If unspecified, the connection file for the currently running
        IPython Kernel will be used, which is only allowed from inside a kernel.
    argv : list [optional]
        Any extra args to be passed to the console.
    profile : str [optional]
        The name of the profile to use when searching for the connection file,
        if different from the current IPython session or 'default'.


    Returns
    -------
    :class:`subprocess.Popen` instance running the qtconsole frontend
    """
    argv = [] if argv is None else argv

    if connection_file is None:
        # get connection file from current kernel
        cf = get_connection_file()
    else:
        cf = find_connection_file(connection_file, profile=profile)

    cmd = ';'.join([
        "from IPython.qt.console import qtconsoleapp",
        "qtconsoleapp.main()"
    ])

    return Popen([sys.executable, '-c', cmd, '--existing', cf] + argv,
        stdout=PIPE, stderr=PIPE, close_fds=(sys.platform != 'win32'),
    )


__all__ = [
    'write_connection_file',
    'get_connection_file',
    'find_connection_file',
    'get_connection_info',
    'connect_qtconsole',
]

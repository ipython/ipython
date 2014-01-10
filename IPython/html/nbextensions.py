# coding: utf-8
"""Utilities for installing Javascript extensions for the notebook"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2014 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import print_function

import os
import shutil
from os.path import basename, join as pjoin

from IPython.utils.path import get_ipython_dir
from IPython.utils.py3compat import string_types, cast_unicode_py2


def _should_copy(src, dest, verbose=1):
    """should a file be copied?"""
    if not os.path.exists(dest):
        return True
    if os.stat(dest).st_mtime < os.stat(src).st_mtime:
        if verbose >= 2:
            print("%s is out of date" % dest)
        return True
    if verbose >= 2:
        print("%s is up to date" % dest)
    return False


def _maybe_copy(src, dest, verbose=1):
    """copy a file if it needs updating"""
    if _should_copy(src, dest, verbose):
        if verbose >= 1:
            print("copying %s -> %s" % (src, dest))
        shutil.copy2(src, dest)


def install_nbextension(files, overwrite=False, ipython_dir=None, verbose=1):
    """Install a Javascript extension for the notebook
    
    Stages files and/or directories into IPYTHONDIR/nbextensions.
    By default, this comparse modification time, and only stages files that need updating.
    If `overwrite` is specified, matching files are purged before proceeding.
    
    Parameters
    ----------
    
    files : list(paths)
        One or more paths to existing files or directories to install.
        These will be installed with their base name, so '/path/to/foo'
        will install to 'nbextensions/foo'.
    overwrite : bool [default: False]
        If True, always install the files, regardless of what may already be installed.
    ipython_dir : str [optional]
        The path to an IPython directory, if the default value is not desired.
        get_ipython_dir() is used by default.
    verbose : int [default: 1]
        Set verbosity level. The default is 1, where file actions are printed.
        set verbose=2 for more output, or verbose=0 for silence.
    """
    
    ipython_dir = ipython_dir or get_ipython_dir()
    nbext = pjoin(ipython_dir, u'nbextensions')
    # make sure nbextensions dir exists
    if not os.path.exists(nbext):
        os.makedirs(nbext)
    
    if isinstance(files, string_types):
        # one file given, turn it into a list
        files = [files]
    
    for path in map(cast_unicode_py2, files):
        dest = pjoin(nbext, basename(path))
        if overwrite and os.path.exists(dest):
            if verbose >= 1:
                print("removing %s" % dest)
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            else:
                os.remove(dest)

        if os.path.isdir(path):
            strip_prefix_len = len(path) - len(basename(path))
            for parent, dirs, files in os.walk(path):
                dest_dir = pjoin(nbext, parent[strip_prefix_len:])
                if not os.path.exists(dest_dir):
                    if verbose >= 2:
                        print("making directory %s" % dest_dir)
                    os.makedirs(dest_dir)
                for file in files:
                    src = pjoin(parent, file)
                    # print("%r, %r" % (dest_dir, file))
                    dest = pjoin(dest_dir, file)
                    _maybe_copy(src, dest, verbose)
        else:
            src = path
            _maybe_copy(src, dest, verbose)

#----------------------------------------------------------------------
# install nbextension app
#----------------------------------------------------------------------

import logging
from IPython.utils.traitlets import Bool, Enum
from IPython.core.application import BaseIPythonApplication

flags = {
    "overwrite" : ({
        "NBExtensionApp" : {
            "overwrite" : True,
        }}, "Force overwrite of existing files"
    ),
    "debug" : ({
        "NBExtensionApp" : {
            "verbose" : 2,
        }}, "Extra output"
    ),
    "quiet" : ({
        "NBExtensionApp" : {
            "verbose" : 0,
        }}, "Minimal output"
    ),
}
aliases = {
    "ipython-dir" : "NBExtensionApp.ipython_dir"
}

class NBExtensionApp(BaseIPythonApplication):
    """Entry point for installing notebook extensions"""
    
    description = """Install IPython notebook extensions
    
    Usage
    
        ipython install-nbextension file [more files or folders]
    
    This copies files and/or folders into the IPython nbextensions directory.
    If the requested files are already up to date, no action is taken
    unless --overwrite is specified.
    """
    
    examples = """
    ipython install-nbextension /path/to/d3.js /path/to/myextension
    """
    aliases = aliases
    flags = flags
    
    overwrite = Bool(False, config=True, help="Force overwrite of existing files")
    verbose = Enum((0,1,2), default_value=1, config=True,
        help="Verbosity level"
    )
    
    def install_extensions(self):
        install_nbextension(self.extra_args,
            overwrite=self.overwrite,
            verbose=self.verbose,
            ipython_dir=self.ipython_dir,
        )
    
    def start(self):
        if not self.extra_args:
            nbext = pjoin(self.ipython_dir, u'nbextensions')
            print("Notebook extensions in %s:" % nbext)
            for ext in os.listdir(nbext):
                print(u"    %s" % ext)
        else:
            self.install_extensions()


if __name__ == '__main__':
    NBExtensionApp.launch_instance()
    
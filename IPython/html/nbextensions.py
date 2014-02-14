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
import tarfile
import zipfile
from os.path import basename, join as pjoin

# Deferred imports
try:
    from urllib.parse import urlparse  # Py3
    from urllib.request import urlretrieve
except ImportError:
    from urlparse import urlparse
    from urllib import urlretrieve

from IPython.utils.path import get_ipython_dir
from IPython.utils.py3compat import string_types, cast_unicode_py2
from IPython.utils.tempdir import TemporaryDirectory


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


def _safe_is_tarfile(path):
    """safe version of is_tarfile, return False on IOError"""
    try:
        return tarfile.is_tarfile(path)
    except IOError:
        return False


def check_nbextension(files, ipython_dir=None):
    """Check whether nbextension files have been installed
    
    files should be a list of relative paths within nbextensions.
    
    Returns True if all files are found, False if any are missing.
    """
    ipython_dir = ipython_dir or get_ipython_dir()
    nbext = pjoin(ipython_dir, u'nbextensions')
    # make sure nbextensions dir exists
    if not os.path.exists(nbext):
        return False
    
    if isinstance(files, string_types):
        # one file given, turn it into a list
        files = [files]
    
    return all(os.path.exists(pjoin(nbext, f)) for f in files)


def install_nbextension(files, overwrite=False, symlink=False, ipython_dir=None, verbose=1):
    """Install a Javascript extension for the notebook
    
    Stages files and/or directories into IPYTHONDIR/nbextensions.
    By default, this compares modification time, and only stages files that need updating.
    If `overwrite` is specified, matching files are purged before proceeding.
    
    Parameters
    ----------
    
    files : list(paths or URLs)
        One or more paths or URLs to existing files directories to install.
        These will be installed with their base name, so '/path/to/foo'
        will install to 'nbextensions/foo'.
        Archives (zip or tarballs) will be extracted into the nbextensions directory.
    overwrite : bool [default: False]
        If True, always install the files, regardless of what may already be installed.
    symlink : bool [default: False]
        If True, create a symlink in nbextensions, rather than copying files.
        Not allowed with URLs or archives.
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
        
        if path.startswith(('https://', 'http://')):
            if symlink:
                raise ValueError("Cannot symlink from URLs")
            # Given a URL, download it
            with TemporaryDirectory() as td:
                filename = urlparse(path).path.split('/')[-1]
                local_path = os.path.join(td, filename)
                if verbose >= 1:
                    print("downloading %s to %s" % (path, local_path))
                urlretrieve(path, local_path)
                # now install from the local copy
                install_nbextension(local_path, overwrite, symlink, ipython_dir, verbose)
            continue
        
        # handle archives
        archive = None
        if path.endswith('.zip'):
            archive = zipfile.ZipFile(path)
        elif _safe_is_tarfile(path):
            archive = tarfile.open(path)
        
        if archive:
            if symlink:
                raise ValueError("Cannot symlink from archives")
            if verbose >= 1:
                print("extracting %s to %s" % (path, nbext))
            archive.extractall(nbext)
            archive.close()
            continue
        
        dest = pjoin(nbext, basename(path))
        if overwrite and os.path.exists(dest):
            if verbose >= 1:
                print("removing %s" % dest)
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            else:
                os.remove(dest)
        
        if symlink:
            path = os.path.abspath(path)
            if not os.path.exists(dest):
                if verbose >= 1:
                    print("symlink %s -> %s" % (dest, path))
                os.symlink(path, dest)
            continue

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
    "symlink" : ({
        "NBExtensionApp" : {
            "symlink" : True,
        }}, "Create symlinks instead of copying files"
    ),
}
flags['s'] = flags['symlink']

aliases = {
    "ipython-dir" : "NBExtensionApp.ipython_dir"
}

class NBExtensionApp(BaseIPythonApplication):
    """Entry point for installing notebook extensions"""
    
    description = """Install IPython notebook extensions
    
    Usage
    
        ipython install-nbextension file [more files, folders, archives or urls]
    
    This copies files and/or folders into the IPython nbextensions directory.
    If a URL is given, it will be downloaded.
    If an archive is given, it will be extracted into nbextensions.
    If the requested files are already up to date, no action is taken
    unless --overwrite is specified.
    """
    
    examples = """
    ipython install-nbextension /path/to/d3.js /path/to/myextension
    """
    aliases = aliases
    flags = flags
    
    overwrite = Bool(False, config=True, help="Force overwrite of existing files")
    symlink = Bool(False, config=True, help="Create symlinks instead of copying files")
    verbose = Enum((0,1,2), default_value=1, config=True,
        help="Verbosity level"
    )
    
    def install_extensions(self):
        install_nbextension(self.extra_args,
            overwrite=self.overwrite,
            symlink=self.symlink,
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
    
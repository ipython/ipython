"""Utility function for installing MathJax javascript library into
the notebook's 'static' directory, for offline use.

Authors:

* Min RK
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import shutil
import urllib2
import tempfile
import tarfile

from IPython.utils.path import locate_profile

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

def install_mathjax(tag='v2.0', replace=False, dest=None):
    """Download and install MathJax for offline use.
    
    You can use this to install mathjax to a location on your static file
    path. This includes the `static` directory within your IPython profile,
    which is the default location for this install.
    
    MathJax is a ~15MB download, and ~150MB installed.
    
    Parameters
    ----------
    
    replace : bool [False]
        Whether to remove and replace an existing install.
    tag : str ['v2.0']
        Which tag to download. Default is 'v2.0', the current stable release,
        but alternatives include 'v1.1' and 'master'.
    dest : path
        The path to the directory in which mathjax will be installed.
        The default is `IPYTHONDIR/profile_default/static`.
        dest must be on your notebook static_path when you run the notebook server.
        The default location works for this.
    """
    
    mathjax_url = "https://github.com/mathjax/MathJax/tarball/%s" % tag
    
    if dest is None:
        dest = os.path.join(locate_profile('default'), 'static')
    
    if not os.path.exists(dest):
        os.mkdir(dest)
    
    static = dest
    dest = os.path.join(static, 'mathjax')
    
    # check for existence and permissions
    if not os.access(static, os.W_OK):
        raise IOError("Need have write access to %s" % static)
    if os.path.exists(dest):
        if replace:
            if not os.access(dest, os.W_OK):
                raise IOError("Need have write access to %s" % dest)
            print "removing previous MathJax install"
            shutil.rmtree(dest)
        else:
            print "offline MathJax apparently already installed"
            return
    
    # download mathjax
    print "Downloading mathjax source from %s ..." % mathjax_url
    response = urllib2.urlopen(mathjax_url)
    print "done"
    # use 'r|gz' stream mode, because socket file-like objects can't seek:
    tar = tarfile.open(fileobj=response.fp, mode='r|gz')
    topdir = tar.firstmember.path
    print "Extracting to %s" % dest
    tar.extractall(static)
    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    os.rename(os.path.join(static, topdir), dest)


__all__ = ['install_mathjax']

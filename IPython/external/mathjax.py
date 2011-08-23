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

from IPython.frontend.html import notebook as nbmod

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

def install_mathjax(tag='v1.1', replace=False):
    """Download and install MathJax for offline use.
    
    This will install mathjax to the 'static' dir in the IPython notebook
    package, so it will fail if the caller does not have write access
    to that location.
    
    MathJax is a ~15MB download, and ~150MB installed.
    
    Parameters
    ----------
    
    replace : bool [False]
        Whether to remove and replace an existing install.
    tag : str ['v1.1']
        Which tag to download. Default is 'v1.1', the current stable release,
        but alternatives include 'v1.1a' and 'master'.
    """
    mathjax_url = "https://github.com/mathjax/MathJax/tarball/%s"%tag
    
    nbdir = os.path.dirname(os.path.abspath(nbmod.__file__))
    static = os.path.join(nbdir, 'static')
    dest = os.path.join(static, 'mathjax')
    
    # check for existence and permissions
    if not os.access(static, os.W_OK):
        raise IOError("Need have write access to %s"%static)
    if os.path.exists(dest):
        if replace:
            if not os.access(dest, os.W_OK):
                raise IOError("Need have write access to %s"%dest)
            print "removing previous MathJax install"
            shutil.rmtree(dest)
        else:
            print "offline MathJax apparently already installed"
            return
    
    # download mathjax
    print "Downloading mathjax source..."
    response = urllib2.urlopen(mathjax_url)
    print "done"
    # use 'r|gz' stream mode, because socket file-like objects can't seek:
    tar = tarfile.open(fileobj=response.fp, mode='r|gz')
    topdir = tar.firstmember.path
    print "Extracting to %s"%dest
    tar.extractall(static)
    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    os.rename(os.path.join(static, topdir), dest)


__all__ = ['install_mathjax']

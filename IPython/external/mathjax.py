"""Utility function for installing MathJax javascript library into
the notebook's 'static' directory, for offline use.

 Authors:

 * Min RK
 * Mark Sienkiewicz
 * Matthias Bussonnier

To download and install MathJax:

From Python:

    >>> from IPython.external.mathjax import install_mathjax
    >>> install_mathjax()

From the command line:

    $ python -m IPython.external.mathjax

To install MathJax from a file you have already downloaded:

    $ python -m IPython.external.mathjax mathjax-xxx.tar.gz
    $ python -m IPython.external.mathjax mathjax-xxx.zip

It will not install MathJax if it is already there.  Use -r to
replace the existing copy of MathJax.

To find the directory where IPython would like MathJax installed:

    $ python -m IPython.external.mathjax -d

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
import sys
import tarfile
import urllib2
import zipfile

#-----------------------------------------------------------------------------
#
#-----------------------------------------------------------------------------

# Where mathjax will be installed.

dest = os.path.join(locate_profile('default'), 'static')

##

# Test for access to install mathjax.

def check_perms(replace=False):
    if not os.access(static, os.W_OK):
        raise IOError("Need have write access to %s" % static)
    if os.path.exists(dest):
        if replace:
            if not os.access(dest, os.W_OK):
                raise IOError("Need have write access to %s" % dest)
            print "removing previous MathJax install"
            shutil.rmtree(dest)
            return True
        else:
            print "offline MathJax apparently already installed"
            return False
    else :
        return True

##

def extract_tar( fd, dest ) :
    # use 'r|gz' stream mode, because socket file-like objects can't seek:
    tar = tarfile.open(fileobj=fd, mode='r|gz')

    # we just happen to know that the first entry in the mathjax
    # archive is the directory that the remaining members are in.
    topdir = tar.firstmember.path

    # extract the archive (contains a single directory) to the static/ directory
    tar.extractall(static)

    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    os.rename(os.path.join(static, topdir), dest)

##

def extract_zip( fd, dest ) :
    z = zipfile.ZipFile( fd, 'r' )

    # we just happen to know that the first entry in the mathjax
    # archive is the directory that the remaining members are in.
    topdir = z.namelist()[0]

    # extract the archive (contains a single directory) to the static/ directory
    z.extractall( static )

    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    d = os.path.join(static, topdir)
    print d
    os.rename(os.path.join(static, topdir), dest)

##

def install_mathjax(tag='v2.0', replace=False, file=None, extractor=extract_tar ):
    """Download and/or install MathJax for offline use.

    This will install mathjax to the 'static' dir in the IPython notebook
    package, so it will fail if the caller does not have write access
    to that location.

    MathJax is a ~15MB download, and ~150MB installed.

    Parameters
    ----------

    replace : bool [False]
        Whether to remove and replace an existing install.
    tag : str ['v2.0']
        Which tag to download. Default is 'v1.1', the current stable release,
        but alternatives include 'v1.1a' and 'master'.
    file : file like object [ defualt to content of https://github.com/mathjax/MathJax/tarball/#{tag}]
        File handle from which to untar/unzip/... mathjax
    extractor : function
        Method tu use to untar/unzip/... `file`
    """

    if not check_perms(replace) :
        return

    if file is None :
        # download mathjax
        mathjax_url = "https://github.com/mathjax/MathJax/tarball/%s"%tag
        print "Downloading mathjax source from %s"%mathjax_url
        response = urllib2.urlopen(mathjax_url)
        file = response.fp

    print "Extracting to %s"%dest
    extractor( fd, dest )

##

def test_func( remove ) :
    """See if mathjax appears to be installed correctly"""
    if not os.path.isdir( dest ) :
        print "%s directory not found"%dest
        status=1
    if not os.path.exists( dest + "/MathJax.js" ) :
        print "MathJax.js not present in %s"%dest
        status=1
    print "ok"
    if remove :
        shutil.rmtree( dest )
    return status

##

def main( args ) :
    # This main is just simple enough that it is not worth the
    # complexity of argparse

    # What directory is mathjax in?
    if '-d' in args :
        print dest
        return

    # help
    if '-h' in args or '--help' in args :
        print __doc__
        return

    # remove/replace existing mathjax?
    if '-r' in args :
        replace = True
        args.remove('-r')
    else :
        replace = False

    # undocumented test interface
    if '-test' in args :
        return test_func( replace )

    # do it
    if len(args) == 0 :
        # This is compatible with the interface documented in ipython 0.13
        install_mathjax( replace=replace )
    else :
        fname = args[0]

        # automatically detect zip/tar - could do something based
	    # on file content, but really not cost-effective here.
        if fname.endswith('.zip') :
            extractor = extract_zip
        else :
            extractor = extract_tar

        # do it
        install_mathjax(fd=open(args[0],"r"), replace=replace, extractor=extractor )

if __name__ == '__main__' :
    sys.exit(main( sys.argv[1:] ))

__all__ = ['install_mathjax','main','dest']

"""
Test notes:

IPython uses IPython.testing.iptest as a custom test controller
(though it is based on nose).  It might be possible to fit automatic
tests of installation into that framework, but it looks awkward to me.
So, here is a manual procedure for testing this automatic installer.

    Mark Sienkiewicz, 2012-08-06
    first 8 letters of my last name @ stsci.edu

# remove mathjax from the installed ipython instance
# IOError ok if mathjax was never installed yet.

python -m IPython.external.mathjax -test -r

# download and install mathjax from command line:

python -m IPython.external.mathjax
python -m IPython.external.mathjax -test -r

# download and install from within python

python -c "from IPython.external.mathjax import install_mathjax; install_mathjax()"
python -m IPython.external.mathjax -test -r

# view http://www.mathjax.org/download/ in your browser
# save-as the link for MathJax-1.1 near the bottom of the page.
# The file it offers is mathjax-MathJax-v1.1-0-g5a7e4d7.zip

python -m IPython.external.mathjax mathjax-MathJax-v1.1-0-g5a7e4d7.zip
python -m IPython.external.mathjax -test -r

# download https://github.com/mathjax/MathJax/tarball/v1.1 in your browser
# (this is the url used internally by install_mathjax)
# The file it offers is mathjax-MathJax-v1.1-0-g5a7e4d7.tar.gz

python -m IPython.external.mathjax mathjax-MathJax-v1.1-0-g5a7e4d7.tar.gz

python -m IPython.external.mathjax -test
        # note no -r

# install it again while it is already there

python -m IPython.external.mathjax mathjax-MathJax-v1.1-0-g5a7e4d7.tar.gz
    # says "offline MathJax apparently already installed"

python -m IPython.external.mathjax  ~/mathjax-MathJax-v1.1-0-g5a7e4d7.tar.gz
python -m IPython.external.mathjax -test


"""

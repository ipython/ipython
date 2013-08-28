#!/usr/bin/python
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

To a specific profile:

    $ python -m IPython.external.mathjax --profile=research

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


from IPython.utils.path import locate_profile
from IPython.external import argparse
#-----------------------------------------------------------------------------
#
#-----------------------------------------------------------------------------

# Where mathjax will be installed.

static = os.path.join(locate_profile('default'), 'static')
default_dest = os.path.join(static, 'mathjax')

##

# Test for access to install mathjax.

def check_perms(dest, replace=False):
    parent = os.path.abspath(os.path.join(dest, os.path.pardir))
    components = dest.split(os.path.sep)
    subpaths = [ os.path.sep+os.path.sep.join(components[1:i]) for i in range(1,len(components))]

    existing_path = filter(os.path.exists, subpaths)
    last_writable = existing_path[-1]
    if not os.access(last_writable, os.W_OK):
        raise IOError("Need have write access to %s" % parent)
    not_existing = [ path for path in subpaths if path not in existing_path]
    # subfolder we will create, will obviously be writable
    # should we still considere checking separately that
    # ipython profiles have been created ?
    for folder in not_existing:
        os.mkdir(folder)

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
    parent = os.path.abspath(os.path.join(dest, os.path.pardir))
    tar.extractall(parent)

    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    os.rename(os.path.join(parent, topdir), dest)

##

def extract_zip( fd, dest ) :
    z = zipfile.ZipFile( fd, 'r' )

    # we just happen to know that the first entry in the mathjax
    # archive is the directory that the remaining members are in.
    topdir = z.namelist()[0]

    # extract the archive (contains a single directory) to the static/ directory
    parent = os.path.abspath(os.path.join(dest, os.path.pardir))
    z.extractall( parent )

    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    d = os.path.join(parent, topdir)
    print d
    os.rename(os.path.join(parent, topdir), dest)

##

def install_mathjax(tag='v2.0', dest=default_dest, replace=False, file=None, extractor=extract_tar ):
    """Download and/or install MathJax for offline use.

    This will install mathjax to the 'static' dir in the IPython notebook
    package, so it will fail if the caller does not have write access
    to that location.

    MathJax is a ~15MB download, and ~150MB installed.

    Parameters
    ----------

    replace : bool [False]
        Whether to remove and replace an existing install.
    dest : str [path to default profile]
        Where to locally install mathjax
    tag : str ['v2.0']
        Which tag to download. Default is 'v2.0', the current stable release,
        but alternatives include 'v1.1a' and 'master'.
    file : file like object [ defualt to content of https://github.com/mathjax/MathJax/tarball/#{tag}]
        File handle from which to untar/unzip/... mathjax
    extractor : function
        Method tu use to untar/unzip/... `file`
    """
    if not check_perms(dest, replace) :
        return

    if file is None :
        # download mathjax
        mathjax_url = "https://github.com/mathjax/MathJax/tarball/%s" % tag
        print "Downloading mathjax source from %s" % mathjax_url
        response = urllib2.urlopen(mathjax_url)
        file = response.fp

    print "Extracting to %s" % dest
    extractor( file, dest )

##

def test_func( remove, dest) :
    """See if mathjax appears to be installed correctly"""
    status = 0
    if not os.path.isdir( dest ) :
        print "%s directory not found" % dest
        status = 1
    if not os.path.exists( dest + "/MathJax.js" ) :
        print "MathJax.js not present in %s" % dest
        status = 1
    print "ok"
    if remove and os.path.exists(dest):
        shutil.rmtree( dest )
    return status

##

def main() :
    # This main is just simple enough that it is not worth the
    # complexity of argparse

    # What directory is mathjax in?
    parser = argparse.ArgumentParser(
            description="""Install mathjax from internet or local archive""",
            )

    parser.add_argument(
            '-p',
            '--profile',
            default='default',
            help='profile to install MathJax to (default is default)')

    parser.add_argument(
            '-i',
            '--install-dir',
            help='custom installation directory')

    parser.add_argument(
            '-d',
            '--dest',
            action='store_true',
            help='print where current mathjax would be installed and exit')
    parser.add_argument(
            '-r',
            '--replace',
            action='store_true',
            help='Whether to replace current mathjax if it already exists')
    parser.add_argument(
            '-t',
            '--test',
            action='store_true')
    parser.add_argument('tarball',
            help="the local tar/zip-ball containing mathjax",
            nargs='?',
            metavar='tarball')

    pargs = parser.parse_args()

    if pargs.install_dir:
        # Explicit install_dir overrides profile
        dest = pargs.install_dir
    else:
        profile = pargs.profile
        dest = os.path.join(locate_profile(profile), 'static', 'mathjax')

    if pargs.dest :
        print dest
        return

    # remove/replace existing mathjax?
    if pargs.replace :
        replace = True
    else :
        replace = False

    # undocumented test interface
    if pargs.test :
        return test_func( replace, dest)

    # do it
    if pargs.tarball :
        fname = pargs.tarball

        # automatically detect zip/tar - could do something based
        # on file content, but really not cost-effective here.
        if fname.endswith('.zip') :
            extractor = extract_zip
        else :
            extractor = extract_tar
        # do it
        install_mathjax(file=open(fname, "r"), replace=replace, extractor=extractor, dest=dest )
    else:
        install_mathjax(replace=replace, dest=dest)


if __name__ == '__main__' :
    sys.exit(main())

__all__ = ['install_mathjax', 'main', 'dest']

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

python -m IPython.external.mathjax --test -r

# download and install mathjax from command line:

python -m IPython.external.mathjax
python -m IPython.external.mathjax --test -r

# download and install from within python

python -c "from IPython.external.mathjax import install_mathjax; install_mathjax()"
python -m IPython.external.mathjax --test -r

# view http://www.mathjax.org/download/ in your browser
# save-as the link for MathJax-2.0 near the bottom of the page.
# The file it offers is mathjax-MathJax-v2.0-20-g07669ac.zip

python -m IPython.external.mathjax mathjax-MathJax-v2.0-20-g07669ac.zip
python -m IPython.external.mathjax --test -r

# download https://github.com/mathjax/MathJax/tarball/v2.0 in your browser
# (this is the url used internally by install_mathjax)
# The file it offers is mathjax-MathJax-v2.0-20-g07669ac.tar.gz

python -m IPython.external.mathjax mathjax-MathJax-v2.0-20-g07669ac.tar.gz

python -m IPython.external.mathjax --test
        # note no -r

# install it again while it is already there

python -m IPython.external.mathjax mathjax-MathJax-v2.0-20-g07669ac.tar.gz
    # says "offline MathJax apparently already installed"

python -m IPython.external.mathjax  ~/mathjax-MathJax-v2.0-20-g07669ac.tar.gz
python -m IPython.external.mathjax --test


"""

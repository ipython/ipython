#!/usr/bin/python
"""Utility function for installing MathJax javascript library into
your IPython nbextensions directory, for offline use.

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

To a specific location:

    $ python -m IPython.external.mathjax -i /usr/share/

will install mathjax to /usr/share/mathjax

To install MathJax from a file you have already downloaded:

    $ python -m IPython.external.mathjax mathjax-xxx.tar.gz
    $ python -m IPython.external.mathjax mathjax-xxx.zip

It will not install MathJax if it is already there.  Use -r to
replace the existing copy of MathJax.

To find the directory where IPython would like MathJax installed:

    $ python -m IPython.external.mathjax -d

"""
from __future__ import print_function


#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import argparse
import os
import shutil
import sys
import tarfile
import zipfile

from IPython.paths import get_ipython_dir

try:
    from urllib.request import urlopen # Py 3
except ImportError:
    from urllib2 import urlopen

#-----------------------------------------------------------------------------
#
#-----------------------------------------------------------------------------

# Where mathjax will be installed

nbextensions = os.path.join(get_ipython_dir(), 'nbextensions')
default_dest = os.path.join(nbextensions, 'mathjax')

# Test for access to install mathjax

def prepare_dest(dest, replace=False):
    """prepare the destination folder for mathjax install
    
    Returns False if mathjax appears to already be installed and there is nothing to do,
    True otherwise.
    """
    
    parent = os.path.abspath(os.path.join(dest, os.path.pardir))
    if not os.path.exists(parent):
        os.makedirs(parent)
    
    if os.path.exists(dest):
        if replace:
            print("removing existing MathJax at %s" % dest)
            shutil.rmtree(dest)
            return True
        else:
            mathjax_js = os.path.join(dest, 'MathJax.js')
            if not os.path.exists(mathjax_js):
                raise IOError("%s exists, but does not contain MathJax.js" % dest)
            print("%s already exists" % mathjax_js)
            return False
    else:
        return True


def extract_tar(fd, dest):
    """extract a tarball from filelike `fd` to destination `dest`"""
    # use 'r|gz' stream mode, because socket file-like objects can't seek:
    tar = tarfile.open(fileobj=fd, mode='r|gz')

    # The first entry in the archive is the top-level dir
    topdir = tar.firstmember.path

    # extract the archive (contains a single directory) to the destination directory
    parent = os.path.abspath(os.path.join(dest, os.path.pardir))
    tar.extractall(parent)

    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    os.rename(os.path.join(parent, topdir), dest)


def extract_zip(fd, dest):
    """extract a zip file from filelike `fd` to destination `dest`"""
    z = zipfile.ZipFile(fd, 'r')

    # The first entry in the archive is the top-level dir
    topdir = z.namelist()[0]

    # extract the archive (contains a single directory) to the static/ directory
    parent = os.path.abspath(os.path.join(dest, os.path.pardir))
    z.extractall(parent)

    # it will be mathjax-MathJax-<sha>, rename to just mathjax
    os.rename(os.path.join(parent, topdir), dest)


def install_mathjax(tag='2.4.0', dest=default_dest, replace=False, file=None, extractor=extract_tar):
    """Download and/or install MathJax for offline use.

    This will install mathjax to the nbextensions dir in your IPYTHONDIR.

    MathJax is a ~15MB download, and ~150MB installed.

    Parameters
    ----------

    replace : bool [False]
        Whether to remove and replace an existing install.
    dest : str [IPYTHONDIR/nbextensions/mathjax]
        Where to install mathjax
    tag : str ['2.4.0']
        Which tag to download. Default is '2.4.0', the current stable release,
        but alternatives include 'v1.1a' and 'master'.
    file : file like object [ defualt to content of https://github.com/mathjax/MathJax/tarball/#{tag}]
        File handle from which to untar/unzip/... mathjax
    extractor : function
        Method to use to untar/unzip/... `file`
    """
    try:
        anything_to_do = prepare_dest(dest, replace)
    except OSError as e:
        print("ERROR %s, require write access to %s" % (e, dest))
        return 1
    else:
        if not anything_to_do:
            return 0

    if file is None:
        # download mathjax
        mathjax_url = "https://github.com/mathjax/MathJax/archive/%s.tar.gz" %tag
        print("Downloading mathjax source from %s" % mathjax_url)
        response = urlopen(mathjax_url)
        file = response.fp

    print("Extracting to %s" % dest)
    extractor(file, dest)
    return 0


def main():
    parser = argparse.ArgumentParser(
            description="""Install mathjax from internet or local archive""",
    )

    parser.add_argument(
            '-i',
            '--install-dir',
            default=nbextensions,
            help='custom installation directory. Mathjax will be installed in here/mathjax')

    parser.add_argument(
            '-d',
            '--print-dest',
            action='store_true',
            help='print where mathjax would be installed and exit')
    parser.add_argument(
            '-r',
            '--replace',
            action='store_true',
            help='Whether to replace current mathjax if it already exists')
    parser.add_argument('filename',
            help="the local tar/zip-ball filename containing mathjax",
            nargs='?',
            metavar='filename')

    pargs = parser.parse_args()

    dest = os.path.join(pargs.install_dir, 'mathjax')

    if pargs.print_dest:
        print(dest)
        return

    # remove/replace existing mathjax?
    replace = pargs.replace

    # do it
    if pargs.filename:
        fname = pargs.filename

        # automatically detect zip/tar - could do something based
        # on file content, but really not cost-effective here.
        if fname.endswith('.zip'):
            extractor = extract_zip
        else :
            extractor = extract_tar
        # do it
        return install_mathjax(file=open(fname, "rb"), replace=replace, extractor=extractor, dest=dest)
    else:
        return install_mathjax(replace=replace, dest=dest)


if __name__ == '__main__' :
    sys.exit(main())

__all__ = ['install_mathjax', 'main', 'default_dest']

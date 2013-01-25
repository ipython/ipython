# encoding: utf-8
from __future__ import print_function

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

import sys, os
from textwrap import fill

display_status=True

def check_display(f):
    """decorator to allow display methods to be muted by mod.display_status"""
    def maybe_display(*args, **kwargs):
        if display_status:
            return f(*args, **kwargs)
    return maybe_display

@check_display
def print_line(char='='):
    print(char * 76)

@check_display
def print_status(package, status):
    initial_indent = "%22s: " % package
    indent = ' ' * 24
    print(fill(str(status), width=76,
               initial_indent=initial_indent,
               subsequent_indent=indent))

@check_display
def print_message(message):
    indent = ' ' * 24 + "* "
    print(fill(str(message), width=76,
               initial_indent=indent,
               subsequent_indent=indent))

@check_display
def print_raw(section):
    print(section)

#-------------------------------------------------------------------------------
# Tests for specific packages
#-------------------------------------------------------------------------------

def check_for_ipython():
    try:
        import IPython
    except ImportError:
        print_status("IPython", "Not found")
        return False
    else:
        print_status("IPython", IPython.__version__)
        return True

def check_for_sphinx():
    try:
        import sphinx
    except ImportError:
        print_status('sphinx', "Not found (required for building documentation)")
        return False
    else:
        print_status('sphinx', sphinx.__version__)
        return True

def check_for_pygments():
    try:
        import pygments
    except ImportError:
        print_status('pygments', "Not found (required for syntax highlighting documentation)")
        return False
    else:
        print_status('pygments', pygments.__version__)
        return True

def check_for_nose():
    try:
        import nose
    except ImportError:
        print_status('nose', "Not found (required for running the test suite)")
        return False
    else:
        print_status('nose', nose.__version__)
        return True

def check_for_pexpect():
    try:
        import pexpect
    except ImportError:
        print_status("pexpect", "no (required for running standalone doctests)")
        return False
    else:
        print_status("pexpect", pexpect.__version__)
        return True

def check_for_httplib2():
    try:
        import httplib2
    except ImportError:
        print_status("httplib2", "no (required for blocking http clients)")
        return False
    else:
        print_status("httplib2","yes")
        return True

def check_for_sqlalchemy():
    try:
        import sqlalchemy
    except ImportError:
        print_status("sqlalchemy", "no (required for the ipython1 notebook)")
        return False
    else:
        print_status("sqlalchemy","yes")
        return True

def check_for_simplejson():
    try:
        import simplejson
    except ImportError:
        print_status("simplejson", "no (required for the ipython1 notebook)")
        return False
    else:
        print_status("simplejson","yes")
        return True

def check_for_pyzmq():
    try:
        import zmq
    except ImportError:
        print_status('pyzmq', "no (required for qtconsole, notebook, and parallel computing capabilities)")
        return False
    else:
        # pyzmq 2.1.10 adds pyzmq_version_info funtion for returning
        # version as a tuple
        if hasattr(zmq, 'pyzmq_version_info') and zmq.pyzmq_version_info() >= (2,1,11):
                print_status("pyzmq", zmq.__version__)
                return True
        else:
            print_status('pyzmq', "no (have %s, but require >= 2.1.11 for"
            " qtconsole, notebook, and parallel computing capabilities)" % zmq.__version__)
            return False

def check_for_readline():
    from distutils.version import LooseVersion
    try:
        import readline
    except ImportError:
        try:
            import pyreadline
            vs = pyreadline.release.version
        except (ImportError, AttributeError):
            print_status('readline', "no (required for good interactive behavior)")
            return False
        if LooseVersion(vs).version >= [1,7,1]:
            print_status('readline', "yes pyreadline-" + vs)
            return True
        else:
            print_status('readline', "no pyreadline-%s < 1.7.1" % vs)
            return False
    else:
        print_status('readline', "yes")
        return True

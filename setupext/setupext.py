# encoding: utf-8

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

if display_status:
    def print_line(char='='):
        print char * 76

    def print_status(package, status):
        initial_indent = "%22s: " % package
        indent = ' ' * 24
        print fill(str(status), width=76,
                   initial_indent=initial_indent,
                   subsequent_indent=indent)

    def print_message(message):
        indent = ' ' * 24 + "* "
        print fill(str(message), width=76,
                   initial_indent=indent,
                   subsequent_indent=indent)

    def print_raw(section):
        print section
else:
    def print_line(*args, **kwargs):
        pass
    print_status = print_message = print_raw = print_line

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
        print_status('pyzmq', "no (required for qtconsole and parallel computing capabilities)")
        return False
    else:
        if zmq.__version__ < '2.0.10':
            print_status('pyzmq', "no (require >= 2.0.10 for qtconsole and parallel computing capabilities)")
            
        else:
            print_status("pyzmq", zmq.__version__)
            return True

def check_for_readline():
    try:
        import readline
    except ImportError:
        try:
            import pyreadline
        except ImportError:
            print_status('readline', "no (required for good interactive behavior)")
            return False
        else:
            print_status('readline', "yes pyreadline-"+pyreadline.release.version)
            return True
    else:
        print_status('readline', "yes")
        return True

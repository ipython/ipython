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

def check_for_zopeinterface():
    try:
        import zope.interface
    except ImportError:
        print_status("zope.Interface", "Not found (required for parallel computing capabilities)")
        return False
    else:
        print_status("Zope.Interface","yes")
        return True
        
def check_for_twisted():
    try:
        import twisted
    except ImportError:
        print_status("Twisted", "Not found (required for parallel computing capabilities)")
        return False
    else:
        major = twisted.version.major
        minor = twisted.version.minor
        micro = twisted.version.micro
        print_status("Twisted", twisted.version.short())
        if not ((major==2 and minor>=5 and micro>=0) or \
                major>=8):
            print_message("WARNING: IPython requires Twisted 2.5.0 or greater, you have version %s"%twisted.version.short())
            print_message("Twisted is required for parallel computing capabilities")
            return False
        else:
            return True

def check_for_foolscap():
    try:
        import foolscap
    except ImportError:
        print_status('Foolscap', "Not found (required for parallel computing capabilities)")
        return False
    else:
        print_status('Foolscap', foolscap.__version__)
        return True

def check_for_pyopenssl():
    try:
        import OpenSSL
    except ImportError:
        print_status('OpenSSL', "Not found (required if you want security in the parallel computing capabilities)")
        return False
    else:
        print_status('OpenSSL', OpenSSL.__version__)    
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

        
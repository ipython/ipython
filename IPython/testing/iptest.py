# -*- coding: utf-8 -*-
"""IPython Test Suite Runner.

This module provides a main entry point to a user script to test IPython
itself from the command line. There are two ways of running this script:

1. With the syntax `iptest all`.  This runs our entire test suite by
   calling this script (with different arguments) recursively.  This
   causes modules and package to be tested in different processes, using nose
   or trial where appropriate.
2. With the regular nose syntax, like `iptest -vvs IPython`.  In this form
   the script simply calls nose, but with special command line flags and
   plugins loaded.

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2009-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib
import glob
import os
import os.path as path
import sys
import warnings

# Now, proceed to import nose itself
import nose.plugins.builtin
from nose.plugins.xunit import Xunit
from nose import SkipTest
from nose.core import TestProgram

# Our own imports
from IPython.utils.importstring import import_item
from IPython.utils.path import get_ipython_package_dir
from IPython.utils.warn import warn

from IPython.testing import globalipapp
from IPython.testing.plugin.ipdoctest import IPythonDoctest
from IPython.external.decorators import KnownFailure, knownfailureif

pjoin = path.join


#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Warnings control
#-----------------------------------------------------------------------------

# Twisted generates annoying warnings with Python 2.6, as will do other code
# that imports 'sets' as of today
warnings.filterwarnings('ignore', 'the sets module is deprecated',
                        DeprecationWarning )

# This one also comes from Twisted
warnings.filterwarnings('ignore', 'the sha module is deprecated',
                        DeprecationWarning)

# Wx on Fedora11 spits these out
warnings.filterwarnings('ignore', 'wxPython/wxWidgets release number mismatch',
                        UserWarning)

# ------------------------------------------------------------------------------
# Monkeypatch Xunit to count known failures as skipped.
# ------------------------------------------------------------------------------
def monkeypatch_xunit():
    try:
        knownfailureif(True)(lambda: None)()
    except Exception as e:
        KnownFailureTest = type(e)

    def addError(self, test, err, capt=None):
        if issubclass(err[0], KnownFailureTest):
            err = (SkipTest,) + err[1:]
        return self.orig_addError(test, err, capt)

    Xunit.orig_addError = Xunit.addError
    Xunit.addError = addError

#-----------------------------------------------------------------------------
# Logic for skipping doctests
#-----------------------------------------------------------------------------
def extract_version(mod):
    return mod.__version__

def test_for(item, min_version=None, callback=extract_version):
    """Test to see if item is importable, and optionally check against a minimum
    version.

    If min_version is given, the default behavior is to check against the
    `__version__` attribute of the item, but specifying `callback` allows you to
    extract the value you are interested in. e.g::

        In [1]: import sys

        In [2]: from IPython.testing.iptest import test_for

        In [3]: test_for('sys', (2,6), callback=lambda sys: sys.version_info)
        Out[3]: True

    """
    try:
        check = import_item(item)
    except (ImportError, RuntimeError):
        # GTK reports Runtime error if it can't be initialized even if it's
        # importable.
        return False
    else:
        if min_version:
            if callback:
                # extra processing step to get version to compare
                check = callback(check)

            return check >= min_version
        else:
            return True

# Global dict where we can store information on what we have and what we don't
# have available at test run time
have = {}

have['curses'] = test_for('_curses')
have['matplotlib'] = test_for('matplotlib')
have['numpy'] = test_for('numpy')
have['pexpect'] = test_for('IPython.external.pexpect')
have['pymongo'] = test_for('pymongo')
have['pygments'] = test_for('pygments')
have['qt'] = test_for('IPython.external.qt')
have['rpy2'] = test_for('rpy2')
have['sqlite3'] = test_for('sqlite3')
have['cython'] = test_for('Cython')
have['oct2py'] = test_for('oct2py')
have['tornado'] = test_for('tornado.version_info', (2,1,0), callback=None)
have['jinja2'] = test_for('jinja2')
have['wx'] = test_for('wx')
have['wx.aui'] = test_for('wx.aui')
have['azure'] = test_for('azure')
have['sphinx'] = test_for('sphinx')

min_zmq = (2,1,11)

have['zmq'] = test_for('zmq.pyzmq_version_info', min_zmq, callback=lambda x: x())

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------


def make_exclude():
    """Make patterns of modules and packages to exclude from testing.

    For the IPythonDoctest plugin, we need to exclude certain patterns that
    cause testing problems.  We should strive to minimize the number of
    skipped modules, since this means untested code.

    These modules and packages will NOT get scanned by nose at all for tests.
    """
    # Simple utility to make IPython paths more readably, we need a lot of
    # these below
    ipjoin = lambda *paths: pjoin('IPython', *paths)

    exclusions = [ipjoin('external'),
                  ipjoin('quarantine'),
                  ipjoin('deathrow'),
                  # This guy is probably attic material
                  ipjoin('testing', 'mkdoctests'),
                  # Testing inputhook will need a lot of thought, to figure out
                  # how to have tests that don't lock up with the gui event
                  # loops in the picture
                  ipjoin('lib', 'inputhook'),
                  # Config files aren't really importable stand-alone
                  ipjoin('config', 'profile'),
                  # The notebook 'static' directory contains JS, css and other
                  # files for web serving.  Occasionally projects may put a .py
                  # file in there (MathJax ships a conf.py), so we might as
                  # well play it safe and skip the whole thing.
                  ipjoin('html', 'static'),
                  ipjoin('html', 'fabfile'),
                  ]
    if not have['sqlite3']:
        exclusions.append(ipjoin('core', 'tests', 'test_history'))
        exclusions.append(ipjoin('core', 'history'))
    if not have['wx']:
        exclusions.append(ipjoin('lib', 'inputhookwx'))
    
    if 'IPython.kernel.inprocess' not in sys.argv:
        exclusions.append(ipjoin('kernel', 'inprocess'))
    
    # FIXME: temporarily disable autoreload tests, as they can produce
    # spurious failures in subsequent tests (cythonmagic).
    exclusions.append(ipjoin('extensions', 'autoreload'))
    exclusions.append(ipjoin('extensions', 'tests', 'test_autoreload'))

    # We do this unconditionally, so that the test suite doesn't import
    # gtk, changing the default encoding and masking some unicode bugs.
    exclusions.append(ipjoin('lib', 'inputhookgtk'))
    exclusions.append(ipjoin('kernel', 'zmq', 'gui', 'gtkembed'))

    #Also done unconditionally, exclude nbconvert directories containing
    #config files used to test.  Executing the config files with iptest would
    #cause an exception.
    exclusions.append(ipjoin('nbconvert', 'tests', 'files'))
    exclusions.append(ipjoin('nbconvert', 'exporters', 'tests', 'files'))

    # These have to be skipped on win32 because the use echo, rm, cd, etc.
    # See ticket https://github.com/ipython/ipython/issues/87
    if sys.platform == 'win32':
        exclusions.append(ipjoin('testing', 'plugin', 'test_exampleip'))
        exclusions.append(ipjoin('testing', 'plugin', 'dtexample'))

    if not have['pexpect']:
        exclusions.extend([ipjoin('lib', 'irunner'),
                           ipjoin('lib', 'tests', 'test_irunner'),
                           ipjoin('terminal', 'console'),
                           ])

    if not have['zmq']:
        exclusions.append(ipjoin('lib', 'kernel'))
        exclusions.append(ipjoin('kernel'))
        exclusions.append(ipjoin('qt'))
        exclusions.append(ipjoin('html'))
        exclusions.append(ipjoin('consoleapp.py'))
        exclusions.append(ipjoin('terminal', 'console'))
        exclusions.append(ipjoin('parallel'))
    elif not have['qt'] or not have['pygments']:
        exclusions.append(ipjoin('qt'))

    if not have['pymongo']:
        exclusions.append(ipjoin('parallel', 'controller', 'mongodb'))
        exclusions.append(ipjoin('parallel', 'tests', 'test_mongodb'))

    if not have['matplotlib']:
        exclusions.extend([ipjoin('core', 'pylabtools'),
                           ipjoin('core', 'tests', 'test_pylabtools'),
                           ipjoin('kernel', 'zmq', 'pylab'),
        ])

    if not have['cython']:
        exclusions.extend([ipjoin('extensions', 'cythonmagic')])
        exclusions.extend([ipjoin('extensions', 'tests', 'test_cythonmagic')])

    if not have['oct2py']:
        exclusions.extend([ipjoin('extensions', 'octavemagic')])
        exclusions.extend([ipjoin('extensions', 'tests', 'test_octavemagic')])

    if not have['tornado']:
        exclusions.append(ipjoin('html'))
        exclusions.append(ipjoin('nbconvert', 'post_processors', 'serve'))
        exclusions.append(ipjoin('nbconvert', 'post_processors', 'tests', 'test_serve'))

    if not have['jinja2']:
        exclusions.append(ipjoin('html', 'notebookapp'))

    if not have['rpy2'] or not have['numpy']:
        exclusions.append(ipjoin('extensions', 'rmagic'))
        exclusions.append(ipjoin('extensions', 'tests', 'test_rmagic'))

    if not have['azure']:
        exclusions.append(ipjoin('html', 'services', 'notebooks', 'azurenbmanager'))

    if not all((have['pygments'], have['jinja2'], have['sphinx'])):
        exclusions.append(ipjoin('nbconvert'))

    # This is needed for the reg-exp to match on win32 in the ipdoctest plugin.
    if sys.platform == 'win32':
        exclusions = [s.replace('\\','\\\\') for s in exclusions]
    
    # check for any exclusions that don't seem to exist:
    parent, _ = os.path.split(get_ipython_package_dir())
    for exclusion in exclusions:
        if exclusion.endswith(('deathrow', 'quarantine')):
            # ignore deathrow/quarantine, which exist in dev, but not install
            continue
        fullpath = pjoin(parent, exclusion)
        if not os.path.exists(fullpath) and not glob.glob(fullpath + '.*'):
            warn("Excluding nonexistent file: %r" % exclusion)

    return exclusions

special_test_suites = {
    'autoreload': ['IPython.extensions.autoreload', 'IPython.extensions.tests.test_autoreload'],
}


def run_iptest():
    """Run the IPython test suite using nose.

    This function is called when this script is **not** called with the form
    `iptest all`.  It simply calls nose with appropriate command line flags
    and accepts all of the standard nose arguments.
    """
    # Apply our monkeypatch to Xunit
    if '--with-xunit' in sys.argv and not hasattr(Xunit, 'orig_addError'):
        monkeypatch_xunit()

    warnings.filterwarnings('ignore',
        'This will be removed soon.  Use IPython.testing.util instead')
    
    if sys.argv[1] in special_test_suites:
        sys.argv[1:2] = special_test_suites[sys.argv[1]]
        special_suite = True
    else:
        special_suite = False

    argv = sys.argv + [ '--detailed-errors',  # extra info in tracebacks

                        '--with-ipdoctest',
                        '--ipdoctest-tests','--ipdoctest-extension=txt',

                        # We add --exe because of setuptools' imbecility (it
                        # blindly does chmod +x on ALL files).  Nose does the
                        # right thing and it tries to avoid executables,
                        # setuptools unfortunately forces our hand here.  This
                        # has been discussed on the distutils list and the
                        # setuptools devs refuse to fix this problem!
                        '--exe',
                        ]
    if '-a' not in argv and '-A' not in argv:
        argv = argv + ['-a', '!crash']

    if nose.__version__ >= '0.11':
        # I don't fully understand why we need this one, but depending on what
        # directory the test suite is run from, if we don't give it, 0 tests
        # get run.  Specifically, if the test suite is run from the source dir
        # with an argument (like 'iptest.py IPython.core', 0 tests are run,
        # even if the same call done in this directory works fine).  It appears
        # that if the requested package is in the current dir, nose bails early
        # by default.  Since it's otherwise harmless, leave it in by default
        # for nose >= 0.11, though unfortunately nose 0.10 doesn't support it.
        argv.append('--traverse-namespace')

    # use our plugin for doctesting.  It will remove the standard doctest plugin
    # if it finds it enabled
    ipdt = IPythonDoctest() if special_suite else IPythonDoctest(make_exclude())
    plugins = [ipdt, KnownFailure()]
    
    # We need a global ipython running in this process, but the special
    # in-process group spawns its own IPython kernels, so for *that* group we
    # must avoid also opening the global one (otherwise there's a conflict of
    # singletons).  Ultimately the solution to this problem is to refactor our
    # assumptions about what needs to be a singleton and what doesn't (app
    # objects should, individual shells shouldn't).  But for now, this
    # workaround allows the test suite for the inprocess module to complete.
    if not 'IPython.kernel.inprocess' in sys.argv:
        globalipapp.start_ipython()

    # Now nose can run
    TestProgram(argv=argv, addplugins=plugins)


if __name__ == '__main__':
    run_iptest()

"""test the IPython Kernel"""

#-------------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os
import shutil
import sys
import tempfile

import nose.tools as nt

from IPython.testing import decorators as dec
from IPython.utils import path, py3compat

from .utils import new_kernel, kernel, TIMEOUT, assemble_output, execute, flush_channels

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------
IPYTHONDIR = None
save_env = None
save_get_ipython_dir = None

def setup():
    """setup temporary IPYTHONDIR for tests"""
    global IPYTHONDIR
    global save_env
    global save_get_ipython_dir
    
    IPYTHONDIR = tempfile.mkdtemp()

    save_env = os.environ.copy()
    os.environ["IPYTHONDIR"] = IPYTHONDIR

    save_get_ipython_dir = path.get_ipython_dir
    path.get_ipython_dir = lambda : IPYTHONDIR
    print 'setup'


def teardown():
    print 'tearing down'
    path.get_ipython_dir = save_get_ipython_dir
    os.environ = save_env
    
    try:
        shutil.rmtree(IPYTHONDIR)
    except (OSError, IOError):
        # no such file
        pass

"""Little utilities for testing tconfig.

This module is meant to be used via

import sctst; reload(sctst)
from sctst import *

at the top of the actual test scripts, so that they all get the entire set of
common test tools with minimal fuss.
"""

# Standard library imports
import os
import sys
from pprint import pprint

# Our own imports.

from IPython.config import sconfig
reload(sconfig)

from sconfig import mkConfigObj, RecursiveConfigObj, SConfigManager, \
     sconf2file

# Simple utilities/classes for testing

def cat(fname):
    print '### FILENAME:',fname
    print open(fname).read()


class App(object):
    """A trivial 'application' class to be initialized.
    """
    def __init__(self,config_class,config_filename):
        self.rcman = SConfigManager(config_class,config_filename)
        self.rc = self.rcman.sconf

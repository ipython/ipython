"""Common utilities for testing IPython.

This file is meant to be used as

from IPython.testing.tcommon import *

by any test code.

While a bit ugly, this helps us keep all testing facilities in one place, and
start coding standalone test scripts easily, which can then be pasted into the
larger test suites without any modifications required.
"""

# Required modules and packages

# Standard Python lib
import cPickle as pickle
import doctest
import math
import os
import sys
import unittest

from pprint import pformat, pprint

# From the IPython test lib
import tutils
from tutils import fullPath

try:
    import pexpect
except ImportError:
    pexpect = None
else:
    from IPython.testing.ipdoctest import IPDocTestLoader,makeTestSuite
    

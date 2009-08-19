#!/usr/bin/env python
# encoding: utf-8
"""
IPython.

IPython is a set of tools for interactive and exploratory computing in Python.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
from IPython.core import release

#-----------------------------------------------------------------------------
# Setup everything
#-----------------------------------------------------------------------------


if sys.version[0:3] < '2.4':
    raise ImportError('Python Version 2.4 or above is required for IPython.')


# Make it easy to import extensions - they are always directly on pythonpath.
# Therefore, non-IPython modules can be added to extensions directory
sys.path.append(os.path.join(os.path.dirname(__file__), "extensions"))

from IPython.core import iplib


# Release data
__author__ = ''
for author, email in release.authors.values():
    __author__ += author + ' <' + email + '>\n'
__license__  = release.license
__version__  = release.version
__revision__ = release.revision


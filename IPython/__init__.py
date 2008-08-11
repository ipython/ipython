# -*- coding: utf-8 -*-
"""
IPython -- An enhanced Interactive Python

One of Python's nicest features is its interactive interpreter. This allows
very fast testing of ideas without the overhead of creating test files as is
typical in most programming languages. However, the interpreter supplied with
the standard Python distribution is fairly primitive (and IDLE isn't really
much better).

IPython tries to:

  i - provide an efficient environment for interactive work in Python
  programming. It tries to address what we see as shortcomings of the standard
  Python prompt, and adds many features to make interactive work much more
  efficient.

  ii - offer a flexible framework so that it can be used as the base
  environment for other projects and problems where Python can be the
  underlying language. Specifically scientific environments like Mathematica,
  IDL and Mathcad inspired its design, but similar ideas can be useful in many
  fields. Python is a fabulous language for implementing this kind of system
  (due to its dynamic and introspective features), and with suitable libraries
  entire systems could be built leveraging Python's power.

  iii - serve as an embeddable, ready to go interpreter for your own programs.

IPython requires Python 2.3 or newer.

$Id: __init__.py 2399 2007-05-26 10:23:10Z vivainio $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# Enforce proper version requirements
import sys

if sys.version[0:3] < '2.4':
    raise ImportError('Python Version 2.4 or above is required for IPython.')

# Make it easy to import extensions - they are always directly on pythonpath.
# Therefore, non-IPython modules can be added to Extensions directory
import os
sys.path.append(os.path.dirname(__file__) + "/Extensions")

# Define what gets imported with a 'from IPython import *'
__all__ = ['ipapi','generics','ipstruct','Release','Shell']

# Load __all__ in IPython namespace so that a simple 'import IPython' gives
# access to them via IPython.<name>
glob,loc = globals(),locals()
for name in __all__:
    #print 'Importing: ',name # dbg
    __import__(name,glob,loc,[])

import Shell

# Release data
from IPython import Release # do it explicitly so pydoc can see it - pydoc bug
__author__   = '%s <%s>\n%s <%s>\n%s <%s>' % \
               ( Release.authors['Fernando'] + Release.authors['Janko'] + \
                 Release.authors['Nathan'] )
__license__  = Release.license
__version__  = Release.version
__revision__ = Release.revision

# Namespace cleanup
del name,glob,loc

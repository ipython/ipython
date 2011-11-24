"""Wrap zmq's jsonapi and work around api incompatibilities.

This file is effectively a replacement for zmq.utils.jsonapi, that works around
incompatibilities between jsonlib and the stdlib json, such as the
interpretation of the 'indent' keyword in dumps().
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from zmq.utils import jsonapi as _json
from zmq.utils.jsonapi import *

#-----------------------------------------------------------------------------
# Function definitions
#-----------------------------------------------------------------------------
try:
    _json.dumps(1, indent=2)
except TypeError:
    # This happens with jsonlib, which takes indent as a string instead of as
    # an int.
    def dumps(o, **kw):
        if 'indent' in kw:
            indent = kw.pop('indent')
            if isinstance(indent, int):
                indent = ' ' * indent
            kw['indent'] = indent
            
        return _json.dumps(o, **kw)

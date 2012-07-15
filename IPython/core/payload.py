# -*- coding: utf-8 -*-
"""Payload system for IPython.

Authors:

* Fernando Perez
* Brian Granger
"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2008-2011 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import List

#-----------------------------------------------------------------------------
# Main payload class
#-----------------------------------------------------------------------------

class PayloadManager(Configurable):

    _payload = List([])

    def write_payload(self, data):
        if not isinstance(data, dict):
            raise TypeError('Each payload write must be a dict, got: %r' % data)
        self._payload.append(data)

    def read_payload(self):
        return self._payload

    def clear_payload(self):
        self._payload = []

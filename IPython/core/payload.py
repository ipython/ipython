# -*- coding: utf-8 -*-
"""Payload system for IPython.

Authors:

* Fernando Perez
* Brian Granger
"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2008-2010 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Dict

#-----------------------------------------------------------------------------
# Main payload class
#-----------------------------------------------------------------------------

class PayloadManager(Configurable):

    _payload = Dict({})

    def write_payload(self, key, value):
        self.payload[key] = value

    def reset_payload(self):
        self.payload = {}

    def read_payload(self):
        return self._payload

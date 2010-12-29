# -*- coding: utf-8 -*-
"""An interface for publishing data related to the display of objects.

Authors:

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

#-----------------------------------------------------------------------------
# Main payload class
#-----------------------------------------------------------------------------

class DisplayPublisher(Configurable):

    def _validate_data(self, source, data, metadata=None):
        if not isinstance(source, str):
            raise TypeError('source must be a str, got: %r' % source)
        if not isinstance(data, dict):
            raise TypeError('data must be a dict, got: %r' % data)
        if metadata is not None:
            if not isinstance(metadata, dict):
                raise TypeError('metadata must be a dict, got: %r' % data)

    def publish(self, source, data, metadata=None):
        """Publish data and metadata to all frontends."""
        pass


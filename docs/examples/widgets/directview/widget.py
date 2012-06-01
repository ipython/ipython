"""Python support code for JavaScript based widgets.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import uuid

from IPython.core.display import display, Javascript

from zmq.utils import jsonapi

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------



class JavascriptWidget(object):

    jslibs = []
    
    def __init__(self):
        self.widget_id = unicode(uuid.uuid4()).replace('-','')
        self.widget_var = '__widget_%s' % self.widget_id
        ns = get_ipython().user_ns
        ns[self.widget_var] = self

    def encode_json(self, o):
        return jsonapi.dumps(o)

    def decode_json(self, s):
        return jsonapi.loads(s)

    def interact(self):
        """This should call display(Javascript(jscode))."""
        jscode = self.render()
        display(Javascript(data=jscode,lib=self.jslibs))

    def render(self):
        """Return the final JavaScript code that will be eval'd in the client."""
        raise NotImplementedError('render is not implemented in this base class')




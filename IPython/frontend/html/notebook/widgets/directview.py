"""Widget for interacting with an IPython parallel engine.

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
from IPython.core.displaypub import publish_pretty


#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


import os, sys
from IPython.core.display import Javascript

from .widget import JavascriptWidget


class DirectViewWidget(JavascriptWidget):

    def __init__(self, dv):
        self.dv = dv
        self.targets = self.dv.targets
        super(DirectViewWidget,self).__init__()

    def render(self):
        jscode = self.load_file(u'directview.js')
        data = {
            'widget_var': self.widget_var,
            'targets' : self.encode_json(self.targets)
        }
        jscode = jscode % data
        return jscode

    def execute(self,code):
        ar = self.dv.execute(code,block=False,targets='all')
        ar.wait()
        metadata = ar.metadata
        for md in metadata:
            if md['stdout']:
                publish_pretty(md['stdout'],{'engine_id':md['engine_id']})
            if md['stderr']:
                publish_pretty(md['stderr'],{'engine_id':md['engine_id']})
            if md['pyerr']:
                publish_pretty(md['pyerr'],{'engine_id':md['engine_id']})



def interact(dv):
    w = DirectViewWidget(dv)
    w.interact()
    return w



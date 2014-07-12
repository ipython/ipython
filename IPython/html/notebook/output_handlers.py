"""Tornado handlers for the output iframes for the live notebook view.

Authors:

* Keter Tong
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2014  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
from tornado import web
HTTPError = web.HTTPError

from ..base.handlers import IPythonHandler, notebook_path_regex, path_regex
from ..utils import url_path_join, url_escape

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class OutputFrameHandler(IPythonHandler):

    @web.authenticated
    def get(self, path='', name=None):
        """get renders the output iframe template."""
        nbm = self.notebook_manager
        self.write(self.render_template('outputframe.html',
            mathjax_url=self.mathjax_url,
            )
        )

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/outputframe", OutputFrameHandler)
]


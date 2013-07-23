"""Tornado handlers for the tree view.

Authors:

* Brian Granger
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

from tornado import web
from ..base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class ProjectDashboardHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        self.write(self.render_template('tree.html',
            project=self.project,
            project_component=self.project.split('/'),
        ))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [(r"/", ProjectDashboardHandler)]
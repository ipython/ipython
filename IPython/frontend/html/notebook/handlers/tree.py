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

from .base import IPythonHandler, authenticate_unless_readonly

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class ProjectDashboardHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self):
        self.write(self.render_template('projectdashboard.html',
            project=self.project,
            project_component=self.project.split('/'),
        ))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [(r"/", ProjectDashboardHandler)]
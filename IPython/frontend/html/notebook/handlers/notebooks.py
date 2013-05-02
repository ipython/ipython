"""Tornado handlers for the live notebook view.

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

import os
from tornado import web
HTTPError = web.HTTPError

from .base import IPythonHandler, authenticate_unless_readonly
from ..utils import url_path_join

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class NewHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        notebook_id = self.notebook_manager.new_notebook()
        self.redirect('/' + url_path_join(self.base_project_url, notebook_id))


class NamedNotebookHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self, notebook_id):
        nbm = self.notebook_manager
        if not nbm.notebook_exists(notebook_id):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)       
        self.write(self.render_template('notebook.html',
            project=self.project,
            notebook_id=notebook_id,
            kill_kernel=False,
            mathjax_url=self.mathjax_url,
            )
        )


class NotebookRedirectHandler(IPythonHandler):
    
    @authenticate_unless_readonly
    def get(self, notebook_name):
        # strip trailing .ipynb:
        notebook_name = os.path.splitext(notebook_name)[0]
        notebook_id = self.notebook_manager.rev_mapping.get(notebook_name, '')
        if notebook_id:
            url = self.settings.get('base_project_url', '/') + notebook_id
            return self.redirect(url)
        else:
            raise HTTPError(404)


class NotebookCopyHandler(IPythonHandler):

    @web.authenticated
    def get(self, notebook_id):
        notebook_id = self.notebook_manager.copy_notebook(notebook_id)
        self.redirect('/'+url_path_join(self.base_project_url, notebook_id))


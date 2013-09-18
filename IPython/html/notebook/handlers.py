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

from ..base.handlers import IPythonHandler
from ..utils import url_path_join

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class NewHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        notebook_id = self.notebook_manager.new_notebook()
        self.redirect(url_path_join(self.base_project_url, notebook_id))


class NamedNotebookHandler(IPythonHandler):

    @web.authenticated
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
    
    @web.authenticated
    def get(self, notebook_name):
        # strip trailing .ipynb:
        notebook_name = os.path.splitext(notebook_name)[0]
        notebook_id = self.notebook_manager.rev_mapping.get(notebook_name, '')
        if notebook_id:
            url = url_path_join(self.settings.get('base_project_url', '/'), notebook_id)
            return self.redirect(url)
        else:
            raise HTTPError(404)


class NotebookCopyHandler(IPythonHandler):

    @web.authenticated
    def get(self, notebook_id):
        notebook_id = self.notebook_manager.copy_notebook(notebook_id)
        self.redirect(url_path_join(self.base_project_url, notebook_id))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_id_regex = r"(?P<notebook_id>\w+-\w+-\w+-\w+-\w+)"
_notebook_name_regex = r"(?P<notebook_name>.+\.ipynb)"

default_handlers = [
    (r"/new", NewHandler),
    (r"/%s" % _notebook_id_regex, NamedNotebookHandler),
    (r"/%s" % _notebook_name_regex, NotebookRedirectHandler),
    (r"/%s/copy" % _notebook_id_regex, NotebookCopyHandler),

]

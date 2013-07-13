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


class NewPathHandler(IPythonHandler):
    
    @web.authenticated
    def get(self, notebook_path):
        notebook_name = self.notebook_manager.new_notebook(notebook_path)
        self.redirect(url_path_join(self.base_project_url,"notebooks", notebook_path, notebook_name))
        

class NewHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        notebook_name = self.notebook_manager.new_notebook()
        self.redirect(url_path_join(self.base_project_url, "notebooks", notebook_name))


class NamedNotebookHandler(IPythonHandler):

    @web.authenticated
    def get(self, notebook_path):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        if path == None:
            project = self.project + '/' + name
        else:
            project = self.project + '/' + path +'/'+ name
        #if not nbm.notebook_exists(notebook_path):
         #   raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_path)       
        self.write(self.render_template('notebook.html',
            project=project,
            notebook_path=path,
            notebook_name=name,
            kill_kernel=False,
            mathjax_url=self.mathjax_url,
            )
        )


class NotebookCopyHandler(IPythonHandler):

    @web.authenticated
    def get(self, notebook_path=None):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        notebook_name = self.notebook_manager.copy_notebook(name, path)
        if path==None:
            self.redirect(url_path_join(self.base_project_url, "notebooks", notebook_name))
        else:
            self.redirect(url_path_join(self.base_project_url, "notebooks", path, notebook_name))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_path_regex = r"(?P<notebook_path>.+)"

default_handlers = [
    (r"/notebooks/%s/new" % _notebook_path_regex, NewPathHandler),
    (r"/notebooks/new", NewHandler),
    (r"/notebooks/%s/copy" % _notebook_path_regex, NotebookCopyHandler),
    (r"/notebooks/%s" % _notebook_path_regex, NamedNotebookHandler)
]

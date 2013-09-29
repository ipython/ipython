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
from zmq.utils import jsonapi


from ..base.handlers import IPythonHandler
from ..utils import url_path_join
from urllib import quote

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class NotebookHandler(IPythonHandler):

    @web.authenticated
    def post(self):
        """post either creates a new notebook if no json data is
        sent to the server, or copies the data and returns a 
        copied notebook."""
        nbm = self.notebook_manager
        data=self.request.body
        if data:
            data = jsonapi.loads(data)
            notebook_name = nbm.copy_notebook(data['name'])
        else:
            notebook_name = nbm.new_notebook()
        self.finish(jsonapi.dumps({"name": notebook_name}))


class NamedNotebookHandler(IPythonHandler):

    @web.authenticated
    def get(self, notebook_path):
        """get renders the notebook template if a name is given, or 
        redirects to the '/files/' handler if the name is not given."""
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        if name is not None:
            # a .ipynb filename was given
            if not nbm.notebook_exists(name, path):
                raise web.HTTPError(404, u'Notebook does not exist: %s' % name)
            name = nbm.url_encode(name)
            path = nbm.url_encode(path)
            self.write(self.render_template('notebook.html',
                project=self.project_dir,
                notebook_path=path,
                notebook_name=name,
                kill_kernel=False,
                mathjax_url=self.mathjax_url,
                )
            )
        else:
            url = "/files/" + notebook_path
            self.redirect(url)
            

    @web.authenticated
    def post(self, notebook_path):
        """post either creates a new notebook if no json data is
        sent to the server, or copies the data and returns a 
        copied notebook in the location given by 'notebook_path."""
        nbm = self.notebook_manager
        data = self.request.body
        if data:
            data = jsonapi.loads(data)
            notebook_name = nbm.copy_notebook(data['name'], notebook_path)
        else:
            notebook_name = nbm.new_notebook(notebook_path)
        self.finish(jsonapi.dumps({"name": notebook_name}))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_path_regex = r"(?P<notebook_path>.+)"

default_handlers = [
    (r"/notebooks/%s" % _notebook_path_regex, NamedNotebookHandler),
    (r"/notebooks/", NotebookHandler),
]


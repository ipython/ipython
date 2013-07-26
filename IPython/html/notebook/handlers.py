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
        nbm = self.notebook_manager
        data=self.request.body
        if data == "":
            notebook_name = nbm.new_notebook()
        else:
            data = jsonapi.loads(data)
            notebook_name = nbm.copy_notebook(data['name'])
        self.finish(jsonapi.dumps({"name": notebook_name}))


class NamedNotebookHandler(IPythonHandler):

    @web.authenticated
    def get(self, notebook_path):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        if name != None:
            name = nbm.url_encode(name)
        if path == None:
            project = self.project + '/' + name
        else:
            project = self.project + '/' + path +'/'+ name
            path = nbm.url_encode(path)
        if not nbm.notebook_exists(notebook_path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % name)
        self.write(self.render_template('notebook.html',
            project=project,
            notebook_path=path,
            notebook_name=name,
            kill_kernel=False,
            mathjax_url=self.mathjax_url,
            )
        )

    @web.authenticated
    def post(self, notebook_path):
        nbm = self.notebook_manager
        data = self.request.body
        if data == "":
            notebook_name = nbm.new_notebook(notebook_path)
        else:
            data = jsonapi.loads(data)
            notebook_name = nbm.copy_notebook(data['name'], notebook_path)
        self.finish(jsonapi.dumps({"name": notebook_name}))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_path_regex = r"(?P<notebook_path>.+)"

default_handlers = [
    (r"/notebooks/%s" % _notebook_path_regex, NamedNotebookHandler),
    (r"/notebooks/", NotebookHandler)
]

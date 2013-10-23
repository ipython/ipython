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
import json

from tornado import web
HTTPError = web.HTTPError

from ..base.handlers import IPythonHandler
from ..services.notebooks.handlers import _notebook_path_regex, _path_regex
from ..utils import url_path_join, url_escape, url_unescape
from urllib import quote

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class NotebookHandler(IPythonHandler):

    @web.authenticated
    def get(self, path='', name=None):
        """get renders the notebook template if a name is given, or 
        redirects to the '/files/' handler if the name is not given."""
        path = path.strip('/')
        nbm = self.notebook_manager
        if name is None:
            raise web.HTTPError(500, "This shouldn't be accessible: %s" % self.request.uri)
        
        # a .ipynb filename was given
        if not nbm.notebook_exists(name, path):
            raise web.HTTPError(404, u'Notebook does not exist: %s/%s' % (path, name))
        name = url_escape(name)
        path = url_escape(path)
        self.write(self.render_template('notebook.html',
            project=self.project_dir,
            notebook_path=path,
            notebook_name=name,
            kill_kernel=False,
            mathjax_url=self.mathjax_url,
            )
        )

class NotebookRedirectHandler(IPythonHandler):
    def get(self, path=''):
        nbm = self.notebook_manager
        if nbm.path_exists(path):
            # it's a *directory*, redirect to /tree
            url = url_path_join(self.base_project_url, 'tree', path)
        else:
            # otherwise, redirect to /files
            # TODO: This should check if it's actually a file
            url = url_path_join(self.base_project_url, 'files', path)
        url = url_escape(url)
        self.log.debug("Redirecting %s to %s", self.request.path, url)
        self.redirect(url)

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/notebooks%s" % _notebook_path_regex, NotebookHandler),
    (r"/notebooks%s" % _path_regex, NotebookRedirectHandler),
]


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
import os

from tornado import web
from ..base.handlers import IPythonHandler
from ..utils import url_path_join, path2url, url2path
from ..services.notebooks.handlers import _notebook_path_regex, _path_regex

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class TreeHandler(IPythonHandler):
    """Render the tree view, listing notebooks, clusters, etc."""

    @web.authenticated
    def get(self, path='', name=None):
        nbm = self.notebook_manager
        if name is not None:
            # is a notebook, redirect to notebook handler
            url = url_path_join(self.base_project_url, 'notebooks', path, name)
            self.redirect(url)
        else:
            if not nbm.path_exists(path=path):
                # no such directory, 404
                raise web.HTTPError(404)
            self.write(self.render_template('tree.html',
                project=self.project_dir,
                tree_url_path=path,
                notebook_path=path,
            ))


class TreeRedirectHandler(IPythonHandler):
    """Redirect a request to the corresponding tree URL"""

    @web.authenticated
    def get(self, path=''):
        url = url_path_join(self.base_project_url, 'tree', path).rstrip('/')
        self.log.debug("Redirecting %s to %s", self.request.uri, url)
        self.redirect(url)


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/tree%s" % _notebook_path_regex, TreeHandler),
    (r"/tree%s" % _path_regex, TreeHandler),
    (r"/tree", TreeHandler),
    (r"/", TreeRedirectHandler),
    ]

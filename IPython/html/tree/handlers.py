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
from ..base.handlers import IPythonHandler, notebook_path_regex, path_regex
from ..utils import url_path_join, path2url, url2path, url_escape

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class TreeHandler(IPythonHandler):
    """Render the tree view, listing notebooks, clusters, etc."""

    @web.authenticated
    def get(self, path='', name=None):
        path = path.strip('/')
        nbm = self.notebook_manager
        if name is not None:
            # is a notebook, redirect to notebook handler
            url = url_escape(url_path_join(
                self.base_project_url, 'notebooks', path, name
            ))
            self.log.debug("Redirecting %s to %s", self.request.path, url)
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
        url = url_escape(url_path_join(
            self.base_project_url, 'tree', path.strip('/')
        ))
        self.log.debug("Redirecting %s to %s", self.request.path, url)
        self.redirect(url)


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/tree%s" % notebook_path_regex, TreeHandler),
    (r"/tree%s" % path_regex, TreeHandler),
    (r"/tree", TreeHandler),
    (r"/", TreeRedirectHandler),
    ]

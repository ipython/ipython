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

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class TreeHandler(IPythonHandler):
    """Render the tree view, listing notebooks, clusters, etc."""

    @web.authenticated
    def get(self, notebook_path=""):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        if name is not None:
            # is a notebook, redirect to notebook handler
            url = url_path_join(self.base_project_url, 'notebooks', path, name)
            self.redirect(url)
        else:
            location = nbm.get_os_path(path=path)
            
            if not os.path.exists(location):
                # no such directory, 404
                raise web.HTTPError(404)
            
            self.write(self.render_template('tree.html',
                project=self.project_dir,
                tree_url_path=path2url(location),
                notebook_path=path,
            ))


class TreeRedirectHandler(IPythonHandler):
    """Redirect a request to the corresponding tree URL"""

    @web.authenticated
    def get(self, notebook_path=''):
        url = url_path_join(self.base_project_url, 'tree', notebook_path)
        self.log.debug("Redirecting %s to %s", self.request.uri, url)
        self.redirect(url)


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_path_regex = r"(?P<notebook_path>.+)"

default_handlers = [
    (r"/tree/%s/" % _notebook_path_regex, TreeRedirectHandler),
    (r"/tree/%s" % _notebook_path_regex, TreeHandler),
    (r"/tree/", TreeRedirectHandler),
    (r"/tree", TreeHandler),
    (r"/", TreeRedirectHandler),
    ]

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

from ..base.handlers import IPythonHandler, notebook_path_regex, path_regex
from ..utils import url_path_join, url_escape

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
            url = url_path_join(self.base_url, 'tree', path)
        else:
            # otherwise, redirect to /files
            if '/files/' in path:
                # redirect without files/ iff it would 404
                # this preserves pre-2.0-style 'files/' links
                # FIXME: this is hardcoded based on notebook_path,
                # but so is the files handler itself,
                # so it should work until both are cleaned up.
                parts = path.split('/')
                files_path = os.path.join(nbm.notebook_dir, *parts)
                if not os.path.exists(files_path):
                    self.log.warn("Deprecated files/ URL: %s", path)
                    path = path.replace('/files/', '/', 1)
            
            url = url_path_join(self.base_url, 'files', path)
        url = url_escape(url)
        self.log.debug("Redirecting %s to %s", self.request.path, url)
        self.redirect(url)

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/notebooks%s" % notebook_path_regex, NotebookHandler),
    (r"/notebooks%s" % path_regex, NotebookRedirectHandler),
]


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

from tornado import web
from ..base.handlers import IPythonHandler
from urllib import quote, unquote

#-----------------------------------------------------------------------------
# Handlers
#-----------------------------------------------------------------------------


class ProjectDashboardHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        self.write(self.render_template('tree.html',
            project=self.project,
            project_component=self.project.split('/'),
            notebook_path= "''"
        ))


class ProjectPathDashboardHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self, notebook_path):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        if name != None:
            if path == None:
                self.redirect(self.base_project_url + 'notebooks/' + quote(name))
            else:
                self.redirect(self.base_project_url + 'notebooks/' + path + quote(name))
        else:
            project = self.project + '/' + notebook_path
            self.write(self.render_template('tree.html',
                project=project,
                project_component=project.split('/'),
                notebook_path=path,
                notebook_name=quote(name)))    


class TreeRedirectHandler(IPythonHandler):
    
    @authenticate_unless_readonly
    def get(self):
        url = self.base_project_url + 'tree'
        self.redirect(url)

class TreePathRedirectHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self, notebook_path):
        url = self.base_project_url + 'tree/'+ notebook_path
        self.redirect(url)

class ProjectRedirectHandler(IPythonHandler):
    
    @authenticate_unless_readonly
    def get(self):
        url = self.base_project_url + 'tree'
        self.redirect(url)

class NewFolderHandler(IPythonHandler):
    
    @authenticate_unless_readonly
    def get(self, notebook_path):
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        nbm.add_new_folder(path)
        url = self.base_project_url + 'tree/' + notebook_path
        self.redirect(url)


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_path_regex = r"(?P<notebook_path>.+)"

default_handlers = [
    (r"/tree/%s/-new" %_notebook_path_regex, NewFolderHandler),
    (r"/tree/%s/" % _notebook_path_regex, TreePathRedirectHandler),
    (r"/tree/%s" % _notebook_path_regex, ProjectPathDashboardHandler),
    (r"/tree", ProjectDashboardHandler),
    (r"/tree/", TreeRedirectHandler),
    (r"/", ProjectRedirectHandler)
    ]

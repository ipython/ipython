"""Tornado handlers for the contents web service.

Authors:

* Zach Sailer
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from tornado import web

from zmq.utils import jsonapi

from IPython.utils.jsonutil import date_default

from ...base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Contents web service handlers
#-----------------------------------------------------------------------------


class ContentRootHandler(IPythonHandler):

    @web.authenticated
    def get(self):
        cm = self.content_manager
        contents = cm.list_contents("")
        self.finish(jsonapi.dumps(contents))
        

class ContentHandler(IPythonHandler):

    @web.authenticated
    def get(self, content_path):
        cm = self.content_manager
        contents = cm.list_contents(content_path)
        self.finish(jsonapi.dumps(contents))

    @web.authenticated
    def delete(self, content_path):
        cm = self.content_manager
        cm.delete_content(content_path)
        self.set_status(204)
        self.finish()

class ServicesRedirectHandler(IPythonHandler):
    
    @web.authenticated
    def get(self):
        url = self.base_project_url + 'api'
        self.redirect(url)

class ServicesHandler(IPythonHandler):
    
    @web.authenticated
    def get(self):
        services = ['contents', 'notebooks', 'sessions', 'kernels', 'clusters']
        self.finish(jsonapi.dumps(services))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

_content_path_regex = r"(?P<content_path>.+)"

default_handlers = [
    (r"api/contents/%s" % _content_path_regex, ContentHandler),
    (r"api/contents",  ContentRootHandler),
    (r"api/", ServicesRedirectHandler),
    (r"api", ServicesHandler)
    
]



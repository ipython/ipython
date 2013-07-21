"""Tornado handlers for the contents web service.

Authors:

* Zach Sailer
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
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

from ...base.handlers import IPythonHandler, authenticate_unless_readonly

#-----------------------------------------------------------------------------
# Contents web service handlers
#-----------------------------------------------------------------------------


class ContentRootHandler(IPythonHandler):

    @authenticate_unless_readonly
    def get(self):
        nbm = self.notebook_manager
        cm = self.content_manager
        contents = cm.list_contents("")
        self.finish(jsonapi.dumps(contents))
        

class ContentHandler(IPythonHandler):

    @web.authenticated
    def get(self, content_path):
        cm = self.content_manager
        nbm = self.notebook_manager
        contents = cm.list_contents(content_path)
        self.finish(jsonapi.dumps(contents))

    @web.authenticated
    def delete(self, content_path):
        
        self.set_status(204)
        self.finish()


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

_content_path_regex = r"(?P<content_path>.+)"

default_handlers = [
    (r"api/contents/%s" % _content_path_regex, ContentHandler),
    (r"api/contents",  ContentRootHandler)
]



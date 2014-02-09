"""Tornado handlers logging into the notebook.

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

import uuid

from tornado.escape import url_escape

from IPython.lib.security import passwd_check

from ..base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Handler
#-----------------------------------------------------------------------------

class LoginHandler(IPythonHandler):

    def _render(self, message=None):
        self.write(self.render_template('login.html',
                next=url_escape(self.get_argument('next', default=self.base_url)),
                message=message,
        ))

    def get(self):
        if self.current_user:
            self.redirect(self.get_argument('next', default=self.base_url))
        else:
            self._render()

    def post(self):
        pwd = self.get_argument('password', default=u'')
        if self.login_available:
            if passwd_check(self.password, pwd):
                self.set_secure_cookie(self.cookie_name, str(uuid.uuid4()))
            else:
                self._render(message={'error': 'Invalid password'})
                return

        self.redirect(self.get_argument('next', default=self.base_url))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [(r"/login", LoginHandler)]

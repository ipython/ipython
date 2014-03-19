"""Tornado handlers logging into the notebook.

Authors:

* Brian Granger
* Phil Elson
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2014  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import uuid

from tornado.escape import url_escape
from tornado import web

from IPython.config.configurable import Configurable
from IPython.lib.security import passwd_check

from ..base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Handler
#-----------------------------------------------------------------------------

class LoginHandler(IPythonHandler):
    """ The basic IPythonWebApplication login handler which authenticates with a
    hashed password from the configuration.
    
    """
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
        hashed_password = self.password_from_configuration(self.application)
        typed_password = self.get_argument('password', default=u'')
        if self.login_available(self.application):
            if passwd_check(hashed_password, typed_password):
                self.set_secure_cookie(self.cookie_name, str(uuid.uuid4()))
            else:
                self._render(message={'error': 'Invalid password'})
                return

        self.redirect(self.get_argument('next', default=self.base_url))
    
    @classmethod
    def validate_notebook_app_security(cls, notebook_app, ssl_options=None):
        if not notebook_app.ip:
            warning = "WARNING: The notebook server is listening on all IP addresses"
            if ssl_options is None:
                notebook_app.log.critical(warning + " and not using encryption. This "
                    "is not recommended.")
            if not self.password_from_configuration(notebook_app):
                notebook_app.log.critical(warning + " and not using authentication. "
                    "This is highly insecure and not recommended.")

    @staticmethod
    def password_from_configuration(webapp):
        """ Return the hashed password from the given NotebookWebApplication's configuration.
        
        If there is no configured password, None will be returned.
        
        """
        return webapp.settings['config']['NotebookApp'].get('password', None)

    @classmethod
    def login_available(cls, webapp):
        """Whether this LoginHandler is needed - and therefore whether the login page should be displayed."""
        return bool(cls.password_from_configuration(webapp))

"""Tornado handlers for logging into the notebook."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import uuid

from tornado.escape import url_escape

from IPython.lib.security import passwd_check

from ..base.handlers import IPythonHandler


class LoginHandler(IPythonHandler):
    """The basic tornado login handler
    
    authenticates with a hashed password from the configuration.
    """
    def _render(self, message=None):
        self.write(self.render_template('login.html',
                next=url_escape(self.get_argument('next', default=self.base_url)),
                message=message,
        ))

    def get(self):
        if self.current_user:
            next_url = self.get_argument('next', default=self.base_url)
            if not next_url.startswith(self.base_url):
                # require that next_url be absolute path within our path
                next_url = self.base_url
            self.redirect(next_url)
        else:
            self._render()
    
    @property
    def hashed_password(self):
        return self.password_from_settings(self.settings)

    def post(self):
        typed_password = self.get_argument('password', default=u'')
        if self.login_available(self.settings):
            if passwd_check(self.hashed_password, typed_password):
                # tornado <4.2 have a bug that consider secure==True as soon as
                # 'secure' kwarg is passed to set_secure_cookie
                if self.settings.get('secure_cookie', self.request.protocol == 'https'):
                    kwargs = {'secure':True}
                else:
                    kwargs = {}
                self.set_secure_cookie(self.cookie_name, str(uuid.uuid4()), **kwargs)
            else:
                self._render(message={'error': 'Invalid password'})
                return
        
        next_url = self.get_argument('next', default=self.base_url)
        if not next_url.startswith(self.base_url):
            # require that next_url be absolute path within our path
            next_url = self.base_url
        self.redirect(next_url)
    
    @classmethod
    def get_user(cls, handler):
        """Called by handlers.get_current_user for identifying the current user.
        
        See tornado.web.RequestHandler.get_current_user for details.
        """
        # Can't call this get_current_user because it will collide when
        # called on LoginHandler itself.
        
        user_id = handler.get_secure_cookie(handler.cookie_name)
        # For now the user_id should not return empty, but it could, eventually.
        if user_id == '':
            user_id = 'anonymous'
        if user_id is None:
            # prevent extra Invalid cookie sig warnings:
            handler.clear_login_cookie()
            if not handler.login_available:
                user_id = 'anonymous'
        return user_id
        
    
    @classmethod
    def validate_security(cls, app, ssl_options=None):
        """Check the notebook application's security.
        
        Show messages, or abort if necessary, based on the security configuration.
        """
        if not app.ip:
            warning = "WARNING: The notebook server is listening on all IP addresses"
            if ssl_options is None:
                app.log.warning(warning + " and not using encryption. This "
                    "is not recommended.")
            if not app.password:
                app.log.warning(warning + " and not using authentication. "
                    "This is highly insecure and not recommended.")

    @classmethod
    def password_from_settings(cls, settings):
        """Return the hashed password from the tornado settings.
        
        If there is no configured password, an empty string will be returned.
        """
        return settings.get('password', u'')

    @classmethod
    def login_available(cls, settings):
        """Whether this LoginHandler is needed - and therefore whether the login page should be displayed."""
        return bool(cls.password_from_settings(settings))


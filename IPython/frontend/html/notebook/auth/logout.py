"""Tornado handlers for logging out of the notebook.

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

from .base import IPythonHandler

#-----------------------------------------------------------------------------
# Handler
#-----------------------------------------------------------------------------


class LogoutHandler(IPythonHandler):

    def get(self):
        self.clear_login_cookie()
        if self.login_available:
            message = {'info': 'Successfully logged out.'}
        else:
            message = {'warning': 'Cannot log out.  Notebook authentication '
                       'is disabled.'}
        self.write(self.render_template('logout.html',
                    message=message))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [(r"/logout", LogoutHandler)]
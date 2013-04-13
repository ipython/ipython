import re
import os
import uuid
from zmq.utils import jsonapi
from tornado import web
from tornado.escape import url_escape
from IPython.lib.security import passwd_check
from IPython.frontend.html.notebook.handlers import (
 AuthenticatedHandler, authenticate_unless_readonly)
from .continuum_helpers import notebook_render


class AutoLoginHandler(AuthenticatedHandler):
    def _render(self, message=None):
        template = self.application.jinja2_env.get_template('login.html')

        self.write( template.render(
            
                next=url_escape(
                    self.get_argument(
                        'next',
                        default=self.application.ipython_app.base_project_url)),
                read_only=self.read_only,
                logged_in=self.logged_in,
                login_available=self.login_available,
                base_project_url=self.application.ipython_app.base_project_url,
                message=message))
    def get(self, password):
        redir_url = self.get_argument(
            'next', default=self.application.ipython_app.base_project_url)

        #tornado does an odd form of urlescaping inside of
        #self.redirect, for now replacing ' ' with %20 fixes this,
        #their are probably other escapes to do.  Passing in properly
        #url-escaped urls to the next parameter doesn't help because
        #tornado unescapes the next parameter.


        url_escaped = re.sub(r" ", "%20", redir_url)

        if self.current_user:
            self.redirect(url_escaped)
            return
        pwd = password
        if passwd_check(self.application.password, pwd):
            self.set_secure_cookie(
                self.settings['cookie_name'], str(uuid.uuid4()))
            self.redirect(url_escaped)
            return
        else:
            self._render(message={
                    'error': 'Invalid password.  This is your wakari password'})
            return


class ContinuumProjectDashboardHandler(AuthenticatedHandler):

    @authenticate_unless_readonly
    def get(self):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir
        template = self.application.jinja2_env.get_template(
            'continuumdashboard.html')
        self.write( template.render(project=project,
            base_project_url=self.application.ipython_app.base_project_url,
            base_kernel_url=self.application.ipython_app.base_kernel_url,
            read_only=self.read_only,
            logged_in=self.logged_in,
            login_available=self.login_available))

class NotebookDirectHandler(AuthenticatedHandler):
    @authenticate_unless_readonly
    def get(self, notebook_path):
        print "notebook_path", notebook_path
        nbm = self.application.notebook_manager
        notebook_id = nbm.get_notebook_id_by_path(notebook_path)
        return notebook_render(self, notebook_id)

class NotebookRelativeHandler(AuthenticatedHandler):
    @authenticate_unless_readonly
    def get(self, relative_notebook_path):
        print "relative_notebook_path", relative_notebook_path
        nbm = self.application.notebook_manager
        notebook_path = os.path.join(nbm.notebook_dir, relative_notebook_path)
        notebook_id = nbm.get_notebook_id_by_path(notebook_path)
        return notebook_render(self, notebook_id)

class UNUSEDNotebookDir(AuthenticatedHandler):
    """ This is an example CORS handler, it isn't actually used """
    def options(self):
        print "does this ever get called"
        self.set_header('Access-Control-Allow-Origin', 'http://localhost')
        self.set_header('x-csrftoken', 'set_in_ipython')
        self.set_header('Access-Control-Allow-Headers', 'x-csrftoken')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Access-Control-Allow-Credentials','true')


    @authenticate_unless_readonly
    def post(self):
        print "NotebookDir post"
        print "does this ever get called"
        self.set_header('Access-Control-Allow-Origin', 'http://localhost')
        self.set_header('x-csrftoken', 'set_in_ipython')
        self.set_header('Access-Control-Allow-Headers', 'x-csrftoken')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Access-Control-Allow-Credentials','true')
        path = self.get_argument('path',default=None)
        self.application.notebook_manager.notebook_dir = path
        return self.redirect("/")

import re
import os
import uuid
from zmq.utils import jsonapi
from tornado import web




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

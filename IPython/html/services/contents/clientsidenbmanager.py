"""A dummy contents manager for when the logic is done client side (in JavaScript)."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .manager import ContentsManager

import os.path

class ClientSideContentsManager(ContentsManager):
    """Dummy contents manager for use with client-side contents APIs like GDrive

    The view handlers for notebooks and directories (/tree/) check with the
    ContentsManager that their target exists so they can return 404 if not. Using
    this class as the contents manager allows those pages to render without
    checking something that the server doesn't know about.
    """
    def dir_exists(self, path):
        return True

    def is_hidden(self, path):
        return False

    def file_exists(self, name, path=''):
        return True

    def get_kernel_path(self, path, model=None):
         """Return the initial working dir a kernel associated with a given notebook
         
         Here just alway return home directory
         """
         return os.path.expanduser('~')

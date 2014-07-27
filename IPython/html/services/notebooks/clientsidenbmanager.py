"""A notebook manager for when the logic is done client side (in JavaScript)."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .nbmanager import NotebookManager

from fnmatch import fnmatch
import itertools
import os

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current, sign
from IPython.utils.traitlets import Instance, Unicode, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ClientSideNotebookManager(NotebookManager):
    # The notebook directory is meaningless since  we are not using
    # the local filesystem.
    notebook_dir = ''

    def path_exists(self, path):
        # Always return true, because this check is now done client side.
       return True

    def is_hidden(self, path):
        # Always return false, because this check is now done client side.
        return False

    def notebook_exists(self, name, path=''):
        # Always return true, because this check is now done client side.
        return True

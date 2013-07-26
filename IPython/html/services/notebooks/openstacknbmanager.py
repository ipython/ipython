#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""A notebook manager that uses OpenStack Swift object storage.

Authors:

* Kyle Kelley
"""

#-----------------------------------------------------------------------------
# Copyright (C) 2013 The IPython Development Team
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import datetime

from swiftclient import client

from tornado import web

from .nbmanager import NotebookManager
from IPython.nbformat import current
from IPython.utils.traitlets import Unicode, Instance
from IPython.utils import tz

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class OpenStackNotebookManager(NotebookManager):

    account_name = Unicode('', config=True, help='OpenStack account name.')
    account_key = Unicode('', config=True, help='OpenStack account key.')
    container = Unicode('', config=True, help='Container name for notebooks.')

    def __init__(self, **kwargs):
        super(OpenStackNotebookManager, self).__init__(**kwargs)
        pass

    def load_notebook_names(self):
        """On startup load the notebook ids and names from OpenStack Swift.

        The object names are the notebook ids and the notebook names are stored
        as object metadata.
        """
        pass

    def list_notebooks(self):
        """List all notebooks in the container.

        This version uses `self.mapping` as the authoritative notebook list.
        """
        pass

    def read_notebook_object(self, notebook_id):
        """Get the object representation of a notebook by notebook_id."""
        pass

    def write_notebook_object(self, nb, notebook_id=None):
        """Save an existing notebook object by notebook_id."""
        pass

    def delete_notebook(self, notebook_id):
        """Delete notebook by notebook_id."""
        pass

    def info_string(self):
        pass

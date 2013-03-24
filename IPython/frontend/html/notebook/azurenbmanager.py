"""A notebook manager that uses Azure blob storage.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import datetime

import azure
from azure.storage import BlobService

from tornado import web

from .nbmanager import NotebookManager
from IPython.nbformat import current
from IPython.utils.traitlets import Unicode, Instance


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class AzureNotebookManager(NotebookManager):

    account_name = Unicode('', config=True, help='Azure storage account name.')
    account_key = Unicode('', config=True, help='Azure storage account key.')
    container = Unicode('', config=True, help='Container name for notebooks.')

    blob_service_host_base = Unicode('.blob.core.windows.net', config=True,
        help='The basename for the blob service URL. If running on the preview site this '
             'will be .blob.core.azure-preview.com.')
    def _blob_service_host_base_changed(self, new):
        self._update_service_host_base(new)

    blob_service = Instance('azure.storage.BlobService')
    def _blob_service_default(self):
        return BlobService(account_name=self.account_name, account_key=self.account_key)

    def __init__(self, **kwargs):
        super(AzureNotebookManager, self).__init__(**kwargs)
        self._update_service_host_base(self.blob_service_host_base)
        self._create_container()

    def _update_service_host_base(self, shb):
        azure.BLOB_SERVICE_HOST_BASE = shb

    def _create_container(self):
        self.blob_service.create_container(self.container)

    def load_notebook_names(self):
        """On startup load the notebook ids and names from Azure.

        The blob names are the notebook ids and the notebook names are stored
        as blob metadata.
        """
        self.mapping = {}
        blobs = self.blob_service.list_blobs(self.container)
        ids = [blob.name for blob in blobs]
        
        for id in ids:
            md = self.blob_service.get_blob_metadata(self.container, id)
            name = md['x-ms-meta-nbname']
            self.mapping[id] = name

    def list_notebooks(self):
        """List all notebooks in the container.

        This version uses `self.mapping` as the authoritative notebook list.
        """
        data = [dict(notebook_id=id,name=name) for id, name in self.mapping.items()]
        data = sorted(data, key=lambda item: item['name'])
        return data

    def read_notebook_object(self, notebook_id):
        """Get the object representation of a notebook by notebook_id."""
        if not self.notebook_exists(notebook_id):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        try:
            s = self.blob_service.get_blob(self.container, notebook_id)
        except:
            raise web.HTTPError(500, u'Notebook cannot be read.')
        try:
            # v1 and v2 and json in the .ipynb files.
            nb = current.reads(s, u'json')
        except:
            raise web.HTTPError(500, u'Unreadable JSON notebook.')
        # Todo: The last modified should actually be saved in the notebook document.
        # We are just using the current datetime until that is implemented.
        last_modified = datetime.datetime.utcnow()
        return last_modified, nb

    def write_notebook_object(self, nb, notebook_id=None):
        """Save an existing notebook object by notebook_id."""
        try:
            new_name = nb.metadata.name
        except AttributeError:
            raise web.HTTPError(400, u'Missing notebook name')

        if notebook_id is None:
            notebook_id = self.new_notebook_id(new_name)

        if notebook_id not in self.mapping:
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)

        try:
            data = current.writes(nb, u'json')
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while saving notebook: %s' % e)

        metadata = {'nbname': new_name}
        try:
            self.blob_service.put_blob(self.container, notebook_id, data, 'BlockBlob', x_ms_meta_name_values=metadata)
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while saving notebook: %s' % e)

        self.mapping[notebook_id] = new_name
        return notebook_id

    def delete_notebook(self, notebook_id):
        """Delete notebook by notebook_id."""
        if not self.notebook_exists(notebook_id):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        try:
            self.blob_service.delete_blob(self.container, notebook_id)
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while deleting notebook: %s' % e)
        else:
            self.delete_notebook_id(notebook_id)

    def info_string(self):
        return "Serving notebooks from Azure storage: %s, %s" % (self.account_name, self.container)

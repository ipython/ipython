"""Tornado handlers for the contents web service."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json

from tornado import web

from IPython.html.utils import url_path_join, url_escape
from IPython.utils.jsonutil import date_default

from IPython.html.base.handlers import (IPythonHandler, json_errors,
                                    notebook_path_regex, path_regex,
                                    notebook_name_regex)


class ContentsHandler(IPythonHandler):

    SUPPORTED_METHODS = (u'GET', u'PUT', u'PATCH', u'POST', u'DELETE')

    def location_url(self, name, path=''):
        """Return the full URL location of a file.

        Parameters
        ----------
        name : unicode
            The base name of the file, such as "foo.ipynb".
        path : unicode
            The API path of the file, such as "foo/bar".
        """
        return url_escape(url_path_join(
            self.base_url, 'api', 'contents', path, name
        ))

    def _finish_model(self, model, location=True):
        """Finish a JSON request with a model, setting relevant headers, etc."""
        if location:
            location = self.location_url(model['name'], model['path'])
            self.set_header('Location', location)
        self.set_header('Last-Modified', model['last_modified'])
        self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def get(self, path='', name=None):
        """Return a file or list of files.

        * GET with path and no filename lists files in a directory
        * GET with path and filename returns file contents model
        """
        cm = self.contents_manager
        # Check to see if a filename was given
        if name is None:
            # TODO: Remove this after we create the contents web service and directories are
            # no longer listed by the notebook web service. This should only handle notebooks
            # and not directories.
            dirs = cm.list_dirs(path)
            files = []
            index = []
            for nb in cm.list_files(path):
                if nb['name'].lower() == 'index.ipynb':
                    index.append(nb)
                else:
                    files.append(nb)
            files = index + dirs + files
            self.finish(json.dumps(files, default=date_default))
            return
        # get and return notebook representation
        model = cm.get(name, path)
        self._finish_model(model, location=False)

    @web.authenticated
    @json_errors
    def patch(self, path='', name=None):
        """PATCH renames a notebook without re-uploading content."""
        cm = self.contents_manager
        if name is None:
            raise web.HTTPError(400, u'Filename missing')
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, u'JSON body missing')
        model = cm.update(model, name, path)
        self._finish_model(model)

    def _copy(self, copy_from, path, copy_to=None):
        """Copy a file in path, optionally specifying the new name.

        Only support copying within the same directory.
        """
        self.log.info(u"Copying from %s/%s to %s/%s",
            path, copy_from,
            path, copy_to or '',
        )
        model = self.contents_manager.copy(copy_from, copy_to, path)
        self.set_status(201)
        self._finish_model(model)

    def _upload(self, model, path, name=None):
        """Upload a file

        If name specified, create it in path/name.
        """
        self.log.info(u"Uploading file to %s/%s", path, name or '')
        if name:
            model['name'] = name

        model = self.contents_manager.create_notebook(model, path)
        self.set_status(201)
        self._finish_model(model)

    def _create_empty_notebook(self, path, name=None):
        """Create an empty notebook in path

        If name specified, create it in path/name.
        """
        self.log.info(u"Creating new notebook in %s/%s", path, name or '')
        model = {}
        if name:
            model['name'] = name
        model = self.contents_manager.create_notebook(model, path=path)
        self.set_status(201)
        self._finish_model(model)

    def _save(self, model, path, name):
        """Save an existing file."""
        self.log.info(u"Saving file at %s/%s", path, name)
        model = self.contents_manager.save(model, name, path)
        if model['path'] != path.strip('/') or model['name'] != name:
            # a rename happened, set Location header
            location = True
        else:
            location = False
        self._finish_model(model, location)

    @web.authenticated
    @json_errors
    def post(self, path='', name=None):
        """Create a new notebook in the specified path.

        POST creates new notebooks. The server always decides on the notebook name.

        POST /api/contents/path
          New untitled notebook in path. If content specified, upload a
          notebook, otherwise start empty.
        POST /api/contents/path?copy=OtherNotebook.ipynb
          New copy of OtherNotebook in path
        """

        if name is not None:
            raise web.HTTPError(400, "Only POST to directories. Use PUT for full names.")

        model = self.get_json_body()

        if model is not None:
            copy_from = model.get('copy_from')
            if copy_from:
                if model.get('content'):
                    raise web.HTTPError(400, "Can't upload and copy at the same time.")
                self._copy(copy_from, path)
            else:
                self._upload(model, path)
        else:
            self._create_empty_notebook(path)

    @web.authenticated
    @json_errors
    def put(self, path='', name=None):
        """Saves the file in the location specified by name and path.

        PUT is very similar to POST, but the requester specifies the name,
        whereas with POST, the server picks the name.

        PUT /api/contents/path/Name.ipynb
          Save notebook at ``path/Name.ipynb``. Notebook structure is specified
          in `content` key of JSON request body. If content is not specified,
          create a new empty notebook.
        PUT /api/contents/path/Name.ipynb?copy=OtherNotebook.ipynb
          Copy OtherNotebook to Name
        """
        if name is None:
            raise web.HTTPError(400, "Only PUT to full names. Use POST for directories.")

        model = self.get_json_body()
        if model:
            copy_from = model.get('copy_from')
            if copy_from:
                if model.get('content'):
                    raise web.HTTPError(400, "Can't upload and copy at the same time.")
                self._copy(copy_from, path, name)
            elif self.contents_manager.file_exists(name, path):
                self._save(model, path, name)
            else:
                self._upload(model, path, name)
        else:
            self._create_empty_notebook(path, name)

    @web.authenticated
    @json_errors
    def delete(self, path='', name=None):
        """delete a file in the given path"""
        cm = self.contents_manager
        cm.delete(name, path)
        self.set_status(204)
        self.finish()


class CheckpointsHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'POST')

    @web.authenticated
    @json_errors
    def get(self, path='', name=None):
        """get lists checkpoints for a file"""
        cm = self.contents_manager
        checkpoints = cm.list_checkpoints(name, path)
        data = json.dumps(checkpoints, default=date_default)
        self.finish(data)

    @web.authenticated
    @json_errors
    def post(self, path='', name=None):
        """post creates a new checkpoint"""
        cm = self.contents_manager
        checkpoint = cm.create_checkpoint(name, path)
        data = json.dumps(checkpoint, default=date_default)
        location = url_path_join(self.base_url, 'api/contents',
            path, name, 'checkpoints', checkpoint['id'])
        self.set_header('Location', url_escape(location))
        self.set_status(201)
        self.finish(data)


class ModifyCheckpointsHandler(IPythonHandler):

    SUPPORTED_METHODS = ('POST', 'DELETE')

    @web.authenticated
    @json_errors
    def post(self, path, name, checkpoint_id):
        """post restores a file from a checkpoint"""
        cm = self.contents_manager
        cm.restore_checkpoint(checkpoint_id, name, path)
        self.set_status(204)
        self.finish()

    @web.authenticated
    @json_errors
    def delete(self, path, name, checkpoint_id):
        """delete clears a checkpoint for a given file"""
        cm = self.contents_manager
        cm.delete_checkpoint(checkpoint_id, name, path)
        self.set_status(204)
        self.finish()

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_checkpoint_id_regex = r"(?P<checkpoint_id>[\w-]+)"

default_handlers = [
    (r"/api/contents%s/checkpoints" % notebook_path_regex, CheckpointsHandler),
    (r"/api/contents%s/checkpoints/%s" % (notebook_path_regex, _checkpoint_id_regex),
        ModifyCheckpointsHandler),
    (r"/api/contents%s" % notebook_path_regex, ContentsHandler),
    (r"/api/contents%s" % path_regex, ContentsHandler),
]

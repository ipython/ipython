"""Tornado handlers for the contents web service."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json

from tornado import web

from IPython.html.utils import url_path_join, url_escape
from IPython.utils.jsonutil import date_default

from IPython.html.base.handlers import (
    IPythonHandler, json_errors, path_regex,
)


def sort_key(model):
    """key function for case-insensitive sort by name and type"""
    iname = model['name'].lower()
    type_key = {
        'directory' : '0',
        'notebook'  : '1',
        'file'      : '2',
    }.get(model['type'], '9')
    return u'%s%s' % (type_key, iname)

class ContentsHandler(IPythonHandler):

    SUPPORTED_METHODS = (u'GET', u'PUT', u'PATCH', u'POST', u'DELETE')

    def location_url(self, path):
        """Return the full URL location of a file.

        Parameters
        ----------
        path : unicode
            The API path of the file, such as "foo/bar.txt".
        """
        return url_escape(url_path_join(
            self.base_url, 'api', 'contents', path
        ))

    def _finish_model(self, model, location=True):
        """Finish a JSON request with a model, setting relevant headers, etc."""
        if location:
            location = self.location_url(model['path'])
            self.set_header('Location', location)
        self.set_header('Last-Modified', model['last_modified'])
        self.finish(json.dumps(model, default=date_default))

    @web.authenticated
    @json_errors
    def get(self, path=''):
        """Return a model for a file or directory.

        A directory model contains a list of models (without content)
        of the files and directories it contains.
        """
        path = path or ''
        model = self.contents_manager.get_model(path=path)
        if model['type'] == 'directory':
            # group listing by type, then by name (case-insensitive)
            # FIXME: sorting should be done in the frontends
            model['content'].sort(key=sort_key)
        self._finish_model(model, location=False)

    @web.authenticated
    @json_errors
    def patch(self, path=''):
        """PATCH renames a file or directory without re-uploading content."""
        cm = self.contents_manager
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, u'JSON body missing')
        print('before', model)
        model = cm.update(model, path)
        print('after', model)
        self._finish_model(model)

    def _copy(self, copy_from, copy_to=None):
        """Copy a file, optionally specifying the new path.
        """
        self.log.info(u"Copying {copy_from} to {copy_to}".format(
            copy_from=copy_from,
            copy_to=copy_to or '',
        ))
        model = self.contents_manager.copy(copy_from, copy_to)
        self.set_status(201)
        self._finish_model(model)

    def _upload(self, model, path):
        """Handle upload of a new file to path"""
        self.log.info(u"Uploading file to %s", path)
        model = self.contents_manager.create_file(model, path)
        self.set_status(201)
        self._finish_model(model)

    def _create_empty_file(self, path, ext='.ipynb'):
        """Create an empty file in path

        If name specified, create it in path.
        """
        self.log.info(u"Creating new file in %s", path)
        model = self.contents_manager.create_file(path=path, ext=ext)
        self.set_status(201)
        self._finish_model(model)

    def _save(self, model, path):
        """Save an existing file."""
        self.log.info(u"Saving file at %s", path)
        model = self.contents_manager.save(model, path)
        self._finish_model(model)

    @web.authenticated
    @json_errors
    def post(self, path=''):
        """Create a new file or directory in the specified path.

        POST creates new files or directories. The server always decides on the name.

        POST /api/contents/path
          New untitled, empty file or directory.
        POST /api/contents/path
          with body {"copy_from" : "/path/to/OtherNotebook.ipynb"}
          New copy of OtherNotebook in path
        """

        cm = self.contents_manager

        if cm.file_exists(path):
            raise web.HTTPError(400, "Cannot POST to existing files, use PUT instead.")

        if not cm.dir_exists(path):
            raise web.HTTPError(404, "No such directory: %s" % path)

        model = self.get_json_body()

        if model is not None:
            copy_from = model.get('copy_from')
            ext = model.get('ext', '.ipynb')
            if copy_from:
                self._copy(copy_from, path)
            else:
                self._create_empty_file(path, ext=ext)
        else:
            self._create_empty_file(path)

    @web.authenticated
    @json_errors
    def put(self, path=''):
        """Saves the file in the location specified by name and path.

        PUT is very similar to POST, but the requester specifies the name,
        whereas with POST, the server picks the name.

        PUT /api/contents/path/Name.ipynb
          Save notebook at ``path/Name.ipynb``. Notebook structure is specified
          in `content` key of JSON request body. If content is not specified,
          create a new empty notebook.
        PUT /api/contents/path/Name.ipynb
          with JSON body::

            {
              "copy_from" : "[path/to/]OtherNotebook.ipynb"
            }

          Copy OtherNotebook to Name
        """
        model = self.get_json_body()
        if model:
            copy_from = model.get('copy_from')
            if copy_from:
                if model.get('content'):
                    raise web.HTTPError(400, "Can't upload and copy at the same time.")
                self._copy(copy_from, path)
            elif self.contents_manager.file_exists(path):
                self._save(model, path)
            else:
                self._upload(model, path)
        else:
            self._create_empty_file(path)

    @web.authenticated
    @json_errors
    def delete(self, path=''):
        """delete a file in the given path"""
        cm = self.contents_manager
        self.log.warn('delete %s', path)
        cm.delete(path)
        self.set_status(204)
        self.finish()


class CheckpointsHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'POST')

    @web.authenticated
    @json_errors
    def get(self, path=''):
        """get lists checkpoints for a file"""
        cm = self.contents_manager
        checkpoints = cm.list_checkpoints(path)
        data = json.dumps(checkpoints, default=date_default)
        self.finish(data)

    @web.authenticated
    @json_errors
    def post(self, path=''):
        """post creates a new checkpoint"""
        cm = self.contents_manager
        checkpoint = cm.create_checkpoint(path)
        data = json.dumps(checkpoint, default=date_default)
        location = url_path_join(self.base_url, 'api/contents',
            path, 'checkpoints', checkpoint['id'])
        self.set_header('Location', url_escape(location))
        self.set_status(201)
        self.finish(data)


class ModifyCheckpointsHandler(IPythonHandler):

    SUPPORTED_METHODS = ('POST', 'DELETE')

    @web.authenticated
    @json_errors
    def post(self, path, checkpoint_id):
        """post restores a file from a checkpoint"""
        cm = self.contents_manager
        cm.restore_checkpoint(checkpoint_id, path)
        self.set_status(204)
        self.finish()

    @web.authenticated
    @json_errors
    def delete(self, path, checkpoint_id):
        """delete clears a checkpoint for a given file"""
        cm = self.contents_manager
        cm.delete_checkpoint(checkpoint_id, path)
        self.set_status(204)
        self.finish()


class NotebooksRedirectHandler(IPythonHandler):
    """Redirect /api/notebooks to /api/contents"""
    SUPPORTED_METHODS = ('GET', 'PUT', 'PATCH', 'POST', 'DELETE')

    def get(self, path):
        self.log.warn("/api/notebooks is deprecated, use /api/contents")
        self.redirect(url_path_join(
            self.base_url,
            'api/contents',
            path
        ))

    put = patch = post = delete = get


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_checkpoint_id_regex = r"(?P<checkpoint_id>[\w-]+)"

default_handlers = [
    (r"/api/contents%s/checkpoints" % path_regex, CheckpointsHandler),
    (r"/api/contents%s/checkpoints/%s" % (path_regex, _checkpoint_id_regex),
        ModifyCheckpointsHandler),
    (r"/api/contents%s" % path_regex, ContentsHandler),
    (r"/api/notebooks/?(.*)", NotebooksRedirectHandler),
]

"""A contents manager that uses the local file system for storage."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import base64
import io
import os
import glob
import shutil

from tornado import web

from .manager import ContentsManager
from IPython.nbformat import current
from IPython.utils.io import atomic_writing
from IPython.utils.path import ensure_dir_exists
from IPython.utils.traitlets import Unicode, Bool, TraitError
from IPython.utils.py3compat import getcwd
from IPython.utils import tz
from IPython.html.utils import is_hidden, to_os_path, url_path_join


class FileContentsManager(ContentsManager):

    root_dir = Unicode(getcwd(), config=True)

    save_script = Bool(False, config=True, help='DEPRECATED, IGNORED')
    def _save_script_changed(self):
        self.log.warn("""
        Automatically saving notebooks as scripts has been removed.
        Use `ipython nbconvert --to python [notebook]` instead.
        """)

    def _root_dir_changed(self, name, old, new):
        """Do a bit of validation of the root_dir."""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            self.root_dir = os.path.abspath(new)
            return
        if not os.path.isdir(new):
            raise TraitError("%r is not a directory" % new)

    checkpoint_dir = Unicode('.ipynb_checkpoints', config=True,
        help="""The directory name in which to keep file checkpoints

        This is a path relative to the file's own directory.

        By default, it is .ipynb_checkpoints
        """
    )

    def _copy(self, src, dest):
        """copy src to dest

        like shutil.copy2, but log errors in copystat
        """
        shutil.copyfile(src, dest)
        try:
            shutil.copystat(src, dest)
        except OSError as e:
            self.log.debug("copystat on %s failed", dest, exc_info=True)

    def _get_os_path(self, name=None, path=''):
        """Given a filename and API path, return its file system
        path.

        Parameters
        ----------
        name : string
            A filename
        path : string
            The relative API path to the named file.

        Returns
        -------
        path : string
            API path to be evaluated relative to root_dir.
        """
        if name is not None:
            path = url_path_join(path, name)
        return to_os_path(path, self.root_dir)

    def path_exists(self, path):
        """Does the API-style path refer to an extant directory?

        API-style wrapper for os.path.isdir

        Parameters
        ----------
        path : string
            The path to check. This is an API path (`/` separated,
            relative to root_dir).

        Returns
        -------
        exists : bool
            Whether the path is indeed a directory.
        """
        path = path.strip('/')
        os_path = self._get_os_path(path=path)
        return os.path.isdir(os_path)

    def is_hidden(self, path):
        """Does the API style path correspond to a hidden directory or file?

        Parameters
        ----------
        path : string
            The path to check. This is an API path (`/` separated,
            relative to root_dir).

        Returns
        -------
        exists : bool
            Whether the path is hidden.

        """
        path = path.strip('/')
        os_path = self._get_os_path(path=path)
        return is_hidden(os_path, self.root_dir)

    def file_exists(self, name, path=''):
        """Returns True if the file exists, else returns False.

        API-style wrapper for os.path.isfile

        Parameters
        ----------
        name : string
            The name of the file you are checking.
        path : string
            The relative path to the file's directory (with '/' as separator)

        Returns
        -------
        exists : bool
            Whether the file exists.
        """
        path = path.strip('/')
        nbpath = self._get_os_path(name, path=path)
        return os.path.isfile(nbpath)

    def exists(self, name=None, path=''):
        """Returns True if the path [and name] exists, else returns False.

        API-style wrapper for os.path.exists

        Parameters
        ----------
        name : string
            The name of the file you are checking.
        path : string
            The relative path to the file's directory (with '/' as separator)

        Returns
        -------
        exists : bool
            Whether the target exists.
        """
        path = path.strip('/')
        os_path = self._get_os_path(name, path=path)
        return os.path.exists(os_path)

    def _base_model(self, name, path=''):
        """Build the common base of a contents model"""
        os_path = self._get_os_path(name, path)
        info = os.stat(os_path)
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        created = tz.utcfromtimestamp(info.st_ctime)
        # Create the base model.
        model = {}
        model['name'] = name
        model['path'] = path
        model['last_modified'] = last_modified
        model['created'] = created
        model['content'] = None
        model['format'] = None
        return model

    def _dir_model(self, name, path='', content=True):
        """Build a model for a directory

        if content is requested, will include a listing of the directory
        """
        os_path = self._get_os_path(name, path)

        four_o_four = u'directory does not exist: %r' % os_path

        if not os.path.isdir(os_path):
            raise web.HTTPError(404, four_o_four)
        elif is_hidden(os_path, self.root_dir):
            self.log.info("Refusing to serve hidden directory %r, via 404 Error",
                os_path
            )
            raise web.HTTPError(404, four_o_four)

        if name is None:
            if '/' in path:
                path, name = path.rsplit('/', 1)
            else:
                name = ''
        model = self._base_model(name, path)
        model['type'] = 'directory'
        dir_path = u'{}/{}'.format(path, name)
        if content:
            model['content'] = contents = []
            for os_path in glob.glob(self._get_os_path('*', dir_path)):
                name = os.path.basename(os_path)
                # skip over broken symlinks in listing
                if not os.path.exists(os_path):
                    self.log.warn("%s doesn't exist", os_path)
                    continue
                if self.should_list(name) and not is_hidden(os_path, self.root_dir):
                    contents.append(self.get_model(name=name, path=dir_path, content=False))

            model['format'] = 'json'

        return model

    def _file_model(self, name, path='', content=True):
        """Build a model for a file

        if content is requested, include the file contents.
        UTF-8 text files will be unicode, binary files will be base64-encoded.
        """
        model = self._base_model(name, path)
        model['type'] = 'file'
        if content:
            os_path = self._get_os_path(name, path)
            with io.open(os_path, 'rb') as f:
                bcontent = f.read()
            try:
                model['content'] = bcontent.decode('utf8')
            except UnicodeError as e:
                model['content'] = base64.encodestring(bcontent).decode('ascii')
                model['format'] = 'base64'
            else:
                model['format'] = 'text'
        return model


    def _notebook_model(self, name, path='', content=True):
        """Build a notebook model

        if content is requested, the notebook content will be populated
        as a JSON structure (not double-serialized)
        """
        model = self._base_model(name, path)
        model['type'] = 'notebook'
        if content:
            os_path = self._get_os_path(name, path)
            with io.open(os_path, 'r', encoding='utf-8') as f:
                try:
                    nb = current.read(f, u'json')
                except Exception as e:
                    raise web.HTTPError(400, u"Unreadable Notebook: %s %s" % (os_path, e))
            self.mark_trusted_cells(nb, name, path)
            model['content'] = nb
            model['format'] = 'json'
        return model

    def get_model(self, name, path='', content=True):
        """ Takes a path and name for an entity and returns its model

        Parameters
        ----------
        name : str
            the name of the target
        path : str
            the API path that describes the relative path for the target

        Returns
        -------
        model : dict
            the contents model. If content=True, returns the contents
            of the file or directory as well.
        """
        path = path.strip('/')

        if not self.exists(name=name, path=path):
            raise web.HTTPError(404, u'No such file or directory: %s/%s' % (path, name))

        os_path = self._get_os_path(name, path)
        if os.path.isdir(os_path):
            model = self._dir_model(name, path, content)
        elif name.endswith('.ipynb'):
            model = self._notebook_model(name, path, content)
        else:
            model = self._file_model(name, path, content)
        return model

    def _save_notebook(self, os_path, model, name='', path=''):
        """save a notebook file"""
        # Save the notebook file
        nb = current.to_notebook_json(model['content'])

        self.check_and_sign(nb, name, path)

        if 'name' in nb['metadata']:
            nb['metadata']['name'] = u''

        with atomic_writing(os_path, encoding='utf-8') as f:
            current.write(nb, f, u'json')

    def _save_file(self, os_path, model, name='', path=''):
        """save a non-notebook file"""
        fmt = model.get('format', None)
        if fmt not in {'text', 'base64'}:
            raise web.HTTPError(400, "Must specify format of file contents as 'text' or 'base64'")
        try:
            content = model['content']
            if fmt == 'text':
                bcontent = content.encode('utf8')
            else:
                b64_bytes = content.encode('ascii')
                bcontent = base64.decodestring(b64_bytes)
        except Exception as e:
            raise web.HTTPError(400, u'Encoding error saving %s: %s' % (os_path, e))
        with atomic_writing(os_path, text=False) as f:
            f.write(bcontent)

    def _save_directory(self, os_path, model, name='', path=''):
        """create a directory"""
        if is_hidden(os_path, self.root_dir):
            raise web.HTTPError(400, u'Cannot create hidden directory %r' % os_path)
        if not os.path.exists(os_path):
            os.mkdir(os_path)
        elif not os.path.isdir(os_path):
            raise web.HTTPError(400, u'Not a directory: %s' % (os_path))
        else:
            self.log.debug("Directory %r already exists", os_path)

    def save(self, model, name='', path=''):
        """Save the file model and return the model with no content."""
        path = path.strip('/')

        if 'type' not in model:
            raise web.HTTPError(400, u'No file type provided')
        if 'content' not in model and model['type'] != 'directory':
            raise web.HTTPError(400, u'No file content provided')

        # One checkpoint should always exist
        if self.file_exists(name, path) and not self.list_checkpoints(name, path):
            self.create_checkpoint(name, path)

        new_path = model.get('path', path).strip('/')
        new_name = model.get('name', name)

        if path != new_path or name != new_name:
            self.rename(name, path, new_name, new_path)

        os_path = self._get_os_path(new_name, new_path)
        self.log.debug("Saving %s", os_path)
        try:
            if model['type'] == 'notebook':
                self._save_notebook(os_path, model, new_name, new_path)
            elif model['type'] == 'file':
                self._save_file(os_path, model, new_name, new_path)
            elif model['type'] == 'directory':
                self._save_directory(os_path, model, new_name, new_path)
            else:
                raise web.HTTPError(400, "Unhandled contents type: %s" % model['type'])
        except web.HTTPError:
            raise
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while saving file: %s %s' % (os_path, e))

        model = self.get_model(new_name, new_path, content=False)
        return model

    def update(self, model, name, path=''):
        """Update the file's path and/or name

        For use in PATCH requests, to enable renaming a file without
        re-uploading its contents. Only used for renaming at the moment.
        """
        path = path.strip('/')
        new_name = model.get('name', name)
        new_path = model.get('path', path).strip('/')
        if path != new_path or name != new_name:
            self.rename(name, path, new_name, new_path)
        model = self.get_model(new_name, new_path, content=False)
        return model

    def delete(self, name, path=''):
        """Delete file by name and path."""
        path = path.strip('/')
        os_path = self._get_os_path(name, path)
        rm = os.unlink
        if os.path.isdir(os_path):
            listing = os.listdir(os_path)
            # don't delete non-empty directories (checkpoints dir doesn't count)
            if listing and listing != [self.checkpoint_dir]:
                raise web.HTTPError(400, u'Directory %s not empty' % os_path)
        elif not os.path.isfile(os_path):
            raise web.HTTPError(404, u'File does not exist: %s' % os_path)

        # clear checkpoints
        for checkpoint in self.list_checkpoints(name, path):
            checkpoint_id = checkpoint['id']
            cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
            if os.path.isfile(cp_path):
                self.log.debug("Unlinking checkpoint %s", cp_path)
                os.unlink(cp_path)

        if os.path.isdir(os_path):
            self.log.debug("Removing directory %s", os_path)
            shutil.rmtree(os_path)
        else:
            self.log.debug("Unlinking file %s", os_path)
            rm(os_path)

    def rename(self, old_name, old_path, new_name, new_path):
        """Rename a file."""
        old_path = old_path.strip('/')
        new_path = new_path.strip('/')
        if new_name == old_name and new_path == old_path:
            return

        new_os_path = self._get_os_path(new_name, new_path)
        old_os_path = self._get_os_path(old_name, old_path)

        # Should we proceed with the move?
        if os.path.isfile(new_os_path):
            raise web.HTTPError(409, u'File with name already exists: %s' % new_os_path)

        # Move the file
        try:
            shutil.move(old_os_path, new_os_path)
        except Exception as e:
            raise web.HTTPError(500, u'Unknown error renaming file: %s %s' % (old_os_path, e))

        # Move the checkpoints
        old_checkpoints = self.list_checkpoints(old_name, old_path)
        for cp in old_checkpoints:
            checkpoint_id = cp['id']
            old_cp_path = self.get_checkpoint_path(checkpoint_id, old_name, old_path)
            new_cp_path = self.get_checkpoint_path(checkpoint_id, new_name, new_path)
            if os.path.isfile(old_cp_path):
                self.log.debug("Renaming checkpoint %s -> %s", old_cp_path, new_cp_path)
                shutil.move(old_cp_path, new_cp_path)

    # Checkpoint-related utilities

    def get_checkpoint_path(self, checkpoint_id, name, path=''):
        """find the path to a checkpoint"""
        path = path.strip('/')
        basename, ext = os.path.splitext(name)
        filename = u"{name}-{checkpoint_id}{ext}".format(
            name=basename,
            checkpoint_id=checkpoint_id,
            ext=ext,
        )
        os_path = self._get_os_path(path=path)
        cp_dir = os.path.join(os_path, self.checkpoint_dir)
        ensure_dir_exists(cp_dir)
        cp_path = os.path.join(cp_dir, filename)
        return cp_path

    def get_checkpoint_model(self, checkpoint_id, name, path=''):
        """construct the info dict for a given checkpoint"""
        path = path.strip('/')
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        stats = os.stat(cp_path)
        last_modified = tz.utcfromtimestamp(stats.st_mtime)
        info = dict(
            id = checkpoint_id,
            last_modified = last_modified,
        )
        return info

    # public checkpoint API

    def create_checkpoint(self, name, path=''):
        """Create a checkpoint from the current state of a file"""
        path = path.strip('/')
        src_path = self._get_os_path(name, path)
        # only the one checkpoint ID:
        checkpoint_id = u"checkpoint"
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        self.log.debug("creating checkpoint for %s", name)
        self._copy(src_path, cp_path)

        # return the checkpoint info
        return self.get_checkpoint_model(checkpoint_id, name, path)

    def list_checkpoints(self, name, path=''):
        """list the checkpoints for a given file

        This contents manager currently only supports one checkpoint per file.
        """
        path = path.strip('/')
        checkpoint_id = "checkpoint"
        os_path = self.get_checkpoint_path(checkpoint_id, name, path)
        if not os.path.exists(os_path):
            return []
        else:
            return [self.get_checkpoint_model(checkpoint_id, name, path)]


    def restore_checkpoint(self, checkpoint_id, name, path=''):
        """restore a file to a checkpointed state"""
        path = path.strip('/')
        self.log.info("restoring %s from checkpoint %s", name, checkpoint_id)
        nb_path = self._get_os_path(name, path)
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        if not os.path.isfile(cp_path):
            self.log.debug("checkpoint file does not exist: %s", cp_path)
            raise web.HTTPError(404,
                u'checkpoint does not exist: %s-%s' % (name, checkpoint_id)
            )
        # ensure notebook is readable (never restore from an unreadable notebook)
        if cp_path.endswith('.ipynb'):
            with io.open(cp_path, 'r', encoding='utf-8') as f:
                current.read(f, u'json')
        self._copy(cp_path, nb_path)
        self.log.debug("copying %s -> %s", cp_path, nb_path)

    def delete_checkpoint(self, checkpoint_id, name, path=''):
        """delete a file's checkpoint"""
        path = path.strip('/')
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        if not os.path.isfile(cp_path):
            raise web.HTTPError(404,
                u'Checkpoint does not exist: %s%s-%s' % (path, name, checkpoint_id)
            )
        self.log.debug("unlinking %s", cp_path)
        os.unlink(cp_path)

    def info_string(self):
        return "Serving notebooks from local directory: %s" % self.root_dir

    def get_kernel_path(self, name, path='', model=None):
        """Return the initial working dir a kernel associated with a given notebook"""
        return os.path.join(self.root_dir, path)

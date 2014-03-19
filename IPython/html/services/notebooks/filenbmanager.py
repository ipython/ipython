"""A notebook manager that uses the local file system for storage.

Authors:

* Brian Granger
* Zach Sailer
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

import io
import os
import glob
import shutil

from tornado import web

from .nbmanager import NotebookManager
from IPython.nbformat import current
from IPython.utils.traitlets import Unicode, Bool, TraitError
from IPython.utils.py3compat import getcwd
from IPython.utils import tz
from IPython.html.utils import is_hidden, to_os_path

def sort_key(item):
    """Case-insensitive sorting."""
    return item['name'].lower()

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class FileNotebookManager(NotebookManager):
    
    save_script = Bool(False, config=True,
        help="""Automatically create a Python script when saving the notebook.
        
        For easier use of import, %run and %load across notebooks, a
        <notebook-name>.py script will be created next to any
        <notebook-name>.ipynb on each save.  This can also be set with the
        short `--script` flag.
        """
    )
    notebook_dir = Unicode(getcwd(), config=True)
    
    def _notebook_dir_changed(self, name, old, new):
        """Do a bit of validation of the notebook dir."""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            self.notebook_dir = os.path.abspath(new)
            return
        if not os.path.exists(new) or not os.path.isdir(new):
            raise TraitError("notebook dir %r is not a directory" % new)

    checkpoint_dir = Unicode(config=True,
        help="""The location in which to keep notebook checkpoints
        
        By default, it is notebook-dir/.ipynb_checkpoints
        """
    )
    def _checkpoint_dir_default(self):
        return os.path.join(self.notebook_dir, '.ipynb_checkpoints')
    
    def _checkpoint_dir_changed(self, name, old, new):
        """do a bit of validation of the checkpoint dir"""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            abs_new = os.path.abspath(new)
            self.checkpoint_dir = abs_new
            return
        if os.path.exists(new) and not os.path.isdir(new):
            raise TraitError("checkpoint dir %r is not a directory" % new)
        if not os.path.exists(new):
            self.log.info("Creating checkpoint dir %s", new)
            try:
                os.mkdir(new)
            except:
                raise TraitError("Couldn't create checkpoint dir %r" % new)
    
    def _copy(self, src, dest):
        """copy src to dest
        
        like shutil.copy2, but log errors in copystat
        """
        shutil.copyfile(src, dest)
        try:
            shutil.copystat(src, dest)
        except OSError as e:
            self.log.debug("copystat on %s failed", dest, exc_info=True)
    
    def get_notebook_names(self, path=''):
        """List all notebook names in the notebook dir and path."""
        path = path.strip('/')
        if not os.path.isdir(self._get_os_path(path=path)):
            raise web.HTTPError(404, 'Directory not found: ' + path)
        names = glob.glob(self._get_os_path('*'+self.filename_ext, path))
        names = [os.path.basename(name)
                 for name in names]
        return names

    def path_exists(self, path):
        """Does the API-style path (directory) actually exist?
        
        Parameters
        ----------
        path : string
            The path to check. This is an API path (`/` separated,
            relative to base notebook-dir).
        
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
            relative to base notebook-dir).
        
        Returns
        -------
        exists : bool
            Whether the path is hidden.
        
        """
        path = path.strip('/')
        os_path = self._get_os_path(path=path)
        return is_hidden(os_path, self.notebook_dir)

    def _get_os_path(self, name=None, path=''):
        """Given a notebook name and a URL path, return its file system
        path.

        Parameters
        ----------
        name : string
            The name of a notebook file with the .ipynb extension
        path : string
            The relative URL path (with '/' as separator) to the named
            notebook.

        Returns
        -------
        path : string
            A file system path that combines notebook_dir (location where
            server started), the relative path, and the filename with the
            current operating system's url.
        """
        if name is not None:
            path = path + '/' + name
        return to_os_path(path, self.notebook_dir)

    def notebook_exists(self, name, path=''):
        """Returns a True if the notebook exists. Else, returns False.

        Parameters
        ----------
        name : string
            The name of the notebook you are checking.
        path : string
            The relative path to the notebook (with '/' as separator)

        Returns
        -------
        bool
        """
        path = path.strip('/')
        nbpath = self._get_os_path(name, path=path)
        return os.path.isfile(nbpath)

    # TODO: Remove this after we create the contents web service and directories are
    # no longer listed by the notebook web service.
    def list_dirs(self, path):
        """List the directories for a given API style path."""
        path = path.strip('/')
        os_path = self._get_os_path('', path)
        if not os.path.isdir(os_path):
            raise web.HTTPError(404, u'directory does not exist: %r' % os_path)
        elif is_hidden(os_path, self.notebook_dir):
            self.log.info("Refusing to serve hidden directory, via 404 Error")
            raise web.HTTPError(404, u'directory does not exist: %r' % os_path)
        dir_names = os.listdir(os_path)
        dirs = []
        for name in dir_names:
            os_path = self._get_os_path(name, path)
            if os.path.isdir(os_path) and not is_hidden(os_path, self.notebook_dir)\
                    and self.should_list(name):
                try:
                    model = self.get_dir_model(name, path)
                except IOError:
                    pass
                dirs.append(model)
        dirs = sorted(dirs, key=sort_key)
        return dirs

    # TODO: Remove this after we create the contents web service and directories are
    # no longer listed by the notebook web service.
    def get_dir_model(self, name, path=''):
        """Get the directory model given a directory name and its API style path"""
        path = path.strip('/')
        os_path = self._get_os_path(name, path)
        if not os.path.isdir(os_path):
            raise IOError('directory does not exist: %r' % os_path)
        info = os.stat(os_path)
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        created = tz.utcfromtimestamp(info.st_ctime)
        # Create the notebook model.
        model ={}
        model['name'] = name
        model['path'] = path
        model['last_modified'] = last_modified
        model['created'] = created
        model['type'] = 'directory'
        return model

    def list_notebooks(self, path):
        """Returns a list of dictionaries that are the standard model
        for all notebooks in the relative 'path'.
        
        Parameters
        ----------
        path : str
            the URL path that describes the relative path for the
            listed notebooks
        
        Returns
        -------
        notebooks : list of dicts
            a list of the notebook models without 'content'
        """
        path = path.strip('/')
        notebook_names = self.get_notebook_names(path)
        notebooks = [self.get_notebook(name, path, content=False)
                        for name in notebook_names if self.should_list(name)]
        notebooks = sorted(notebooks, key=sort_key)
        return notebooks

    def get_notebook(self, name, path='', content=True):
        """ Takes a path and name for a notebook and returns its model
        
        Parameters
        ----------
        name : str
            the name of the notebook
        path : str
            the URL path that describes the relative path for
            the notebook
            
        Returns
        -------
        model : dict
            the notebook model. If contents=True, returns the 'contents' 
            dict in the model as well.
        """
        path = path.strip('/')
        if not self.notebook_exists(name=name, path=path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % name)
        os_path = self._get_os_path(name, path)
        info = os.stat(os_path)
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        created = tz.utcfromtimestamp(info.st_ctime)
        # Create the notebook model.
        model ={}
        model['name'] = name
        model['path'] = path
        model['last_modified'] = last_modified
        model['created'] = created
        model['type'] = 'notebook'
        if content:
            with io.open(os_path, 'r', encoding='utf-8') as f:
                try:
                    nb = current.read(f, u'json')
                except Exception as e:
                    raise web.HTTPError(400, u"Unreadable Notebook: %s %s" % (os_path, e))
            self.mark_trusted_cells(nb, name, path)
            model['content'] = nb
        return model

    def save_notebook(self, model, name='', path=''):
        """Save the notebook model and return the model with no content."""
        path = path.strip('/')

        if 'content' not in model:
            raise web.HTTPError(400, u'No notebook JSON data provided')

        # One checkpoint should always exist
        if self.notebook_exists(name, path) and not self.list_checkpoints(name, path):
            self.create_checkpoint(name, path)

        new_path = model.get('path', path).strip('/')
        new_name = model.get('name', name)

        if path != new_path or name != new_name:
            self.rename_notebook(name, path, new_name, new_path)

        # Save the notebook file
        os_path = self._get_os_path(new_name, new_path)
        nb = current.to_notebook_json(model['content'])
        
        self.check_and_sign(nb, new_name, new_path)
        
        if 'name' in nb['metadata']:
            nb['metadata']['name'] = u''
        try:
            self.log.debug("Autosaving notebook %s", os_path)
            with io.open(os_path, 'w', encoding='utf-8') as f:
                current.write(nb, f, u'json')
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while autosaving notebook: %s %s' % (os_path, e))

        # Save .py script as well
        if self.save_script:
            py_path = os.path.splitext(os_path)[0] + '.py'
            self.log.debug("Writing script %s", py_path)
            try:
                with io.open(py_path, 'w', encoding='utf-8') as f:
                    current.write(nb, f, u'py')
            except Exception as e:
                raise web.HTTPError(400, u'Unexpected error while saving notebook as script: %s %s' % (py_path, e))

        model = self.get_notebook(new_name, new_path, content=False)
        return model

    def update_notebook(self, model, name, path=''):
        """Update the notebook's path and/or name"""
        path = path.strip('/')
        new_name = model.get('name', name)
        new_path = model.get('path', path).strip('/')
        if path != new_path or name != new_name:
            self.rename_notebook(name, path, new_name, new_path)
        model = self.get_notebook(new_name, new_path, content=False)
        return model

    def delete_notebook(self, name, path=''):
        """Delete notebook by name and path."""
        path = path.strip('/')
        os_path = self._get_os_path(name, path)
        if not os.path.isfile(os_path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % os_path)
        
        # clear checkpoints
        for checkpoint in self.list_checkpoints(name, path):
            checkpoint_id = checkpoint['id']
            cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
            if os.path.isfile(cp_path):
                self.log.debug("Unlinking checkpoint %s", cp_path)
                os.unlink(cp_path)
        
        self.log.debug("Unlinking notebook %s", os_path)
        os.unlink(os_path)

    def rename_notebook(self, old_name, old_path, new_name, new_path):
        """Rename a notebook."""
        old_path = old_path.strip('/')
        new_path = new_path.strip('/')
        if new_name == old_name and new_path == old_path:
            return
        
        new_os_path = self._get_os_path(new_name, new_path)
        old_os_path = self._get_os_path(old_name, old_path)

        # Should we proceed with the move?
        if os.path.isfile(new_os_path):
            raise web.HTTPError(409, u'Notebook with name already exists: %s' % new_os_path)
        if self.save_script:
            old_py_path = os.path.splitext(old_os_path)[0] + '.py'
            new_py_path = os.path.splitext(new_os_path)[0] + '.py'
            if os.path.isfile(new_py_path):
                raise web.HTTPError(409, u'Python script with name already exists: %s' % new_py_path)

        # Move the notebook file
        try:
            os.rename(old_os_path, new_os_path)
        except Exception as e:
            raise web.HTTPError(500, u'Unknown error renaming notebook: %s %s' % (old_os_path, e))

        # Move the checkpoints
        old_checkpoints = self.list_checkpoints(old_name, old_path)
        for cp in old_checkpoints:
            checkpoint_id = cp['id']
            old_cp_path = self.get_checkpoint_path(checkpoint_id, old_name, old_path)
            new_cp_path = self.get_checkpoint_path(checkpoint_id, new_name, new_path)
            if os.path.isfile(old_cp_path):
                self.log.debug("Renaming checkpoint %s -> %s", old_cp_path, new_cp_path)
                os.rename(old_cp_path, new_cp_path)

        # Move the .py script
        if self.save_script:
            os.rename(old_py_path, new_py_path)
  
    # Checkpoint-related utilities
    
    def get_checkpoint_path(self, checkpoint_id, name, path=''):
        """find the path to a checkpoint"""
        path = path.strip('/')
        basename, _ = os.path.splitext(name)
        filename = u"{name}-{checkpoint_id}{ext}".format(
            name=basename,
            checkpoint_id=checkpoint_id,
            ext=self.filename_ext,
        )
        cp_path = os.path.join(path, self.checkpoint_dir, filename)
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
        """Create a checkpoint from the current state of a notebook"""
        path = path.strip('/')
        nb_path = self._get_os_path(name, path)
        # only the one checkpoint ID:
        checkpoint_id = u"checkpoint"
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        self.log.debug("creating checkpoint for notebook %s", name)
        if not os.path.exists(self.checkpoint_dir):
            os.mkdir(self.checkpoint_dir)
        self._copy(nb_path, cp_path)
        
        # return the checkpoint info
        return self.get_checkpoint_model(checkpoint_id, name, path)
    
    def list_checkpoints(self, name, path=''):
        """list the checkpoints for a given notebook
        
        This notebook manager currently only supports one checkpoint per notebook.
        """
        path = path.strip('/')
        checkpoint_id = "checkpoint"
        path = self.get_checkpoint_path(checkpoint_id, name, path)
        if not os.path.exists(path):
            return []
        else:
            return [self.get_checkpoint_model(checkpoint_id, name, path)]
        
    
    def restore_checkpoint(self, checkpoint_id, name, path=''):
        """restore a notebook to a checkpointed state"""
        path = path.strip('/')
        self.log.info("restoring Notebook %s from checkpoint %s", name, checkpoint_id)
        nb_path = self._get_os_path(name, path)
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        if not os.path.isfile(cp_path):
            self.log.debug("checkpoint file does not exist: %s", cp_path)
            raise web.HTTPError(404,
                u'Notebook checkpoint does not exist: %s-%s' % (name, checkpoint_id)
            )
        # ensure notebook is readable (never restore from an unreadable notebook)
        with io.open(cp_path, 'r', encoding='utf-8') as f:
            current.read(f, u'json')
        self._copy(cp_path, nb_path)
        self.log.debug("copying %s -> %s", cp_path, nb_path)
    
    def delete_checkpoint(self, checkpoint_id, name, path=''):
        """delete a notebook's checkpoint"""
        path = path.strip('/')
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        if not os.path.isfile(cp_path):
            raise web.HTTPError(404,
                u'Notebook checkpoint does not exist: %s%s-%s' % (path, name, checkpoint_id)
            )
        self.log.debug("unlinking %s", cp_path)
        os.unlink(cp_path)
    
    def info_string(self):
        return "Serving notebooks from local directory: %s" % self.notebook_dir

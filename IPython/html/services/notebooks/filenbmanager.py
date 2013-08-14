"""A notebook manager that uses the local file system for storage.

Authors:

* Brian Granger
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

import datetime
import io
import os
import glob
import shutil

from unicodedata import normalize

from tornado import web

from .nbmanager import NotebookManager
from IPython.nbformat import current
from IPython.utils.traitlets import Unicode, Dict, Bool, TraitError
from IPython.utils import tz

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
    
    filename_ext = Unicode(u'.ipynb')

    
    def get_notebook_names(self, path):
        """List all notebook names in the notebook dir."""
        names = glob.glob(self.get_os_path('*'+self.filename_ext, path))
        names = [os.path.basename(name)
                 for name in names]
        return names
        
    def list_notebooks(self, path):
        """List all notebooks in the notebook dir."""
        notebook_names = self.get_notebook_names(path)
        notebooks = []
        for name in notebook_names:
            model = self.notebook_model(name, path, content=False)
            notebooks.append(model)
        return notebooks

    def change_notebook(self, data, notebook_name, notebook_path=None):
        """Changes notebook"""
        changes = data.keys()
        response = 200
        for change in changes:
            full_path = self.get_os_path(notebook_name, notebook_path)
            if change == "name":
                new_path = self.get_os_path(data['name'], notebook_path)
                if not os.path.isfile(new_path):
                    os.rename(full_path,
                        self.get_os_path(data['name'], notebook_path))
                    notebook_name = data['name']
                else:
                    response = 409
            if change == "path":
                new_path = self.get_os_path(data['name'], data['path'])
                stutil.move(full_path, new_path)
                notebook_path = data['path']
            if change == "content":
                self.save_notebook(data, notebook_name, notebook_path)
        model = self.notebook_model(notebook_name, notebook_path)
        return model, response

    def notebook_exists(self, name, path):
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
        path = self.get_os_path(name, path)
        return os.path.isfile(path)

    def get_os_path(self, fname, path='/'):
        """Given a notebook name and a server URL path, return its file system
        path.
        
        Parameters
        ----------
        fname : string
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
        parts = path.split('/')
        parts = [p for p in parts if p != ''] # remove duplicate splits
        parts += [fname]
        path = os.path.join(self.notebook_dir, *parts)
        return path

    def read_notebook_object_from_path(self, path):
        """read a notebook object from a path"""
        info = os.stat(path)
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        with open(path,'r') as f:
            s = f.read()
            try:
                # v1 and v2 and json in the .ipynb files.
                nb = current.reads(s, u'json')
            except ValueError as e:
                msg = u"Unreadable Notebook: %s" % e
                raise web.HTTPError(400, msg, reason=msg)
        return last_modified, nb
    
    def read_notebook_object(self, notebook_name, notebook_path=None):
        """Get the Notebook representation of a notebook by notebook_name."""
        path = self.get_os_path(notebook_name, notebook_path)
        if not os.path.isfile(path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_name)
        last_modified, nb = self.read_notebook_object_from_path(path)
        # Always use the filename as the notebook name.
        # Eventually we will get rid of the notebook name in the metadata
        # but for now, that name is just an empty string. Until the notebooks
        # web service knows about names in URLs we still pass the name
        # back to the web app using the metadata though.
        nb.metadata.name = os.path.splitext(os.path.basename(path))[0]
        return last_modified, nb
    
    def write_notebook_object(self, nb, notebook_name=None, notebook_path=None, new_name= None):
        """Save an existing notebook object by notebook_name."""
        if new_name == None:
            try:
                new_name = normalize('NFC', nb.metadata.name)
            except AttributeError:
                raise web.HTTPError(400, u'Missing notebook name')

        new_path = notebook_path
        old_name = notebook_name
        old_checkpoints = self.list_checkpoints(old_name)
        
        path = self.get_os_path(new_name, new_path)
        
        # Right before we save the notebook, we write an empty string as the
        # notebook name in the metadata. This is to prepare for removing
        # this attribute entirely post 1.0. The web app still uses the metadata
        # name for now.
        nb.metadata.name = u''

        try:
            self.log.debug("Autosaving notebook %s", path)
            with open(path,'w') as f:
                current.write(nb, f, u'json')
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while autosaving notebook: %s' % e)

        # save .py script as well
        if self.save_script:
            pypath = os.path.splitext(path)[0] + '.py'
            self.log.debug("Writing script %s", pypath)
            try:
                with io.open(pypath,'w', encoding='utf-8') as f:
                    current.write(nb, f, u'py')
            except Exception as e:
                raise web.HTTPError(400, u'Unexpected error while saving notebook as script: %s' % e)
        
        if old_name != None:
            # remove old files if the name changed
            if old_name != new_name:            
                # remove renamed original, if it exists
                old_path = self.get_os_path(old_name, notebook_path)
                if os.path.isfile(old_path):
                    self.log.debug("unlinking notebook %s", old_path)
                    os.unlink(old_path)
            
                # cleanup old script, if it exists
                if self.save_script:
                    old_pypath = os.path.splitext(old_path)[0] + '.py'
                    if os.path.isfile(old_pypath):
                        self.log.debug("unlinking script %s", old_pypath)
                        os.unlink(old_pypath)
                
                # rename checkpoints to follow file
                for cp in old_checkpoints:
                    checkpoint_id = cp['checkpoint_id']
                    old_cp_path = self.get_checkpoint_path_by_name(old_name, checkpoint_id)
                    new_cp_path = self.get_checkpoint_path_by_name(new_name, checkpoint_id)
                    if os.path.isfile(old_cp_path):
                        self.log.debug("renaming checkpoint %s -> %s", old_cp_path, new_cp_path)
                        os.rename(old_cp_path, new_cp_path)
            
        return new_name
            
    def delete_notebook(self, notebook_name, notebook_path):
        """Delete notebook by notebook_name."""
        nb_path = self.get_os_path(notebook_name, notebook_path)
        if not os.path.isfile(nb_path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_name)
        
        # clear checkpoints
        for checkpoint in self.list_checkpoints(notebook_name):
            checkpoint_id = checkpoint['checkpoint_id']
            path = self.get_checkpoint_path(notebook_name, checkpoint_id)
            self.log.debug(path)
            if os.path.isfile(path):
                self.log.debug("unlinking checkpoint %s", path)
                os.unlink(path)
        
        self.log.debug("unlinking notebook %s", nb_path)
        os.unlink(nb_path)

    def increment_filename(self, basename, notebook_path=None):
        """Return a non-used filename of the form basename<int>.
        
        This searches through the filenames (basename0, basename1, ...)
        until is find one that is not already being used. It is used to
        create Untitled and Copy names that are unique.
        """
        i = 0
        while True:
            name = u'%s%i.ipynb' % (basename,i)
            path = self.get_os_path(name, notebook_path)
            if not os.path.isfile(path):
                break
            else:
                i = i+1
        return name
    
    # Checkpoint-related utilities
    
    def get_checkpoint_path_by_name(self, name, checkpoint_id, notebook_path=None):
        """Return a full path to a notebook checkpoint, given its name and checkpoint id."""
        filename = u"{name}-{checkpoint_id}{ext}".format(
            name=name,
            checkpoint_id=checkpoint_id,
            ext=self.filename_ext,
        )
        if notebook_path ==None:
            path = os.path.join(self.checkpoint_dir, filename)
        else:
            path = os.path.join(notebook_path, self.checkpoint_dir, filename)
        return path
    
    def get_checkpoint_path(self, notebook_name, checkpoint_id, notebook_path=None):
        """find the path to a checkpoint"""
        name = notebook_name
        return self.get_checkpoint_path_by_name(name, checkpoint_id, notebook_path)
    
    def get_checkpoint_info(self, notebook_name, checkpoint_id, notebook_path=None):
        """construct the info dict for a given checkpoint"""
        path = self.get_checkpoint_path(notebook_name, checkpoint_id, notebook_path)
        stats = os.stat(path)
        last_modified = tz.utcfromtimestamp(stats.st_mtime)
        info = dict(
            checkpoint_id = checkpoint_id,
            last_modified = last_modified,
        )
        
        return info
        
    # public checkpoint API
    
    def create_checkpoint(self, notebook_name, notebook_path=None):
        """Create a checkpoint from the current state of a notebook"""
        nb_path = self.get_os_path(notebook_name, notebook_path)
        # only the one checkpoint ID:
        checkpoint_id = u"checkpoint"
        cp_path = self.get_checkpoint_path(notebook_name, checkpoint_id, notebook_path)
        self.log.debug("creating checkpoint for notebook %s", notebook_name)
        if not os.path.exists(self.checkpoint_dir):
            os.mkdir(self.checkpoint_dir)
        shutil.copy2(nb_path, cp_path)
        
        # return the checkpoint info
        return self.get_checkpoint_info(notebook_name, checkpoint_id, notebook_path)
    
    def list_checkpoints(self, notebook_name, notebook_path=None):
        """list the checkpoints for a given notebook
        
        This notebook manager currently only supports one checkpoint per notebook.
        """
        checkpoint_id = "checkpoint"
        path = self.get_checkpoint_path(notebook_name, checkpoint_id, notebook_path)
        if not os.path.exists(path):
            return []
        else:
            return [self.get_checkpoint_info(notebook_name, checkpoint_id, notebook_path)]
        
    
    def restore_checkpoint(self, notebook_name, checkpoint_id, notebook_path=None):
        """restore a notebook to a checkpointed state"""
        self.log.info("restoring Notebook %s from checkpoint %s", notebook_name, checkpoint_id)
        nb_path = self.get_os_path(notebook_name, notebook_path)
        cp_path = self.get_checkpoint_path(notebook_name, checkpoint_id, notebook_path)
        if not os.path.isfile(cp_path):
            self.log.debug("checkpoint file does not exist: %s", cp_path)
            raise web.HTTPError(404,
                u'Notebook checkpoint does not exist: %s-%s' % (notebook_name, checkpoint_id)
            )
        # ensure notebook is readable (never restore from an unreadable notebook)
        last_modified, nb = self.read_notebook_object_from_path(cp_path)
        shutil.copy2(cp_path, nb_path)
        self.log.debug("copying %s -> %s", cp_path, nb_path)
    
    def delete_checkpoint(self, notebook_name, checkpoint_id, notebook_path=None):
        """delete a notebook's checkpoint"""
        path = self.get_checkpoint_path(notebook_name, checkpoint_id, notebook_path)
        if not os.path.isfile(path):
            raise web.HTTPError(404,
                u'Notebook checkpoint does not exist: %s-%s' % (notebook_name, checkpoint_id)
            )
        self.log.debug("unlinking %s", path)
        os.unlink(path)
    
    def info_string(self):
        return "Serving notebooks from local directory: %s" % self.notebook_dir

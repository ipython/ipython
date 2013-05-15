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

from tornado import web

from .nbmanager import NotebookManager
from IPython.nbformat import current
from IPython.utils.traitlets import Unicode, Dict, Bool, TraitError

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

    # Map notebook names to notebook_ids
    rev_mapping = Dict()
    
    def get_notebook_names(self):
        """List all notebook names in the notebook dir."""
        names = glob.glob(os.path.join(self.notebook_dir,
                                       '*' + self.filename_ext))
        names = [os.path.splitext(os.path.basename(name))[0]
                 for name in names]
        return names

    def list_notebooks(self):
        """List all notebooks in the notebook dir."""
        names = self.get_notebook_names()

        data = []
        for name in names:
            if name not in self.rev_mapping:
                notebook_id = self.new_notebook_id(name)
            else:
                notebook_id = self.rev_mapping[name]
            data.append(dict(notebook_id=notebook_id,name=name))
        data = sorted(data, key=lambda item: item['name'])
        return data

    def new_notebook_id(self, name):
        """Generate a new notebook_id for a name and store its mappings."""
        notebook_id = super(FileNotebookManager, self).new_notebook_id(name)
        self.rev_mapping[name] = notebook_id
        return notebook_id

    def delete_notebook_id(self, notebook_id):
        """Delete a notebook's id in the mapping."""
        name = self.mapping[notebook_id]
        super(FileNotebookManager, self).delete_notebook_id(notebook_id)
        del self.rev_mapping[name]

    def notebook_exists(self, notebook_id):
        """Does a notebook exist?"""
        exists = super(FileNotebookManager, self).notebook_exists(notebook_id)
        if not exists:
            return False
        path = self.get_path_by_name(self.mapping[notebook_id])
        return os.path.isfile(path)
    
    def get_name(self, notebook_id):
        """get a notebook name, raising 404 if not found"""
        try:
            name = self.mapping[notebook_id]
        except KeyError:
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        return name

    def get_path(self, notebook_id):
        """Return a full path to a notebook given its notebook_id."""
        name = self.get_name(notebook_id)
        return self.get_path_by_name(name)

    def get_path_by_name(self, name):
        """Return a full path to a notebook given its name."""
        filename = name + self.filename_ext
        path = os.path.join(self.notebook_dir, filename)
        return path

    def read_notebook_object_from_path(self, path):
        """read a notebook object from a path"""
        info = os.stat(path)
        last_modified = datetime.datetime.utcfromtimestamp(info.st_mtime)
        with open(path,'r') as f:
            s = f.read()
            try:
                # v1 and v2 and json in the .ipynb files.
                nb = current.reads(s, u'json')
            except Exception as e:
                raise web.HTTPError(500, u'Unreadable JSON notebook: %s' % e)
        return last_modified, nb
    
    def read_notebook_object(self, notebook_id):
        """Get the Notebook representation of a notebook by notebook_id."""
        path = self.get_path(notebook_id)
        if not os.path.isfile(path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        last_modified, nb = self.read_notebook_object_from_path(path)
        # Always use the filename as the notebook name.
        nb.metadata.name = os.path.splitext(os.path.basename(path))[0]
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

        old_name = self.mapping[notebook_id]
        old_checkpoints = self.list_checkpoints(notebook_id)
        
        path = self.get_path_by_name(new_name)
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
        
        # remove old files if the name changed
        if old_name != new_name:
            # update mapping
            self.mapping[notebook_id] = new_name
            self.rev_mapping[new_name] = notebook_id
            del self.rev_mapping[old_name]
            
            # remove renamed original, if it exists
            old_path = self.get_path_by_name(old_name)
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
            
        return notebook_id

    def delete_notebook(self, notebook_id):
        """Delete notebook by notebook_id."""
        nb_path = self.get_path(notebook_id)
        if not os.path.isfile(nb_path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        
        # clear checkpoints
        for checkpoint in self.list_checkpoints(notebook_id):
            checkpoint_id = checkpoint['checkpoint_id']
            path = self.get_checkpoint_path(notebook_id, checkpoint_id)
            self.log.debug(path)
            if os.path.isfile(path):
                self.log.debug("unlinking checkpoint %s", path)
                os.unlink(path)
        
        self.log.debug("unlinking notebook %s", nb_path)
        os.unlink(nb_path)
        self.delete_notebook_id(notebook_id)

    def increment_filename(self, basename):
        """Return a non-used filename of the form basename<int>.
        
        This searches through the filenames (basename0, basename1, ...)
        until is find one that is not already being used. It is used to
        create Untitled and Copy names that are unique.
        """
        i = 0
        while True:
            name = u'%s%i' % (basename,i)
            path = self.get_path_by_name(name)
            if not os.path.isfile(path):
                break
            else:
                i = i+1
        return name
    
    # Checkpoint-related utilities
    
    def get_checkpoint_path_by_name(self, name, checkpoint_id):
        """Return a full path to a notebook checkpoint, given its name and checkpoint id."""
        filename = "{name}-{checkpoint_id}{ext}".format(
            name=name,
            checkpoint_id=checkpoint_id,
            ext=self.filename_ext,
        )
        path = os.path.join(self.checkpoint_dir, filename)
        return path
    
    def get_checkpoint_path(self, notebook_id, checkpoint_id):
        """find the path to a checkpoint"""
        name = self.get_name(notebook_id)
        return self.get_checkpoint_path_by_name(name, checkpoint_id)
    
    def get_checkpoint_info(self, notebook_id, checkpoint_id):
        """construct the info dict for a given checkpoint"""
        path = self.get_checkpoint_path(notebook_id, checkpoint_id)
        stats = os.stat(path)
        last_modified = datetime.datetime.utcfromtimestamp(stats.st_mtime)
        info = dict(
            checkpoint_id = checkpoint_id,
            last_modified = last_modified,
        )
        
        return info
        
    # public checkpoint API
    
    def create_checkpoint(self, notebook_id):
        """Create a checkpoint from the current state of a notebook"""
        nb_path = self.get_path(notebook_id)
        # only the one checkpoint ID:
        checkpoint_id = "checkpoint"
        cp_path = self.get_checkpoint_path(notebook_id, checkpoint_id)
        self.log.debug("creating checkpoint for notebook %s", notebook_id)
        if not os.path.exists(self.checkpoint_dir):
            os.mkdir(self.checkpoint_dir)
        shutil.copy2(nb_path, cp_path)
        
        # return the checkpoint info
        return self.get_checkpoint_info(notebook_id, checkpoint_id)
    
    def list_checkpoints(self, notebook_id):
        """list the checkpoints for a given notebook
        
        This notebook manager currently only supports one checkpoint per notebook.
        """
        checkpoint_id = "checkpoint"
        path = self.get_checkpoint_path(notebook_id, checkpoint_id)
        if not os.path.exists(path):
            return []
        else:
            return [self.get_checkpoint_info(notebook_id, checkpoint_id)]
        
    
    def restore_checkpoint(self, notebook_id, checkpoint_id):
        """restore a notebook to a checkpointed state"""
        self.log.info("restoring Notebook %s from checkpoint %s", notebook_id, checkpoint_id)
        nb_path = self.get_path(notebook_id)
        cp_path = self.get_checkpoint_path(notebook_id, checkpoint_id)
        if not os.path.isfile(cp_path):
            self.log.debug("checkpoint file does not exist: %s", cp_path)
            raise web.HTTPError(404,
                u'Notebook checkpoint does not exist: %s-%s' % (notebook_id, checkpoint_id)
            )
        # ensure notebook is readable (never restore from an unreadable notebook)
        last_modified, nb = self.read_notebook_object_from_path(cp_path)
        shutil.copy2(cp_path, nb_path)
        self.log.debug("copying %s -> %s", cp_path, nb_path)
    
    def delete_checkpoint(self, notebook_id, checkpoint_id):
        """delete a notebook's checkpoint"""
        path = self.get_checkpoint_path(notebook_id, checkpoint_id)
        if not os.path.isfile(path):
            raise web.HTTPError(404,
                u'Notebook checkpoint does not exist: %s-%s' % (notebook_id, checkpoint_id)
            )
        self.log.debug("unlinking %s", path)
        os.unlink(path)
    
    def info_string(self):
        return "Serving notebooks from local directory: %s" % self.notebook_dir

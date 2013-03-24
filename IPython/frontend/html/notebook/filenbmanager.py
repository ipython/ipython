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

    def find_path(self, notebook_id):
        """Return a full path to a notebook given its notebook_id."""
        try:
            name = self.mapping[notebook_id]
        except KeyError:
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        return self.get_path_by_name(name)

    def get_path_by_name(self, name):
        """Return a full path to a notebook given its name."""
        filename = name + self.filename_ext
        path = os.path.join(self.notebook_dir, filename)
        return path       

    def read_notebook_object(self, notebook_id):
        """Get the NotebookNode representation of a notebook by notebook_id."""
        path = self.find_path(notebook_id)
        if not os.path.isfile(path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        info = os.stat(path)
        last_modified = datetime.datetime.utcfromtimestamp(info.st_mtime)
        with open(path,'r') as f:
            s = f.read()
            try:
                # v1 and v2 and json in the .ipynb files.
                nb = current.reads(s, u'json')
            except:
                raise web.HTTPError(500, u'Unreadable JSON notebook.')
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
        path = self.get_path_by_name(new_name)
        try:
            with open(path,'w') as f:
                current.write(nb, f, u'json')
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while saving notebook: %s' % e)

        # save .py script as well
        if self.save_script:
            pypath = os.path.splitext(path)[0] + '.py'
            try:
                with io.open(pypath,'w', encoding='utf-8') as f:
                    current.write(nb, f, u'py')
            except Exception as e:
                raise web.HTTPError(400, u'Unexpected error while saving notebook as script: %s' % e)
        
        # remove old files if the name changed
        if old_name != new_name:
            old_path = self.get_path_by_name(old_name)
            if os.path.isfile(old_path):
                os.unlink(old_path)
            if self.save_script:
                old_pypath = os.path.splitext(old_path)[0] + '.py'
                if os.path.isfile(old_pypath):
                    os.unlink(old_pypath)
            self.mapping[notebook_id] = new_name
            self.rev_mapping[new_name] = notebook_id
            del self.rev_mapping[old_name]
        
        return notebook_id

    def delete_notebook(self, notebook_id):
        """Delete notebook by notebook_id."""
        path = self.find_path(notebook_id)
        if not os.path.isfile(path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        os.unlink(path)
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
        
    def info_string(self):
        return "Serving notebooks from local directory: %s" % self.notebook_dir

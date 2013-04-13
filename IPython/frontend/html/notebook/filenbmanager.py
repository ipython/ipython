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
import uuid

from tornado import web

#from .nbmanager import NotebookManager
from IPython.frontend.html.notebook.nbmanager import NotebookManager
from IPython.nbformat import current
from IPython.utils.traitlets import Unicode, Dict, Bool, TraitError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class NonExistentNotebook(Exception):
    pass

class Notebook(object):
    #filename_ext = Unicode(u'.ipynb')
    filename_ext = u'.ipynb'

    def __init__(self):
        self.id = None
        self.name = None
        self.notebook_dir = None
        self.has_name = False

    @staticmethod
    def create(id, notebook_dir):
        nb = Notebook()
        nb.id, nb.notebook_dir = unicode(uuid.uuid4()), notebook_dir
        # I want every notebook to always have an ID and a name
        nb.name = nb.id
        # treat name==id as a special case though
        nb.has_name = False
        return nb

    @staticmethod
    def create_by_name(name, notebook_dir):
        nb = Notebook()
        nb.id = unicode(uuid.uuid4())
        nb.name = name
        nb.notebook_dir = notebook_dir
        nb.has_name = True
        return nb

    def file_path(self):
        return self._file_path(self.name)

    def _file_path(self, name):
        filename = name + self.filename_ext
        path = os.path.join(self.notebook_dir, filename)
        return path

    def script_path(self):
        return self._script_path(self.name)

    def _script_path(self, name):
        filename = name + ".py"
        path = os.path.join(self.notebook_dir, filename)
        return path


    def file_exists(self):
        return os.path.isfile(self.file_path())

    def save(self, nb, save_script=False):
        path = self.file_path()
        with open(self.file_path(),'w') as f:
            current.write(nb, f, u'json')

        # save .py script as well
        if save_script:
            with io.open(self.script_path(),'w', encoding='utf-8') as f:
                current.write(nb, f, u'py')

    def read(self):
        path = self.file_path()
        info = os.stat(self.file_path())
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

    def _delete_name(self, name):
        old_path = self._file_path(name)
        if os.path.isfile(old_path):
            os.unlink(old_path)
        # let's always delete the python file associated with this
        # notebook, it shouldn't be based on whether or not this call
        # was invoked with a flag
        old_pypath = self._script_path(name)
        if os.path.isfile(old_pypath):
            os.unlink(old_pypath)

    def delete_old_name(self, old_name):
        self._delete_name(old_name)

    def delete(self):
        self._delete_name(self.name)
        

        

class NotebookCollection(object):
    def __init__(self):
        self.name_mapping = {} #from name to notebook
        self.id_mapping = {} # from id to notebook


    def by_id(self, id):
        return self.id_mapping[id]

    def by_name(self, name):
        return self.name_mapping[name]

    def create_notebook(self, notebook_dir, name=False):
        if name:
            nb = Notebook.create_by_name(name, notebook_dir)
        else:
            nb = Notebook.create(notebook_dir)
        self.name_mapping[nb.name] = nb
        self.id_mapping[nb.id] = nb
        return nb

    def delete_notebook_id(self, notebook_id):
        return self.delete_notebook(self.by_id(notebook_id))

    def delete_notebook(self, nb):
        nb.delete()
        del self.name_mapping[nb.name]
        del self.id_mapping[nb.id]

    def update_name(self, old_name, new_name):
        notebook = self.by_name(old_name)
        #I assume this is called after the notebook object has been updated
        if not new_name == notebook.name:
            print "there was an error, the notebook your trying to delete already exists"
            print "old notebook_name %s, new_notebook_name %s, notebook.name" \
                % (old_name, new_name, notebook.name)
            assert new_name == notebook.name
        del self.name_mapping[old_name]
        self.name_mapping[new_name] = notebook


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

    def __init__(self, *args, **kwargs):
        super(FileNotebookManager, self).__init__(*args, **kwargs)
        self.nb_collection = NotebookCollection()
        self.untitled_counter = 0
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
            #note this makes it impossible two notebooks with the same
            #name in different directories
            if name not in self.nb_collection.name_mapping:
                #note this puts the notebook into the collection
                notebook = self.nb_collection.create_notebook(
                    self.notebook_dir, name)
            else:
                notebook = self.nb_collection.by_name(name)
            data.append(dict(notebook_id=notebook.id, name=notebook.name))
        data = sorted(data, key=lambda item: item['name'])
        return data

    def delete_notebook_id(self, notebook_id):
        """Delete a notebook's id in the mapping."""
        return self.nb_collection.delete_notebook_id(notebook_id)

    def notebook_exists(self, notebook_id):
        """Does a notebook exist?"""
        return notebook_id in self.nb_collection.id_mapping and \
            self.nb_collection.by_id(notebook_id).file_exists()

    def find_path(self, notebook_id):
        """Return a full path to a notebook given its notebook_id."""
        try:
            notebook = self.nb_collection.by_id(notebook_id)
        except KeyError:
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        return notebook.file_path()

    def read_notebook_object(self, notebook_id):
        """Get the NotebookNode representation of a notebook by notebook_id."""
        notebook = self.nb_collection.by_id(notebook_id)
        if not notebook.file_exists():
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        return notebook.read()

    def get_notebook_id_by_path(self, path):
        """Get the NotebookNode representation of a notebook by notebook_id."""
        import pdb
        #pdb.set_trace()
        temp_notebook_dir = os.path.dirname(path)
        notebook_filename = os.path.split(path)[-1]
        #pdb.set_trace()
        notebook_name = os.path.splitext(os.path.basename(path))[0]
        print "temp_notebook_dir", temp_notebook_dir
        print "notebook_filename", notebook_filename
        print "notebook_name", notebook_name
        
        nb = self.nb_collection.create_notebook(
            temp_notebook_dir, notebook_name)
        return nb.id

    def notebook_dir_for_id(self, notebook_id):
        return self.nb_collection.by_id(notebook_id).notebook_dir

    def write_notebook_object(self, nb, notebook_id=None):
        """Save an existing notebook object by notebook_id."""
        try:
            new_name = nb.metadata.name
        except AttributeError:
            raise web.HTTPError(400, u'Missing notebook name')

        if notebook_id is None:
            notebook = self.nb_collection.create_notebook(
                self.notebook_dir, new_name)
            notebook_id = notebook.id
        if notebook_id not in self.nb_collection.id_mapping:
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)

        notebook = self.nb_collection.by_id(notebook_id)
        old_name = notebook.name
        notebook.name = new_name
        try:
            notebook.save(nb, self.save_script)
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while saving notebook: %s' % e)
        
        # remove old files if the name changed
        if old_name != new_name:
            notebook.delete_old_name(old_name)
            self.nb_collection.update_name(old_name, new_name)
        return notebook_id

    def delete_notebook(self, notebook_id):
        """Delete notebook by notebook_id."""
        self.nb_collection.delete_notebook_id(notebook_id)

    def increment_filename(self, basename):
        """Return a non-used filename of the form basename<int>.
        
        This searches through the filenames (basename0, basename1, ...)
        until is find one that is not already being used. It is used to
        create Untitled and Copy names that are unique.
        """
        while True:
            name = u'%s%i' % (basename, self.untitled_counter)
            self.untitled_counter += 1
            notebook = Notebook.create_by_name(name, self.notebook_dir)
            if not notebook.file_exists():
                return notebook.name
        
    def info_string(self):
        return "Serving notebooks from local directory: %s" % self.notebook_dir


    def new_notebook(self):
        """Create a new notebook and return its notebook_id."""
        name = self.increment_filename('Untitled')
        metadata = current.new_metadata(name=name)
        nb = current.new_notebook(metadata=metadata)
        notebook_id = self.write_notebook_object(nb)
        return notebook_id

    def save_notebook(self, notebook_id, data, name=None, format=u'json'):
        """Save an existing notebook by notebook_id."""
        if format not in self.allowed_formats:
            raise web.HTTPError(415, u'Invalid notebook format: %s' % format)
        try:
            nb = current.reads(data.decode('utf-8'), format)
        except:
            raise web.HTTPError(400, u'Invalid JSON data')
        if name is not None:
            nb.metadata.name = name
        self.write_notebook_object(nb, notebook_id)

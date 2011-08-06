#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import datetime
import os
import uuid

from tornado import web

from IPython.config.configurable import Configurable
from IPython.nbformat import current
from IPython.utils.traitlets import Unicode, List, Dict


#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class NotebookManager(Configurable):

    notebook_dir = Unicode(os.getcwd())
    filename_ext = Unicode(u'.ipynb')
    allowed_formats = List([u'json',u'xml',u'py'])

    # Map notebook_ids to notebook names
    mapping = Dict()
    # Map notebook names to notebook_ids
    rev_mapping = Dict()

    def list_notebooks(self):
        """List all notebooks in the notebook dir.

        This returns a list of dicts of the form::

            dict(notebook_id=notebook,name=name)
        """
        names = os.listdir(self.notebook_dir)
        names = [name.split(u'.')[0] \
            for name in names if name.endswith(self.filename_ext)]
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
        notebook_id = unicode(uuid.uuid4())
        self.mapping[notebook_id] = name
        self.rev_mapping[name] = notebook_id
        return notebook_id

    def delete_notebook_id(self, notebook_id):
        """Delete a notebook's id only. This doesn't delete the actual notebook."""
        name = self.mapping[notebook_id]
        del self.mapping[notebook_id]
        del self.rev_mapping[name]

    def notebook_exists(self, notebook_id):
        """Does a notebook exist?"""
        if notebook_id not in self.mapping:
            return False
        path = self.get_path_by_name(self.mapping[notebook_id])
        if not os.path.isfile(path):
            return False
        return True        

    def find_path(self, notebook_id):
        """Return a full path to a notebook given its notebook_id."""
        try:
            name = self.mapping[notebook_id]
        except KeyError:
            raise web.HTTPError(404)
        return self.get_path_by_name(name)

    def get_path_by_name(self, name):
        """Return a full path to a notebook given its name."""
        filename = name + self.filename_ext
        path = os.path.join(self.notebook_dir, filename)
        return path       

    def get_notebook(self, notebook_id, format=u'json'):
        """Get the representation of a notebook in format by notebook_id."""
        format = unicode(format)
        if format not in self.allowed_formats:
            raise web.HTTPError(415)
        last_modified, nb = self.get_notebook_object(notebook_id)
        data = current.writes(nb, format)
        name = nb.get('name','notebook')
        return last_modified, name, data

    def get_notebook_object(self, notebook_id):
        """Get the NotebookNode representation of a notebook by notebook_id."""
        path = self.find_path(notebook_id)
        if not os.path.isfile(path):
            raise web.HTTPError(404)
        info = os.stat(path)
        last_modified = datetime.datetime.utcfromtimestamp(info.st_mtime)
        try:
            with open(path,'r') as f:
                s = f.read()
                try:
                    # v2 and later have xml in the .ipynb files.
                    nb = current.reads(s, 'xml')
                except:
                    # v1 had json in the .ipynb files.
                    nb = current.reads(s, 'json')
                    # v1 notebooks don't have a name field, so use the filename.
                    nb.name = os.path.split(path)[-1].split(u'.')[0]
        except:
            raise web.HTTPError(404)
        return last_modified, nb

    def save_new_notebook(self, data, name=None, format=u'json'):
        """Save a new notebook and return its notebook_id.

        If a name is passed in, it overrides any values in the notebook data
        and the value in the data is updated to use that value.
        """
        if format not in self.allowed_formats:
            raise web.HTTPError(415)

        try:
            nb = current.reads(data, format)
        except:
            if format == u'xml':
                # v1 notebooks might come in with a format='xml' but be json.
                try:
                    nb = current.reads(data, u'json')
                except:
                    raise web.HTTPError(400)
            else:
                raise web.HTTPError(400)

        if name is None:
            try:
                name = nb.name
            except AttributeError:
                raise web.HTTPError(400)
        nb.name = name

        notebook_id = self.new_notebook_id(name)
        self.save_notebook_object(notebook_id, nb)
        return notebook_id

    def save_notebook(self, notebook_id, data, name=None, format=u'json'):
        """Save an existing notebook by notebook_id."""
        if format not in self.allowed_formats:
            raise web.HTTPError(415)

        try:
            nb = current.reads(data, format)
        except:
            if format == u'xml':
                # v1 notebooks might come in with a format='xml' but be json.
                try:
                    nb = current.reads(data, u'json')
                except:
                    raise web.HTTPError(400)
            else:
                raise web.HTTPError(400)

        if name is not None:
            nb.name = name
        self.save_notebook_object(notebook_id, nb)

    def save_notebook_object(self, notebook_id, nb):
        """Save an existing notebook object by notebook_id."""
        if notebook_id not in self.mapping:
            raise web.HTTPError(404)
        old_name = self.mapping[notebook_id]
        try:
            new_name = nb.name
        except AttributeError:
            raise web.HTTPError(400)
        path = self.get_path_by_name(new_name)
        try:
            with open(path,'w') as f:
                current.write(nb, f, u'xml')
        except:
            raise web.HTTPError(400)
        if old_name != new_name:
            old_path = self.get_path_by_name(old_name)
            if os.path.isfile(old_path):
                os.unlink(old_path)
            self.mapping[notebook_id] = new_name
            self.rev_mapping[new_name] = notebook_id

    def delete_notebook(self, notebook_id):
        """Delete notebook by notebook_id."""
        path = self.find_path(notebook_id)
        if not os.path.isfile(path):
            raise web.HTTPError(404)
        os.unlink(path)
        self.delete_notebook_id(notebook_id)

    def new_notebook(self):
        """Create a new notebook and returns its notebook_id."""
        i = 0
        while True:
            name = u'Untitled%i' % i
            path = self.get_path_by_name(name)
            if not os.path.isfile(path):
                break
            else:
                i = i+1
        notebook_id = self.new_notebook_id(name)
        nb = current.new_notebook(name=name, id=notebook_id)
        with open(path,'w') as f:
            current.write(nb, f, u'xml')
        return notebook_id


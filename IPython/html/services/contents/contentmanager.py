"""A base class contents manager.

Authors:

* Zach Sailer
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
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
import ast
import base64

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current
from IPython.utils.traitlets import List, Dict, Unicode, TraitError
from IPython.utils import tz

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ContentManager(LoggingConfigurable):
    
    content_dir = Unicode(os.getcwdu(), config=True, help="""
            The directory to use for contents.
            """)

    def get_os_path(self, fname=None, path='/'):
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
        if fname is not None:
            parts += [fname]
        path = os.path.join(self.content_dir, *parts)
        return path

    def get_content_names(self, content_path='/'):
        """Returns list of names in the server's root + relative
        location given by 'content_path'."""
        names = os.listdir(self.get_os_path(None, content_path))
        return names

    def list_contents(self, content_path='/'):
        """Returns a list of dictionaries including info for all
        contents in the location given by 'content_path'.
        
        Parameters
        ----------
        content_path: str
            the relative path/location of the desired files.
        
        Returns
        -------
        contents: list of dicts
            a the contents of each dict includes information for each item 
            in the named location given by 'content_path'.
        """
        names = self.get_content_names(content_path)
        contents = list()
        dirs = list()
        notebooks = list()
        for name in names:
            if os.path.isdir(name) == True:
                dirs.append(os.path.split(name)[1])
            elif os.path.splitext(name)[1] == '.ipynb':
                notebooks.append(os.path.split(name)[1])        
            else:
                contents.append(os.path.split(name)[1])        
        return dirs, notebooks, contents

    def list_contents(self, content_path):
        """List all contents in the named path."""
        dir_names, notebook_names, content_names = self.get_content_names(content_path)
        content_mapping = []
        for name in dir_names:
            model = self.content_model(name, content_path, type='dir')
            content_mapping.append(model)
        for name in content_names:
            model = self.content_model(name, content_path, type='file')
            content_mapping.append(model)
        for name in notebook_names:
            model = self.content_model(name, content_path, type='notebook')
            content_mapping.append(model)
        return content_mapping

    def get_path_by_name(self, name, content_path):
        """Return a full path to content"""
        path = os.path.join(self.content_dir, content_path, name)
        return path

    def content_info(self, name, content_path):
        """Read the content of a named file"""
        file_type = os.path.splitext(os.path.basename(name))[1]
        full_path = self.get_path_by_name(name, content_path)
        info = os.stat(full_path)
        size = info.st_size
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        return last_modified, file_type, size

    def content_model(self, name, content_path, type=None):
        """Create a dict standard model for any file (other than notebooks)"""
        last_modified, file_type, size = self.content_info(name, content_path)
        model = {"name": name,
                    "path": content_path,
                    "type": type,
                    "MIME-type": "",
                    "last_modified (UTC)": last_modified.ctime(),
                    "size": size}
        return model

    def delete_content(self, content_path):
        """Delete a file"""
        os.unlink(os.path.join(self.content_dir, content_path))
        

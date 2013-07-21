"""A base class contents manager.

Authors:

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
            
    contents = List()
    
    def get_content_names(self, content_path):
        names = glob.glob(os.path.join(self.content_dir, content_path,'*'))
        content_names = list()
        dir_names = list()
        for name in names:
            if os.path.isdir(name) == True:
                dir_names.append(os.path.split(name)[1])
            elif os.path.splitext(os.path.basename(name))[1] != '.ipynb':
                content_names.append(os.path.split(name)[1])        
        return dir_names, content_names
        
    def list_contents(self, content_path):
        """List all contents in the named path."""
        dir_names, content_names = self.get_content_names(content_path)
        content_mapping = []
        for name in dir_names:
            model = self.directory_model(name, content_path)
            content_mapping.append(model)
        for name in content_names:
            model = self.content_model(name, content_path)
            content_mapping.append(model)
        return content_mapping

    def get_path_by_name(self, name, content_path):
        """Return a full path to content"""
        path = os.path.join(self.content_dir, content_path, name)
        return path

    def read_content(self, name, content_path):
        file_type = os.path.splitext(os.path.basename(name))[1]
        #Collect contents of file
        with open(name, 'rb') as file_content:
            contents = file_content.read()
        full_path = self.get_path_by_name(name, content_path)
        info = os.stat(full_path)
        size = info.st_size
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        return last_modified, file_type, contents, size
        
    def directory_model(self, name, content_path):
        model = {"name": name,
                    "path": content_path,
                    "type": 'tree'}
        return model

    def content_model(self, name, content_path):
        last_modified, file_type, contents, size = self.read_content(name, content_path)
        model = {"name": name,
                    "path": content_path,
                    "type": file_type,
                    "last_modified": last_modified.ctime(),
                    "size": size}
        return model

    def delete_content(self, content_path):
        os.unlink(os.path.join(self.content_dir, content_path))
        
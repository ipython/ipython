#!/usr/bin/env python
"""NBConvert is a utility for conversion of IPYNB files.

Commandline interface for the NBConvert conversion utility.  Read the
readme.rst for usage information
"""
#-----------------------------------------------------------------------------
#Copyright (c) 2013, the IPython Development Team.
#
#Distributed under the terms of the Modified BSD License.
#
#The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#Imports
#-----------------------------------------------------------------------------

#Stdlib imports
from __future__ import print_function
import sys
import os
import glob

#From IPython
from IPython.core.application import BaseIPythonApplication
from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode, List, Instance, DottedObjectName, Type
from IPython.utils.importstring import import_item

from .exporters.export import export_by_name, get_export_names
from .exporters.exporter import Exporter
from .writers.base import WriterBase
from .utils.config import GlobalConfigurable

#-----------------------------------------------------------------------------
#Classes and functions
#-----------------------------------------------------------------------------

class NbConvertApp(BaseIPythonApplication):
    """Application used to convert to and from notebook file type (*.ipynb)"""


    description = Unicode(
        u"""This application is used to convert notebook files (*.ipynb).
        An ipython config file can be used to batch convert notebooks in the 
        current directory.""")

    examples = Unicode(u"""
        Running `ipython nbconvert` will read the directory config file and then 
        apply it to one or more notebooks.

        Multiple notebooks can be given at the command line in a couple of 
        different ways:
  
        > ipython nbconvert notebook*.ipynb
        > ipython nbconvert notebook1.ipynb notebook2.ipynb
        > ipython nbconvert # this will use the config file to fill in the notebooks
        """)
    
    config_file_name = Unicode(u'ipython_nbconvert_config.py')

    #Writer specific variables
    writer = Instance('IPython.nbconvert.writers.base.WriterBase',  
                      help="""Instance of the writer class used to write the 
                      results of the conversion.""")
    writer_class = DottedObjectName('FilesWriter', config=True, 
                                    help="""Writer class used to write the 
                                    results of the conversion""")
    writer_aliases = {'FilesWriter': 'IPython.nbconvert.writers.files.FilesWriter',
                      'DebugWriter': 'IPython.nbconvert.writers.debug.DebugWriter',
                      'StdoutWriter': 'IPython.nbconvert.writers.stdout.StdoutWriter'}
    writer_factory = Type()

    def _writer_class_changed(self, name, old, new):
        if new in self.writer_aliases:
            new = self.writer_aliases[new]
        self.writer_factory = import_item(new)


    #Other configurable variables
    export_format = Unicode(
        "", config=True,
        help="""If specified, nbconvert will convert the document(s) specified
                using this format.""")

    notebooks = List([], config=True, help="""List of notebooks to convert.
                     Search patterns are supported.""")

    aliases = {'format':'NbConvertApp.export_format',
               'notebooks':'NbConvertApp.notebooks',
               'writer':'NbConvertApp.writer_class'} 


    @catch_config_error
    def initialize(self, argv=None):
        super(NbConvertApp, self).initialize(argv)

        #Register class here to have help with help all
        self.classes.insert(0, Exporter)
        self.classes.insert(0, WriterBase)
        self.classes.insert(0, GlobalConfigurable)

        #Init
        self.init_config(self.extra_args)
        self.init_writer()


    def init_config(self, extra_args):
        """
        Add notebooks to the config if needed.  Glob each notebook to replace
        notebook patterns with filenames.
        """

        #Get any additional notebook patterns from the commandline
        if len(extra_args) > 0:
            for pattern in extra_args:
                self.notebooks.append(pattern)

        #Use glob to replace all the notebook patterns with filenames.
        filenames = []
        for pattern in self.notebooks:
            for filename in glob.glob(pattern):
                if not filename in filenames:
                    filenames.append(filename)
        self.notebooks = filenames


    def init_writer(self):
        """
        Initialize the writer (which is stateless)
        """
        self._writer_class_changed(None, self.writer_class, self.writer_class)
        self.writer = self.writer_factory(parent=self)


    def start(self, argv=None):
        """
        Entrypoint of NbConvert application.
        """

        #Call base
        super(NbConvertApp, self).start()

        #Export each notebook
        for notebook_filename in self.notebooks:

            #Get a unique key for the notebook and set it in the resources object.
            basename = os.path.basename(notebook_filename)
            notebook_name = basename[:basename.rfind('.')]
            resources = {}
            resources['unique_key'] = notebook_name

            #Export & write
            output, resources = export_by_name(self.export_format,
                                               notebook_filename, 
                                               resources=resources,
                                               config=self.config)
            self.writer.write(output, resources, notebook_name=notebook_name)


#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

launch_new_instance = NbConvertApp.launch_instance


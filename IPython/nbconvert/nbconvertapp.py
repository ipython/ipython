#!/usr/bin/env python
"""NBConvert is a utility for conversion of .ipynb files.

Command-line interface for the NbConvert conversion utility.
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
from IPython.core.application import BaseIPythonApplication, base_aliases, base_flags
from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode, List, Instance, DottedObjectName, Type
from IPython.utils.importstring import import_item

from .exporters.export import (
    export_by_name, get_export_names, ExporterNameError, get_exporters
)
from .writers import FilesWriter, StdoutWriter
from .utils.base import NbConvertBase

#-----------------------------------------------------------------------------
#Classes and functions
#-----------------------------------------------------------------------------

nbconvert_aliases = {}
nbconvert_aliases.update(base_aliases)
nbconvert_aliases.update({
    'format' : 'NbConvertApp.export_format',
    'notebooks' : 'NbConvertApp.notebooks',
    'writer' : 'NbConvertApp.writer_class',
})

nbconvert_flags = {}
nbconvert_flags.update(base_flags)
nbconvert_flags.update({
    'stdout' : (
        {'NbConvertApp' : {'writer_class' : "StdoutWriter"}},
        "Write notebook output to stdout instead of files."
        )
})


class NbConvertApp(BaseIPythonApplication):
    """Application used to convert to and from notebook file type (*.ipynb)"""

    name = 'ipython-nbconvert'
    aliases = nbconvert_aliases
    flags = nbconvert_flags
    
    def _classes_default(self):
        classes = []
        classes.extend(get_exporters())
        classes.extend([FilesWriter, StdoutWriter])
        
        return [
            Exporter,
            WriterBase,
            NbConvertBase,
        ]

    description = Unicode(
        u"""This application is used to convert notebook files (*.ipynb).
        An ipython config file can be used to batch convert notebooks in the 
        current directory.""")

    examples = Unicode(u"""
        Multiple notebooks can be given at the command line in a couple of 
        different ways:
  
        > ipython nbconvert notebook*.ipynb
        > ipython nbconvert notebook1.ipynb notebook2.ipynb
        > ipython nbconvert --format sphinx_howto notebook.ipynb
        """)
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
        "full_html", config=True,
        help="""If specified, nbconvert will convert the document(s) specified
                using this format.""")

    notebooks = List([], config=True, help="""List of notebooks to convert.
                     Search patterns are supported.""")

    @catch_config_error
    def initialize(self, argv=None):
        super(NbConvertApp, self).initialize(argv)
        self.init_notebooks()
        self.init_writer()

    def init_notebooks(self):
        """
        Add notebooks to the config if needed.  Glob each notebook to replace
        notebook patterns with filenames.
        """

        #Get any additional notebook patterns from the commandline
        patterns = self.notebooks + self.extra_args

        #Use glob to replace all the notebook patterns with filenames.
        filenames = []
        for pattern in patterns:
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

    def start(self):
        """
        Ran after initialization completed
        """
        super(NbConvertApp, self).start()
        self.convert_notebooks()

    def convert_notebooks(self):
        """
        Convert the notebooks in the self.notebook traitlet
        """
        #Export each notebook
        conversion_success = 0
        for notebook_filename in self.notebooks:

            #Get a unique key for the notebook and set it in the resources object.
            basename = os.path.basename(notebook_filename)
            notebook_name = basename[:basename.rfind('.')]
            resources = {}
            resources['unique_key'] = notebook_name

            #Try to export
            try:
                output, resources = export_by_name(self.export_format,
                                              notebook_filename, 
                                              resources=resources,
                                              config=self.config)
            except ExporterNameError as e:
                print("Error: '%s' exporter not found." % self.export_format,
                      file=sys.stderr)
                print("Known exporters are:",
                      "\n\t" + "\n\t".join(get_export_names()),
                      file=sys.stderr)
                sys.exit(-1)
            #except Exception as e:
                #print("Error: could not export '%s'" % notebook_filename, file=sys.stderr)
                #print(e, file=sys.stderr)
            else:
                self.writer.write(output, resources, notebook_name=notebook_name)
                conversion_success += 1

        #If nothing was converted successfully, help the user.
        if conversion_success == 0:

            #No notebooks were specified, show help.
            if len(self.notebooks) == 0:
                self.print_help()

            #Notebooks were specified, but not converted successfully.  Show how
            #to access help.
            else:
                print('For help, use "ipython nbconvert --help"')


#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

launch_new_instance = NbConvertApp.launch_instance

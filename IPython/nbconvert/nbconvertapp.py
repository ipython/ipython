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

# Stdlib imports
from __future__ import print_function
import sys
import os
import glob

# From IPython
from IPython.core.application import BaseIPythonApplication, base_aliases, base_flags
from IPython.config import catch_config_error, Configurable
from IPython.utils.traitlets import (
    Unicode, List, Instance, DottedObjectName, Type, CaselessStrEnum,
)
from IPython.utils.importstring import import_item

from .exporters.export import export_by_name, get_export_names, ExporterNameError
from IPython.nbconvert import exporters, transformers, writers
from .utils.base import NbConvertBase
from .utils.exceptions import ConversionException

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
        classes = [NbConvertBase]
        for pkg in (exporters, transformers, writers):
            for name in dir(pkg):
                cls = getattr(pkg, name)
                if isinstance(cls, type) and issubclass(cls, Configurable):
                    classes.append(cls)
        return classes

    description = Unicode(
        u"""This application is used to convert notebook files (*.ipynb)
        to various other formats.""")

    examples = Unicode(u"""
        The simplest way to use nbconvert is
        
        > ipython nbconvert mynotebook.ipynb
        
        which will convert mynotebook.ipynb to the default format (probably HTML).
        
        You can specify the export format with `--format`.
        Options include {0}
        
        > ipython nbconvert --format latex mynotebook.ipnynb
        
        You can also pipe the output to stdout, rather than a file
        
        > ipython nbconvert mynotebook.ipynb --stdout
        
        Multiple notebooks can be given at the command line in a couple of 
        different ways:
  
        > ipython nbconvert notebook*.ipynb
        > ipython nbconvert notebook1.ipynb notebook2.ipynb
        
        or you can specify the notebooks list in a config file, containing::
        
            c.NbConvertApp.notebooks = ["my_notebook.ipynb"]
        
        > ipython nbconvert --config mycfg.py
        """.format(get_export_names()))
    # Writer specific variables
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


    # Other configurable variables
    export_format = CaselessStrEnum(get_export_names(),
        default_value="full_html",
        config=True,
        help="""The export format to be used."""
    )

    notebooks = List([], config=True, help="""List of notebooks to convert.
                     Wildcards are supported.
                     Filenames passed positionally will be added to the list.
                     """)

    @catch_config_error
    def initialize(self, argv=None):
        super(NbConvertApp, self).initialize(argv)
        self.init_syspath()
        self.init_notebooks()
        self.init_writer()


    def init_syspath(self):
        """
        Add the cwd to the sys.path ($PYTHONPATH)
        """
        sys.path.insert(0, os.getcwd())
        

    def init_notebooks(self):
        """Construct the list of notebooks.
        If notebooks are passed on the command-line,
        they override notebooks specified in config files.
        Glob each notebook to replace notebook patterns with filenames.
        """

        # Specifying notebooks on the command-line overrides (rather than adds)
        # the notebook list
        if self.extra_args:
            patterns = self.extra_args
        else:
            patterns = self.notebooks

        # Use glob to replace all the notebook patterns with filenames.
        filenames = []
        for pattern in patterns:
            
            # Use glob to find matching filenames.  Allow the user to convert 
            # notebooks without having to type the extension.
            globbed_files = glob.glob(pattern)
            globbed_files.extend(glob.glob(pattern + '.ipynb'))

            for filename in globbed_files:
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
        # Export each notebook
        conversion_success = 0
        for notebook_filename in self.notebooks:

            # Get a unique key for the notebook and set it in the resources object.
            basename = os.path.basename(notebook_filename)
            notebook_name = basename[:basename.rfind('.')]
            resources = {}
            resources['unique_key'] = notebook_name
            resources['output_files_dir'] = '%s_files' % notebook_name

            # Try to export
            try:
                output, resources = export_by_name(self.export_format,
                                              notebook_filename, 
                                              resources=resources,
                                              config=self.config)
            except ExporterNameError as e:
                print("Error while converting '%s': '%s' exporter not found."
                      %(notebook_filename, self.export_format),
                      file=sys.stderr)
                print("Known exporters are:",
                      "\n\t" + "\n\t".join(get_export_names()),
                      file=sys.stderr)
                self.exit(1)
            except ConversionException as e:
                print("Error while converting '%s': %s" %(notebook_filename, e),
                      file=sys.stderr)
                self.exit(1)
            else:
                self.writer.write(output, resources, notebook_name=notebook_name)
                conversion_success += 1

        # If nothing was converted successfully, help the user.
        if conversion_success == 0:
            self.print_help()
            sys.exit(-1)


#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

launch_new_instance = NbConvertApp.launch_instance

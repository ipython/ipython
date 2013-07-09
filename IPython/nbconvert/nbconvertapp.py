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
import io
import os
import yaml
import copy
import glob

#From IPython
from IPython.config.application import Application, catch_config_error
from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, List, Instance, DottedObjectName, Type
from IPython.utils.importstring import import_item

from .exporters.export import export_by_name
from .exporters.exporter import Exporter
from .utils.config import GlobalConfigurable

#-----------------------------------------------------------------------------
#Classes and functions
#-----------------------------------------------------------------------------

class NbConvertApp(Application):
    """Application used to convert to and from notebook file type (*.ipynb)"""

    description = Unicode(
        u"""This application is used to convert notebook files (*.ipynb).
        A yaml file can be used to batch convert notebooks in the current 
        directory.""")

    examples = Unicode(u"""
        Standard
            > ipython nbconvert
            
            Loads the nbconvert.yaml file in the current directory.  The
            nbconvert.yaml is written by the user and contains all of the 
            imformation governing what notebooks will be converted and how.
            For more information about nbconvert YAML, please refer to the 
            nbconvert example repository

        Explicit YAML
            > ipython nbconvert --yaml=foo.yaml

            Loads the foo.yaml file in the current directory.  Behaves like the
            Standard usage case (seen above).

        Simple
            > ipython nbconvert --f=foo bar.ipynb

            Exports bar.ipynb to the "nbconvert_build" subdirectory using the 
            foo format.  Still uses the standard yaml file if it exists.
        """)

    yaml = Unicode(u'nbconvert.yaml', config=True, help="""""")

    export_format = Unicode(
        "", config=True,
        help="""If specified, nbconvert will convert the document(s) specified
                using this format.""")
    
    notebooks = List([], config=True, help="""""")

    writer = Instance('IPython.nbconvert.writers.base.WriterBase',  help="""TODO: Help""")
    writer_class = DottedObjectName('IPython.nbconvert.writers.files.FilesWriter', config=True)
    writer_factory = Type()
    def _writer_class_changed(self, name, old, new):
        self.writer_factory = import_item(new)
    
    aliases = {'f':'NbConvertApp.export_format',
               'yaml':'NbConvertApp.yaml',
               'writer':'NbConvertApp.writer_class'} 

    writer_aliases = {'FilesWriter': ['IPython', 'nbconvert', 'writers', 'files', 'FilesWriter'],
                      'DebugWriter': ['IPython', 'nbconvert', 'writers', 'debug', 'DebugWriter'],
                      'StdoutWriter': ['IPython', 'nbconvert', 'writers', 'stdout', 'StdoutWriter']}

    @catch_config_error
    def initialize(self, argv=None):
        super(NbConvertApp, self).initialize(argv)

        #Register class here to have help with help all
        self.classes.insert(0, Exporter)
        self.classes.insert(0, GlobalConfigurable)

        self.init_configs(self.yaml, self.extra_args)
        self.init_writer()


    def init_configs(self, yaml_filename, extra_args):

        #Read yaml config
        yaml_config = self._process_yaml(yaml_filename)

        #Read the config applied to the writer if it exists.  Use that config
        #as a base for the configs when exporting.
        if 'writer' in yaml_config:

            #Append the name of the writer to the writer key list (config path)
            writer_name = yaml_config['writer'].keys()[0]

            #Use the writer name to determine the writer class.
            if writer_name in self.writer_aliases:

                #Copy the config to the main config in the right destination
                writer_config = Config({writer_name: yaml_config['writer'][writer_name]})
                self.config.merge(writer_config)

                #Set the name to the full name so we can create an instance of 
                #the class.
                writer_name = '.'.join(self.writer_aliases[writer_name])

            self.writer_class = writer_name
            del yaml_config['writer']

        #Use glob to match file names to the pattern filenames from the yaml.
        #Keep separate configs for each notebook in a dictionary for now...
        self.nb_configs = {}
        if 'notebooks' in yaml_config:
            for notebook_pattern in yaml_config['notebooks']:

                if isinstance(notebook_pattern, dict):
                    notebook_pattern = notebook_pattern.keys()[0]

                filenames = glob.glob(notebook_pattern)
                for filename in filenames:

                    #Check that the notebook exists in the extra-args if the
                    #extra args isn't empty.
                    if len(extra_args) == 0 or filename in extra_args:

                        #Copy the config for the pattern string
                        nb_config = Config(yaml_config['notebooks'][notebook_pattern])

                        for format_dict in nb_config['formats']:
                            format_name = format_dict['format']
                            del format_dict['format']
                            format_dict = Config({'Exporter':format_dict})

                            #If the export_format was specified, use only that config.
                            if not self.export_format or self.export_format == format_name:
                                if not (filename, format_name) in self.nb_configs:
                                    self.nb_configs[(filename, format_name)] = Config()
                                self.nb_configs[(filename, format_name)].merge(format_dict)

        else:

            #No notebooks were specified in the yaml.  Check if notebooks were
            #specified via the extra args and that a format was set.
            if len(self.export_format) > 0 and len(extra_args) > 0:
                for filename in extra_args:
                    self.nb_configs[(filename, self.export_format)] = Config()
            else:
                print("Note enough information provided to perform conversion", 
                      file=sys.stderr)

        #Remove 'notebooks' node from config.
        if 'notebooks' in yaml_config: 
            del yaml_config['notebooks']

        #Merge yaml config with user config
        self.config.merge(yaml_config)


    def init_writer(self):
        self._writer_class_changed('writer_class', self.writer_class, self.writer_class)


    def _process_yaml(self, yaml_filename):
        """
        Read a yaml file and return a Config instance.
        """

        #If the file doesn't exist, return an empty config.
        if yaml_filename is None or not os.path.isfile(yaml_filename):
            return Config()
        else:

            #Create a config and merge each yaml document into the config.
            config = Config()
            with open(yaml_filename, "r") as f:
                yaml_docs = yaml.load_all(f)
                for yaml_doc in yaml_docs:
                    yaml_config = Config(yaml_doc)
                    config.merge(yaml_config)
            return config


    def start(self, argv=None):
        """Entrypoint of NbConvert application.

        Parameters
        ----------
        argv : list
            Commandline arguments
        """

        #Call base
        super(NbConvertApp, self).start()

        #Loop through each notebook&format to export.  Create a config that is 
        #the current config merged with all the config options specific to that
        #notebook/format combo.
        for (notebook_filename, format_name), notebook_config in self.nb_configs.items():
            config = copy.deepcopy(self.config)
            config.merge(notebook_config)
            self.writer = self.writer_factory(config=config)

            basename = os.path.basename(notebook_filename)
            notebook_name = basename[:basename.rfind('.')]

            (output, resources, exporter_instance) = export_by_name(format_name, notebook_filename, config=config, notebook_name=notebook_name)
            self.writer.write(notebook_name, exporter_instance.file_extension, output, resources)                


#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    """Application entry point"""

    app = NbConvertApp.instance()
    app.description = __doc__
    app.start(argv=sys.argv)


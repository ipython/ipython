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

#From IPython
from IPython.config.application import Application
from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode, List

from .exporters.export import export_by_name
from .exporters.exporter import Exporter
from .transformers import extractfigure
from .utils.config import GlobalConfigurable
from .writers.file import FileWriter
from .writers.stdout import StdoutWriter

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
            > ipython nbconvert --template=foo bar.ipynb

            Exports bar.ipynb to the "nbconvert_build" subdirectory using the 
            foo template.  Still uses the standard yaml file if it exists.
        """)

    yaml_config = Unicode(u'nbconvert.yaml', config=True, help="""""")

    template = Unicode(
        "", config=True,
        help="""If specified, nbconvert will convert the document(s) specified
                using this template.""")
    
    notebooks = List([], config=True, help="""""")

    writer = Instance('IPython.nbconvert.writers.base.WriterBase',  help="""TODO: Help""")
    writer_class = DottedObjectName('IPython.nbconvert.writers.base.WriterBase', config=True)
    writer_factory = Type()

    def _writer_class_changed(self, name, old, new):
        self.writer_factory = import_item(new)
    

    aliases = {'template':'NbConvertApp.template'} #TODO, writer/yaml also


    def __init__(self, **kwargs):
        """Constructor"""

        #Call base class
        super(NbConvertApp, self).__init__(**kwargs)

        #Register class here to have help with help all
        self.classes.insert(0, Exporter)
        self.classes.insert(0, GlobalConfigurable)

        self._init_writer()


    def _init_writer(self):
        self.writer = self.writer_factory(parent=self)


    def start(self, argv=None):
        """Entrypoint of NbConvert application.
        
        Parameters
        ----------
        argv : list
            Commandline arguments
        """
        
        #Parse the commandline options.
        self.parse_command_line(argv)

        #Call base
        super(NbConvertApp, self).start()

        #Make sure argument count is correct
        if len(self.extra_args) > 2:
            print( "Wrong number of arguments, use --help flag for usage", file=sys.stderr)
            sys.exit(-1)

        #Check for user specified yaml or notebook file.
        yaml_file = 'nbconvert.yaml'
        if len(self.extra_args) > 1:

            #If a template is explicitly set via the commandline, treat the argument
            #as a notebook file.
            if len(self.template.strip()) > 0:
                yaml_file = None

                ipynb_file = self.extra_args[1]

                #Make sure the yaml file exists.
                if not os.path.isfile(ipynb_file):
                    print( "Notebook file '%s' not found" % ipynb_file, file=sys.stderr)
                    sys.exit(-1)

            #Since no template was specified, treat the commandline parameter as
            #a yaml file.
            else:
                yaml_file = self.extra_args[1]

                #Make sure the yaml file exists.
                if not os.path.isfile(yaml_file):
                    print( "Yaml file '%s' not found" % yaml_file, file=sys.stderr)
                    sys.exit(-1)

        #Write the single notebook conversion to the file system.
        if yaml_file is None:
            self._export_and_write(self.template, ipynb_file, FileWriter(config=self.config))
        else:
            with open(yaml_file, "r") as f:
                yaml_docs = yaml.load_all(f)
                for yaml_doc in yaml_docs:
                    self._export_using_yaml(yaml_doc)


    def _export_using_yaml(self, yaml):
        """
        Export a document using the provided yaml structure

        Parameters
        ----------
        yaml : dict
            Yaml document containing parameters for export process.
        """

        #Get the writers from the yaml config (if possible).
        writers = []
        if 'writters' in yaml:
            for (writer_name, writer_yaml) in yaml['writers'].items():
                writers.append(self._writer_from_name(writer_name, writer_yaml))
        else:

            #Create a filewriter by default
            writers.append(FileWriter(config=config))

        #Get the notebooks to export, if no notebooks exist, complain.
        if 'notebooks' in yaml and len(yaml(notebooks)) > 0:
            for (notebook_name, notebook_yaml) in yaml['notebooks'].items():
                pass #TODO
        else:
            raise TypeError('notebooks note specified in yaml')


    def _export_and_write(self, template, ipynb_file, writer, config=None):
        """
        Export a notebook file and write it using the writer provided.

        Paramteres
        ----------
        template : string
            Name of the template to use to export.
        ipynb_file : string
            Filename & path to the notebook file to be converted.
        writer : WriterBase
            Instance of a Writer to use to write the results of the conversion.
        """

        #Export
        (output, resources, exporter) = export_by_name(template, ipynb_file)
        
        #Get the name of the notebook from the filename.  Remove fullpath and
        #file extension.
        basename = os.path.basename(ipynb_file)
        notebook_name = basename[:basename.rfind('.')]

        #Write the output using a notebook writer
        writer.write(notebook_name, exporter.file_extension, output, resources)


    def _writer_from_name(self, writer_name, config_dict=None):
        """
        Create a writer using its class name.  Config the writer using a
        dictionary
        """

        #Map the yaml config to the config system.
        if not config_dict is None:
            config = self._map_dict_to_config(copy.deepcopy(self.config), 
                                              config_dict)

        #Case insensitive compare
        writer_name = writer_name.lower().strip()
        if writer_name == 'filewriter':
            return FileWriter()
        elif writer_name == 'stdoutwriter':
            return StdoutWriter()


    def _map_dict_to_config(self, config, dictionary):
        """
        Map a dictionary to a config object.  Very similar to Config.Merge 
        method but designed to handle dictionaries from YAML.
        """

        to_update = {}
        for (key, value) in dictionary.items():
            if key not in config:
                to_update[key] = value
            else:

                #Check if the value is a dictionary and the destination value is
                #a config.  If so, recursively map.
                if isinstance(value, dict) and isinstance(config[key], Config):
                    self._map_dict_to_config(config[key], value)
                else:
                    to_update[key] = value

        config.update(to_update)
        return config


#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    """Application entry point"""

    app = NbConvertApp.instance()
    app.description = __doc__
    app.start(argv=sys.argv)


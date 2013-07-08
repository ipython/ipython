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
            > ipython nbconvert --template=foo bar.ipynb

            Exports bar.ipynb to the "nbconvert_build" subdirectory using the 
            foo template.  Still uses the standard yaml file if it exists.
        """)

    yaml = Unicode(u'nbconvert.yaml', config=True, help="""""")

    template = Unicode(
        "", config=True,
        help="""If specified, nbconvert will convert the document(s) specified
                using this template.""")
    
    notebooks = List([], config=True, help="""""")

    writer = Instance('IPython.nbconvert.writers.base.WriterBase',  help="""TODO: Help""")
    writer_class = DottedObjectName('IPython.nbconvert.writers.file.FileWriter', config=True)
    writer_factory = Type()
    def _writer_class_changed(self, name, old, new):
        self.writer_factory = import_item(new)
    
    aliases = {'template':'NbConvertApp.template',
               'yaml':'NbConvertApp.yaml',
               'writer':'NbConvertApp.writer_class'} 

    writer_aliases = {'FileWriter': 'IPython.nbconvert.writers.file.FileWriter',
                      'DebugWriter': 'IPython.nbconvert.writers.debug.DebugWriter',
                      'StdoutWriter': 'IPython.nbconvert.writers.stdout.StdoutWriter'}

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
            writer_name = yaml_config['writer'].keys[0]
            writer_config_dict = yaml_config['writer'][writer_name]
            self.config.merge(Config(writer_config_dict))

            #Use the writer name to determine the writer class.
            if writer_name in writer_aliases:
                writer_name = writer_aliases[writer_name]
            self.writer_class = writer_name

        #Use glob to match file names to the pattern filenames from the yaml.
        #Keep separate configs for each notebook in a dictionary for now...
        self.nb_configs = {}
        if 'notebooks' in yaml_config:
            for notebook_pattern in yaml_config['notebooks']:
                filenames = glob.glob(notebook_pattern)
                for filename in filenames:

                    #Check that the notebook exists in the extra-args if the
                    #extra args isn't empty.
                    if len(extra_args) == 0 or filename in extra_args:
                            
                        #Copy the config for the pattern string
                        nb_config = Config(yaml_config['notebooks'][notebook_pattern])

                        #If the template name was specified, remove any other
                        #templates from the config (template name acts as a
                        #filter)
                        if len(self.template) > 0:

                            #Figure out which templates need to be removed.
                            remove_templates = []
                            for template_dict in nb_config['templates']:
                                if not template_dict['template'] == self.template:
                                    remove_templates.append(nb_config['templates'].index(template_dict))

                            #Remove the templates
                            for remove_template in remove_templates:
                                del nb_config['templates'][remove_template]

                        #Merge to existing config for the file, or set as new config.
                        if filename in self.nb_configs:
                            self.nb_configs[filename].merge(nb_config)
                        else:
                            self.nb_configs[filename] = nb_config
        else:

            #No notebooks were specified in the yaml.  Check if notebooks were
            #specified via the extra args and that a template was set.
            if len(self.template) > 0 and len(extra_args) > 0:
                for filename in extra_args:
                    self.nb_configs[filename] = Config()
                    self.nb_configs[filename]['templates'] = [{'template':self.template}]
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

        #Loop through each notebook&template to export.  Create a config that is 
        #the current config merged with all the config options specific to that
        #notebook/template combo.
        for notebook_filename, notebook_config in self.nb_configs.items():
            for template_config in notebook_config['templates']:
                config = copy.deepcopy(self.config)
                config.merge(template_config)

                template_name = config['template']
                self.writer = self.writer_factory(config=config)

                basename = os.path.basename(notebook_filename)
                notebook_name = basename[:basename.rfind('.')]

                (output, resources, exporter_instance) = export_by_name(template_name, notebook_filename, config=config, notebook_name=notebook_name)
                self.writer.write(notebook_name, exporter_instance.file_extension, output, resources)                


#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    """Application entry point"""

    app = NbConvertApp.instance()
    app.description = __doc__
    app.start(argv=sys.argv)


#!/usr/bin/env python
"""
================================================================================

|,---.     |    |                 ,   .|                                   |
||---',   .|--- |---.,---.,---.   |\  ||---.,---.,---.,---..    ,,---.,---.|---
||    |   ||    |   ||   ||   |   | \ ||   ||    |   ||   | \  / |---'|    |
``    `---|`---'`   '`---'`   '   `  `'`---'`---'`---'`   '  `'  `---'`    `---'
      `---'
================================================================================

Highly experimental for now

"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function
import sys
import io
import os

from converters.template import ConverterTemplate
# From IPython

# All the stuff needed for the configurable things
from IPython.config.application import Application
from IPython.config.loader import ConfigFileNotFound
from IPython.utils.traitlets import Unicode, Bool

from converters.transformers import (ExtractFigureTransformer)

from converters.config import GlobalConfigurable

NBCONVERT_DIR = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))

class NbconvertApp(Application):
    """A basic application to convert ipynb files

    """

    stdout = Bool(True, config=True,
            help="""
            Wether to print the converted ipynb file to stdout
            use full do diff files without actually writing a new file
            """)

    write = Bool(False, config=True,
            help="""Shoudl the converted notebook file be written to disk
            along with potential extracted resources.
            """
            )

    fileext = Unicode('txt', config=True,
            help="""Extension of the file that should be written to disk"""
            )

    aliases = {
            'stdout':'NbconvertApp.stdout',
            'write':'NbconvertApp.write',
            }

    flags = {}
    flags['no-stdout'] = (
        {'NbconvertApp' : {'stdout' : False}},
    """Do not print converted file to stdout, equivalent to --stdout=False
    """
    )

    def __init__(self, **kwargs):
        super(NbconvertApp, self).__init__(**kwargs)
        self.classes.insert(0, ConverterTemplate)
        # register class here to have help with help all
        self.classes.insert(0, ExtractFigureTransformer)
        self.classes.insert(0, GlobalConfigurable)

    def load_config_file(self, profile_name):
        """load a config file from the config file dir

        profile_name : {string} name of the profile file to load without file extension.
        """
        try:
            Application.load_config_file(
                self,
                profile_name+'.py',
                path=[os.path.join(NBCONVERT_DIR, 'profile')]
            )
            return True
        except ConfigFileNotFound:
            self.log.warn("Config file for profile '%s' not found, giving up ", profile_name)
            return False


    def initialize(self, argv=None):
        """parse command line and load config"""
        self.parse_command_line(argv)
        cl_config = self.config
        profile_file = argv[1]
        if not self.load_config_file(profile_file):
            exit(1)
        self.update_config(cl_config)



    def run(self):
        """Convert a notebook in one step"""
        ipynb_file = (self.extra_args or [None])[2]

        # If you are writting a custom transformer, append it to the dictionary
        # below.
        userpreprocessors = {}
        
        # Create the converter
        C = ConverterTemplate(config=self.config, preprocessors=userpreprocessors)

        output, resources = C.from_filename(ipynb_file)
        if self.stdout :
            print(output.encode('utf-8'))

        out_root = ipynb_file[:-6].replace('.', '_').replace(' ', '_')

        if self.write :
            with io.open(os.path.join(out_root+'.'+self.fileext), 'w') as f:
                f.write(output)

        binkeys = resources.get('figures', {}).get('binary',{}).keys()
        textkeys = resources.get('figures', {}).get('text',{}).keys()
        if binkeys or textkeys :
            if self.write:
                files_dir = out_root+'_files'
                if not os.path.exists(out_root+'_files'):
                    os.mkdir(files_dir)
                for key in binkeys:
                    with io.open(os.path.join(files_dir, key), 'wb') as f:
                        f.write(resources['figures']['binary'][key])
                for key in textkeys:
                    with io.open(os.path.join(files_dir, key), 'w') as f:
                        f.write(resources['figures']['text'][key])

            elif self.stdout:
                print('''====================== Keys in Resources ==================================''')
                print(resources['figures'].keys())
                print("""
===========================================================================
you are responsible from writing those data do a file in the right place if
they need to be.
===========================================================================
                  """)

def main():
    """Convert a notebook to html in one step"""
    app = NbconvertApp.instance()
    app.description = __doc__
    app.initialize(argv=sys.argv)
    app.start()
    app.run()
#-----------------------------------------------------------------------------
# Script main
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    main()

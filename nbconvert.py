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

#From IPython
#All the stuff needed for the configurable things
from IPython.config.application import Application
from IPython.config.loader import ConfigFileNotFound
from IPython.utils.traitlets import Unicode, Bool

#Local imports
from api.exporter import Exporter
from converters.config import GlobalConfigurable #TODO
from converters.transformers import (ExtractFigureTransformer) #TODO

#-----------------------------------------------------------------------------
#Globals and constants
#-----------------------------------------------------------------------------
NBCONVERT_DIR = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))

#'Keys in resources' user prompt.
KEYS_PROMPT_HEAD = "====================== Keys in Resources =================================="
KEYS_PROMPT_BODY = """
===========================================================================
You are responsible for writting these files into the appropriate 
directorie(s) if need be.  If you do not want to see this message, enable
the 'write' (boolean) flag of the converter.
===========================================================================
"""

#Error Messages
ERROR_CONFIG_NOT_FOUND = "Config file for profile '%s' not found, giving up."

#-----------------------------------------------------------------------------
#Classes and functions
#-----------------------------------------------------------------------------
class NbconvertApp(Application):
    """A basic application to convert ipynb files"""

    stdout = Bool(
        True, config=True,
        help="""Whether to print the converted ipynb file to stdout
        "use full do diff files without actually writing a new file"""
        )

    write = Bool(
        False, config=True,
        help="""Should the converted notebook file be written to disk
        along with potential extracted resources."""
        )

    fileext = Unicode(
        'txt', config=True, 
        help="Extension of the file that should be written to disk"
        )

    aliases = {
        'stdout':'NbconvertApp.stdout',
        'write':'NbconvertApp.write'
        }

    flags = {}
    flags['no-stdout'] = (
        {'NbconvertApp' : {'stdout' : False}}, 
        """Do not print converted file to stdout, equivalent to 
        --stdout=False"""
        )

    def __init__(self, **kwargs):
        """Public constructor"""

        #Call base class
        super(NbconvertApp, self).__init__(**kwargs)

        #Register class here to have help with help all
        self.classes.insert(0, ConverterTemplate)
        self.classes.insert(0, ExtractFigureTransformer)
        self.classes.insert(0, GlobalConfigurable)


    def load_config_file(self, profile_name):
        """Load a config file from the config file dir

        profile_name : {string} name of the profile file to load without file 
        extension.
        """

        #Try to load the config file.  If the file isn't found, catch the 
        #exception.
        try:
            Application.load_config_file(
                self,
                profile_name + '.py',
                path=[os.path.join(NBCONVERT_DIR, 'profile')]
                )
            return True

        except ConfigFileNotFound:
            self.log.warn(ERROR_CONFIG_NOT_FOUND, profile_name)
            return False


    def start(self, argv=None):
        """Convert a notebook in one step"""

        #Parse the commandline options.
        self.parse_command_line(argv)

        #Load an addition config file if specified by the user via the 
        #commandline.
        cl_config = self.config
        profile_file = argv[1]
        if not self.load_config_file(profile_file):
            exit(1)
        self.update_config(cl_config)

        #Call base
        super(NbconvertApp, self).start()

        #The last arguments in chain of arguments will be used as conversion
        ipynb_file = (self.extra_args or [None])[2]

        #If you are writting a custom transformer, append it to the dictionary
        #below.
        userpreprocessors = {}

        #Create the Jinja template exporter.  TODO: Add ability to 
        #import in IPYNB aswell
        exporter = Exporter(config=self.config, preprocessors=userpreprocessors)

        #Export
        output, resources = exporter.from_filename(ipynb_file)
        if self.stdout :
            print(output.encode('utf-8'))

        #Get the file name without the '.ipynb' (6 chars) extension and then
        #remove any addition periods and spaces. The resulting name will
        #be used to create the directory that the files will be exported
        #into.
        out_root = ipynb_file[:-6].replace('.', '_').replace(' ', '_')

        #Write file output from conversion.
        if self.write :
            with io.open(os.path.join(out_root+'.'+self.fileext), 'w') as f:
                f.write(output)

        #Output any associate figures into the same "root" directory.
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

            #Figures that weren't exported which will need to be created by the
            #user.  Tell the user what figures these are.
            elif self.stdout:
                print(KEYS_PROMPT_HEAD)
                print(resources['figures'].keys())
                print(KEYS_PROMPT_BODY)

#-----------------------------------------------------------------------------
#Script main
#-----------------------------------------------------------------------------
def main():
    """Convert a notebook in one step"""

    app = NbconvertApp.instance()
    app.description = __doc__
    app.run(argv=sys.argv)

if __name__ == '__main__':
    main()
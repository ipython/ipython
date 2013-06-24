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
from IPython.utils.traitlets import (Bool)

#Local imports
from nbconvert.exporters.export import export_by_name
from nbconvert.exporters.exporter import Exporter
from nbconvert.transformers import extractfigure
from nbconvert.utils.config import GlobalConfigurable

#-----------------------------------------------------------------------------
#Globals and constants
#-----------------------------------------------------------------------------

#'Keys in resources' user prompt.
KEYS_PROMPT_HEAD = "====================== Keys in Resources =================================="
KEYS_PROMPT_BODY = """
===========================================================================
You are responsible for writting these files into the appropriate 
directorie(s) if need be.  If you do not want to see this message, enable
the 'write' (boolean) flag of the converter.
===========================================================================
"""

#-----------------------------------------------------------------------------
#Classes and functions
#-----------------------------------------------------------------------------

class NbConvertApp(Application):
    """Application used to convert to and from notebook file type (*.ipynb)"""

    stdout = Bool(
        False, config=True,
        help="""Whether to print the converted IPYNB file to stdout
        use full do diff files without actually writing a new file"""
        )

    write = Bool(
        True, config=True,
        help="""Should the converted notebook file be written to disk
        along with potential extracted resources."""
        )

    aliases = {
             'stdout':'NbConvertApp.stdout',
             'write':'NbConvertApp.write',
             }

    flags = {}

    flags['stdout'] = (
        {'NbConvertApp' : {'stdout' : True}},
    """Print converted file to stdout, equivalent to --stdout=True
    """
    )

    flags['no-write'] = (
        {'NbConvertApp' : {'write' : True}},
    """Do not write to disk, equivalent to --write=False
    """
    )


    def __init__(self, **kwargs):
        """Public constructor"""

        #Call base class
        super(NbConvertApp, self).__init__(**kwargs)

        #Register class here to have help with help all
        self.classes.insert(0, Exporter)
        self.classes.insert(0, GlobalConfigurable)


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

        #The last arguments in list will be used by nbconvert
        if len(self.extra_args) is not 3:
            print( "Wrong number of arguments, use --help flag for usage", file=sys.stderr)
            sys.exit(-1)
        export_type = (self.extra_args)[1]
        ipynb_file = (self.extra_args)[2]
        
        #Export
        return_value = export_by_name(export_type, ipynb_file)
        if return_value is None:
            print("Error: '%s' template not found." % export_type)
            return
        else:
            (output, resources, exporter) = return_value 
        
        #TODO: Allow user to set output directory and file. 
        destination_filename = None
        destination_directory = None
        if self.write:
                
            #Get the file name without the '.ipynb' (6 chars) extension and then
            #remove any addition periods and spaces. The resulting name will
            #be used to create the directory that the files will be exported
            #into.
            out_root = ipynb_file[:-6].replace('.', '_').replace(' ', '_')
            destination_filename = os.path.join(out_root+'.'+exporter.file_extension)
            
            destination_directory = out_root+'_files'
            if not os.path.exists(destination_directory):
                os.mkdir(destination_directory)
                
        #Write the results
        if self.stdout or not (destination_filename is None and destination_directory is None):
            self._write_results(output, resources, destination_filename, destination_directory)


    def _write_results(self, output, resources, destination_filename=None, destination_directory=None):
        """Output the conversion results to the console and/or filesystem
        
        Parameters
        ----------
        output : str
            Output of conversion
        resources : dictionary
            Additional input/output used by the transformers.  For
            example, the ExtractFigure transformer outputs the
            figures it extracts into this dictionary.  This method
            relies on the figures being in this dictionary when
            attempting to write the figures to the file system.
        destination_filename : str, Optional
            Filename to write output into.  If None, output is not 
            written to a file.
        destination_directory : str, Optional 
            Directory to write notebook data (i.e. figures) to.  If
            None, figures are not written to the file system.
        """
        
        if self.stdout:
            print(output.encode('utf-8'))

        #Write file output from conversion.
        if not destination_filename is None:
            with io.open(destination_filename, 'w') as f:
                f.write(output)

        #Get the key names used by the extract figure transformer
        figures_key = extractfigure.FIGURES_KEY
        binary_key = extractfigure.BINARY_KEY
        text_key = extractfigure.TEXT_KEY
        
        #Output any associate figures into the same "root" directory.
        binkeys = resources.get(figures_key, {}).get(binary_key,{}).keys()
        textkeys = resources.get(figures_key, {}).get(text_key,{}).keys()
        if binkeys or textkeys :
            if not destination_directory is None:
                for key in binkeys:
                    with io.open(os.path.join(destination_directory, key), 'wb') as f:
                        f.write(resources[figures_key][binary_key][key])
                for key in textkeys:
                    with io.open(os.path.join(destination_directory, key), 'w') as f:
                        f.write(resources[figures_key][text_key][key])

            #Figures that weren't exported which will need to be created by the
            #user.  Tell the user what figures these are.
            if self.stdout:
                print(KEYS_PROMPT_HEAD, file=sys.stderr)
                print(resources[figures_key].keys(), file=sys.stderr)
                print(KEYS_PROMPT_BODY , file=sys.stderr)

#-----------------------------------------------------------------------------
#Script main
#-----------------------------------------------------------------------------

def main():
    """Application entry point"""

    app = NbConvertApp.instance()
    app.description = __doc__
    app.start(argv=sys.argv)

#Check to see if python is calling this file directly.
if __name__ == '__main__':
    main()

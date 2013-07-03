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
from IPython.config.application import Application
from IPython.utils.traitlets import Bool

from .exporters.export import export_by_name
from .exporters.exporter import Exporter
from .transformers import extractfigure
from .utils.config import GlobalConfigurable
from .writers.file import FileWriter
from .writers.stdout import StdoutWriter

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
        
        #Get the name of the notebook from the filename.  Remove fullpath and
        #file extension.
        basename = os.path.basename(ipynb_file)
        notebook_name = basename[:basename.rfind('.')]

        #Write the output using a notebook writer
        writer = FileWriter(config=self.config)
        #writer = StdoutWriter(config=self.config, debug=True)
        writer.write(notebook_name, exporter.file_extension, output, resources)


#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def launch_new_instance():
    """Application entry point"""

    app = NbConvertApp.instance()
    app.description = __doc__
    app.start(argv=sys.argv)


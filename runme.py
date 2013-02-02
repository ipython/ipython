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

from converters.template import *
from converters.template import ConverterTemplate
from converters.html import ConverterHTML
# From IPython

# All the stuff needed for the configurable things
from IPython.config.application import Application
from IPython.config.loader import ConfigFileNotFound
from IPython.utils.traitlets import List, Unicode, Type, Bool, Dict, CaselessStrEnum

from converters.transformers import (ConfigurableTransformers,ExtractFigureTransformer)


class NbconvertApp(Application):

    stdout = Bool(True, config=True)
    write = Bool(False, config=True)

    fileext = Unicode('txt', config=True)

    aliases = {
            'stdout':'NbconvertApp.stdout',
            'write':'NbconvertApp.write',
            }

    flags= {}
    flags['no-stdout'] = (
        {'NbconvertApp' : {'stdout' : False}},
    """the doc for this flag

    """
    )

    def __init__(self, **kwargs):
        super(NbconvertApp, self).__init__(**kwargs)
        self.classes.insert(0,ConverterTemplate)
        # register class here to have help with help all
        self.classes.insert(0,ExtractFigureTransformer)
        # ensure those are registerd

    def load_config_file(self, profile_name):
        try:
            Application.load_config_file(
                self,
                profile_name+'.nbcv',
                path=[os.path.join(os.getcwdu(),'profile')]
            )
        except ConfigFileNotFound:
            self.log.warn("Config file for profile '%s' not found, giving up ",profile_name)
            exit(1)


    def initialize(self, argv=None):
        self.parse_command_line(argv)
        cl_config = self.config
        profile_file = sys.argv[1]
        self.load_config_file(profile_file)
        self.update_config(cl_config)



    def run(self):
        """Convert a notebook to html in one step"""
        template_file = (self.extra_args or [None])[0]
        ipynb_file = (self.extra_args or [None])[1]

        template_file = sys.argv[1]

        C = ConverterTemplate(config=self.config)

        output,resources = C.from_filename(ipynb_file)
        if self.stdout :
            print(output.encode('utf-8'))

        out_root = ipynb_file[:-6].replace('.','_').replace(' ','_')

        keys = resources.get('figures',{}).keys()
        if self.write :
            with io.open(os.path.join(out_root+'.'+self.fileext),'w') as f:
                        f.write(output)
        if keys :
            if self.write and not os.path.exists(out_root+'_files'):
                os.mkdir(out_root+'_files')
            for key in keys:
                if self.write:
                    with io.open(os.path.join(out_root+'_files',key),'wb') as f:
                        print(' writing to ',os.path.join(out_root,key))
                        f.write(resources['figures'][key])
            if self.stdout:
                print('''
====================== Keys in Resources ==================================
''')
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
    app.initialize()
    app.start()
    app.run()
#-----------------------------------------------------------------------------
# Script main
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    main()

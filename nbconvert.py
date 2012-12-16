#!/usr/bin/env python
"""Convert IPython notebooks to other formats, such as ReST, and HTML.

Example:
  ./nbconvert.py --format rst file.ipynb

Produces 'file.rst', along with auto-generated figure files
called nb_figure_NN.png.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# From IPython
from IPython.external import argparse

# All the stuff needed for the configurable things
from IPython.config.application import Application, catch_config_error
from IPython.config.configurable import Configurable
from IPython.config.loader import Config, ConfigFileNotFound
from IPython.utils.traitlets import List, Unicode, Type, Bool, Dict, CaselessStrEnum


# local
from converters.html import ConverterHTML
from converters.markdown import ConverterMarkdown
from converters.bloggerhtml import ConverterBloggerHTML
from converters.rst import ConverterRST
from converters.latex import ConverterLaTeX
from converters.python import ConverterPy
from converters.reveal import ConverterReveal


# When adding a new format, make sure to add it to the `converters`
# dictionary below. This is used to create the list of known formats,
# which gets printed in case an unknown format is encounteres, as well
# as in the help

converters = {
    'rst': ConverterRST,
    'markdown': ConverterMarkdown,
    'html': ConverterHTML,
    'blogger-html': ConverterBloggerHTML,
    'latex': ConverterLaTeX,
    'py': ConverterPy,
    'reveal': ConverterReveal,
    }

default_format = 'rst'

# Extract the list of known formats and mark the first format as the default.
known_formats = ', '.join([key + " (default)" if key == default_format else key
                           for key in converters])

class NbconvertApp(Application):

    name = Unicode('thisIsNbconvertApp',config=True)

    fmt = CaselessStrEnum(converters.keys(),
                          default_value='rst', 
                          config=True,
                          help="Supported conversion format")

    preamble = Unicode("" ,
                        config=True,
                        help="Path to a user-specified preamble file")

    highlight = Bool(True, 
                     config=True,
                     help="Enable syntax highlighting for code blocks.")

    exclude = List( [],
                    config=True,
                    help = 'list of cells to exclude while converting')

    infile = Unicode("", config=True)

    converter = ConverterClass(infile, highlight_source=highlight_source, exclude=exclude)
    converter.render()


    aliases = {
            'format':'NbconvertApp.fmt',
            'highlight':'NbconvertApp.highlight',
            'preamble':'NbconvertApp.preamble',
            'infile' : 'NbconvertApp.infile'
            }

    def __init__(self, **kwargs):
        super(NbconvertApp, self).__init__(**kwargs)

    def initialize(self, argv=None):
        # don't hook up crash handler before parsing command-line
        self.parse_command_line(argv)
        cl_config = self.config
        print(self.config)
        self.update_config(cl_config)
        #self.init_crash_handler()
        #self.foo = Cnf(config=self.config)
        #if self.subapp is not None:
            # stop here if subapp is taking over
            #return
        #cl_config = self.config
        #self.init_profile_dir()
        #self.init_config_files()
        #self.load_config_file()
        # enforce cl-opts override configfile opts:
        #self.update_config(cl_config)


    def run(self):
        """Convert a notebook to html in one step"""
        ConverterClass = converters[self.fmt]

        converter = ConverterClass(self.infile, highlight_source=self.highlight, preamble=self.preamble, exclude=self.exclude)
        converter.render()

def main():
    """Convert a notebook to html in one step"""
    app = NbconvertApp.instance()
    print(app.classes)
    app.initialize()
    app.start()
    app.run()
#-----------------------------------------------------------------------------
# Script main
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    #parser = argparse.ArgumentParser(description=__doc__,
    #        formatter_class=argparse.RawTextHelpFormatter)
    # TODO: consider passing file like object around, rather than filenames
    # would allow us to process stdin, or even http streams
    #parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
    #                    default=sys.stdin)

    #Require a filename as a positional argument
    #parser.add_argument('infile', nargs=1)
    #parser.add_argument('-e', '--exclude', default='',
    #                    help='Comma-separated list of cells to exclude')
    #parser.add_argument('-H', '--no-highlighting', action='store_false',
    #                    help='Disable syntax highlighting for code blocks.')
    #args = parser.parse_args()
    #exclude_cells = [s.strip() for s in args.exclude.split(',')]

    main()

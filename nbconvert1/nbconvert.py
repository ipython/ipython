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
from IPython.config.configurable import Configurable, SingletonConfigurable
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
from converters.base import Converter
from converters.pdf import ConverterLaTeXToPDF


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
    'pdf' : ConverterLaTeXToPDF,
    'py': ConverterPy,
    'reveal': ConverterReveal,
    }

default_format = 'rst'

# Extract the list of known formats and mark the first format as the default.
known_formats = ', '.join([key + " (default)" if key == default_format else key
                           for key in converters])

class NbconvertApp(Application):


    fmt = CaselessStrEnum(converters.keys(),
                          default_value='rst',
                          config=True,
                          help="Supported conversion format")

    exclude = List( [],
                    config=True,
                    help = 'list of cells to exclude while converting')

    aliases = {
            'format':'NbconvertApp.fmt',
            'exclude':'NbconvertApp.exclude',
            'highlight':'Converter.highlight_source',
            'preamble':'Converter.preamble',
            }

    def __init__(self, **kwargs):
        super(NbconvertApp, self).__init__(**kwargs)
        # ensure those are registerd
        self.classes.insert(0,Converter)
        self.classes.insert(0,ConverterRST)
        self.classes.insert(0,ConverterMarkdown)
        self.classes.insert(0,ConverterBloggerHTML)
        self.classes.insert(0,ConverterLaTeX)
        self.classes.insert(0,ConverterPy)

    def initialize(self, argv=None):
        self.parse_command_line(argv)
        cl_config = self.config
        self.update_config(cl_config)

    def run(self):
        """Convert a notebook in one step"""
        ConverterClass = converters[self.fmt]
        infile = (self.extra_args or [None])[0]
        converter = ConverterClass(infile=infile,  config=self.config)
        converter.render()

def main():
    """Convert a notebook to html in one step"""
    app = NbconvertApp.instance()
    app.description = __doc__
    print("""
======================================================
Warning, we are deprecating this version of nbconvert,
please consider using the new version.
======================================================
    """)
    app.initialize()
    app.start()
    app.run()
#-----------------------------------------------------------------------------
# Script main
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    # TODO: consider passing file like object around, rather than filenames
    # would allow us to process stdin, or even http streams
    #parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
    #                    default=sys.stdin)

    #parser.add_argument('-e', '--exclude', default='',
    #                    help='Comma-separated list of cells to exclude')
    #exclude_cells = [s.strip() for s in args.exclude.split(',')]

    main()

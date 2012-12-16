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



def main(infile, format='rst', preamble=None, exclude=None):
    """Convert a notebook to html in one step"""
    try:
        ConverterClass = converters[format]
    except KeyError:
        raise SystemExit("Unknown format '%s', " % format +
                         "known formats are: " + known_formats)

    converter = ConverterClass(infile)
    converter.render()

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

    converter = ConverterClass(infile, highlight_source=highlight_source, exclude=exclude)
    converter.render()


    aliases = {
            'format':'NbconvertApp.fmt',
            'highlight':'Converter.highlight_source',
            'preamble':'Converter.preamble',
            'infile' : 'NbconvertApp.infile'
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
        # don't hook up crash handler before parsing command-line
        self.parse_command_line(argv)
        cl_config = self.config
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
        """Convert a notebook in one step"""
        ConverterClass = converters[self.fmt]
        converter = ConverterClass(infile=self.extra_args[0],  config=self.config)
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
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    # TODO: consider passing file like object around, rather than filenames
    # would allow us to process stdin, or even http streams
    #parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
    #                    default=sys.stdin)

    #Require a filename as a positional argument
    parser.add_argument('infile', nargs=1)
    parser.add_argument('-f', '--format', default='rst',
                        help='Output format. Supported formats: \n' +
                        known_formats)
    parser.add_argument('-p', '--preamble',
                        help='Path to a user-specified preamble file')
    parser.add_argument('-e', '--exclude', default='',
                        help='Comma-separated list of cells to exclude')

    main()

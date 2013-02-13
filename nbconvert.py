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


def main(infile, format='rst', preamble=None, exclude=[],
         highlight_source=True):
    """Convert a notebook to html in one step"""
    try:
        ConverterClass = converters[format]
    except KeyError:
        raise SystemExit("Unknown format '%s', " % format +
                         "known formats are: " + known_formats)

    converter = ConverterClass(infile, highlight_source=highlight_source, exclude=exclude)
    converter.render()

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
    parser.add_argument('-H', '--no-highlighting', action='store_false',
                        help='Disable syntax highlighting for code blocks.')
    args = parser.parse_args()
    exclude_cells = [s.strip() for s in args.exclude.split(',')]

    main(infile=args.infile[0], format=args.format, preamble=args.preamble,
         exclude=exclude_cells, highlight_source=args.no_highlighting)

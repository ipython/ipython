"""Base classes for the notebook conversion pipeline.

This module defines Converter, from which all objects designed to implement
a conversion of IPython notebooks to some other format should inherit.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function, absolute_import

# Stdlib imports
import codecs
import io
import logging
import os
import pprint
import re
from types import FunctionType

# IPython imports
from IPython.nbformat import current as nbformat
from IPython.config.configurable import Configurable, SingletonConfigurable
from IPython.utils.traitlets import List, Unicode, Type, Bool, Dict, CaselessStrEnum

# Our own imports
from .utils import remove_fake_files_url


#-----------------------------------------------------------------------------
# Local utilities
#-----------------------------------------------------------------------------

def clean_filename(filename):
    """
    Remove non-alphanumeric characters from filenames.

    Parameters
    ----------
    filename : str
        The filename to be sanitized.

    Returns
    -------
    clean : str
        A sanitized filename that contains only alphanumeric
        characters and underscores.
    """
    filename = re.sub(r'[^a-zA-Z0-9_]', '_', filename)
    return filename


#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------

class ConversionException(Exception):
    pass


class DocStringInheritor(type):
    """
    This metaclass will walk the list of bases until the desired
    superclass method is found AND if that method has a docstring and only
    THEN does it attach the superdocstring to the derived class method.

    Please use carefully, I just did the metaclass thing by following
    Michael Foord's Metaclass tutorial
    (http://www.voidspace.org.uk/python/articles/metaclasses.shtml), I may
    have missed a step or two.

    source:
    http://groups.google.com/group/comp.lang.python/msg/26f7b4fcb4d66c95
    by Paul McGuire
    """
    def __new__(meta, classname, bases, classDict):
        newClassDict = {}
        for attributeName, attribute in classDict.items():
            if type(attribute) == FunctionType:
                # look through bases for matching function by name
                for baseclass in bases:
                    if hasattr(baseclass, attributeName):
                        basefn = getattr(baseclass, attributeName)
                        if basefn.__doc__:
                            attribute.__doc__ = basefn.__doc__
                            break
            newClassDict[attributeName] = attribute
        return type.__new__(meta, classname, bases, newClassDict)



class Converter(Configurable):
    #__metaclass__ = DocStringInheritor
    #-------------------------------------------------------------------------
    # Class-level attributes determining the behaviour of the class but
    # probably not varying from instance to instance.
    #-------------------------------------------------------------------------
    default_encoding = 'utf-8'
    extension = str()
    blank_symbol = " "
    # Which display data format is best? Subclasses can override if
    # they have specific requirements.
    display_data_priority = ['pdf', 'svg', 'png', 'jpg', 'text']
    #-------------------------------------------------------------------------
    # Instance-level attributes that are set in the constructor for this
    # class.
    #-------------------------------------------------------------------------
    infile = Unicode()

    highlight_source = Bool(True,
                     config=True,
                     help="Enable syntax highlighting for code blocks.")

    preamble = Unicode("" ,
                        config=True,
                        help="Path to a user-specified preamble file")

    infile_dir = Unicode()
    infile_root = Unicode()
    clean_name = Unicode()
    files_dir = Unicode()
    outbase = Unicode()
    #-------------------------------------------------------------------------
    # Instance-level attributes that are set by other methods in the base
    # class.
    #-------------------------------------------------------------------------
    figures_counter = 0
    output = Unicode()
    #-------------------------------------------------------------------------
    # Instance-level attributes that are not actually mentioned further
    # in this class. TODO: Could they be usefully moved to a subclass?
    #-------------------------------------------------------------------------
    with_preamble = Bool(True,config=True)
    user_preamble = None
    raw_as_verbatim = False


    def __init__(self, infile='', config=None, exclude=[], **kw):
        super(Converter,self).__init__(config=config)

        #DocStringInheritor.__init__(self=config)
        # N.B. Initialized in the same order as defined above. Please try to
        # keep in this way for readability's sake.
        self.exclude_cells = exclude
        self.infile = infile
        self.infile_dir, infile_root = os.path.split(infile)
        self.infile_root = os.path.splitext(infile_root)[0]
        self.clean_name = clean_filename(self.infile_root)
        # Handle the creation of a directory for ancillary files, for
        # formats that need one.
        files_dir = os.path.join(self.infile_dir, self.clean_name + '_files')
        if not os.path.isdir(files_dir):
            os.mkdir(files_dir)
        self.files_dir = files_dir
        self.outbase = os.path.join(self.infile_dir, self.infile_root)

    def __del__(self):
        if os.path.isdir(self.files_dir) and not os.listdir(self.files_dir):
            os.rmdir(self.files_dir)

    def _get_prompt_number(self, cell):
        return cell.prompt_number if hasattr(cell, 'prompt_number') \
            else self.blank_symbol

    def dispatch(self, cell_type):
        """return cell_type dependent render method,  for example render_code
        """
        return getattr(self, 'render_' + cell_type, self.render_unknown)

    def dispatch_display_format(self, format):
        """
        return output_type dependent render method,  for example
        render_output_text
        """
        return getattr(self, 'render_display_format_' + format,
                       self.render_unknown_display)

    def convert(self, cell_separator='\n'):
        """
        Generic method to converts notebook to a string representation.

        This is accomplished by dispatching on the cell_type, so subclasses of
        Convereter class do not need to re-implement this method, but just
        need implementation for the methods that will be dispatched.

        Parameters
        ----------
        cell_separator : string
          Character or string to join cells with. Default is "\n"

        Returns
        -------
        out : string
        """
        lines = []
        lines.extend(self.optional_header())
        lines.extend(self.main_body(cell_separator))
        lines.extend(self.optional_footer())
        return u'\n'.join(lines)

    def main_body(self, cell_separator='\n'):
        converted_cells = []
        for worksheet in self.nb.worksheets:
            for cell in worksheet.cells:
                #print(cell.cell_type)  # dbg
                conv_fn = self.dispatch(cell.cell_type)
                if cell.cell_type in ('markdown', 'raw'):
                    remove_fake_files_url(cell)
                converted_cells.append('\n'.join(conv_fn(cell)))
        cell_lines = cell_separator.join(converted_cells).split('\n')
        return cell_lines

    def render(self):
        "read, convert, and save self.infile"
        if not hasattr(self, 'nb'):
            self.read()
        self.output = self.convert()
        assert(type(self.output) == unicode)
        return self.save()

    def read(self):
        "read and parse notebook into NotebookNode called self.nb"
        with open(self.infile) as f:
            self.nb = nbformat.read(f, 'json')

    def save(self, outfile=None, encoding=None):
        "read and parse notebook into self.nb"
        if outfile is None:
            outfile = self.outbase + '.' + self.extension
        if encoding is None:
            encoding = self.default_encoding
        with io.open(outfile, 'w', encoding=encoding) as f:
            f.write(self.output)
        return os.path.abspath(outfile)

    def optional_header(self):
        """
        Optional header to insert at the top of the converted notebook

        Returns a list
        """
        return []

    def optional_footer(self):
        """
        Optional footer to insert at the end of the converted notebook

        Returns a list
        """
        return []

    def _new_figure(self, data, fmt):
        """Create a new figure file in the given format.

        Returns a path relative to the input file.
        """
        figname = '%s_fig_%02i.%s' % (self.clean_name,
                                      self.figures_counter, fmt)
        self.figures_counter += 1
        fullname = os.path.join(self.files_dir, figname)

        # Binary files are base64-encoded, SVG is already XML
        if fmt in ('png', 'jpg', 'pdf'):
            data = data.decode('base64')
            fopen = lambda fname: open(fname, 'wb')
        else:
            fopen = lambda fname: codecs.open(fname, 'wb',
                                              self.default_encoding)

        with fopen(fullname) as f:
            f.write(data)

        return fullname

    def render_heading(self, cell):
        """convert a heading cell

        Returns list."""
        raise NotImplementedError

    def render_code(self, cell):
        """Convert a code cell

        Returns list."""
        raise NotImplementedError

    def render_markdown(self, cell):
        """convert a markdown cell

        Returns list."""
        raise NotImplementedError

    def _img_lines(self, img_file):
        """Return list of lines to include an image file."""
        # Note: subclasses may choose to implement format-specific _FMT_lines
        # methods if they so choose (FMT in {png, svg, jpg, pdf}).
        raise NotImplementedError

    def render_display_data(self, output):
        """convert display data from the output of a code cell

        Returns list.
        """
        for fmt in self.display_data_priority:
            if fmt in output:
                break
        else:
            for fmt in output:
                if fmt != 'output_type':
                    break
            else:
                raise RuntimeError('no display data')

        # Is it an image?
        if fmt in ['png', 'svg', 'jpg', 'pdf']:
            img_file = self._new_figure(output[fmt], fmt)
            # Subclasses can have format-specific render functions (e.g.,
            # latex has to auto-convert all SVG to PDF first).
            lines_fun = getattr(self, '_%s_lines' % fmt, None)
            if not lines_fun:
                lines_fun = self._img_lines
            lines = lines_fun(img_file)
        else:
            lines_fun = self.dispatch_display_format(fmt)
            lines = lines_fun(output)

        return lines

    def render_raw(self, cell):
        """convert a cell with raw text

        Returns list."""
        raise NotImplementedError

    def render_unknown(self, cell):
        """Render cells of unkown type

        Returns list."""
        data = pprint.pformat(cell)
        logging.warning('Unknown cell: %s' % cell.cell_type)
        return self._unknown_lines(data)

    def render_unknown_display(self, output, type):
        """Render cells of unkown type

        Returns list."""
        data = pprint.pformat(output)
        logging.warning('Unknown output: %s' % output.output_type)
        return self._unknown_lines(data)

    def render_stream(self, output):
        """render the stream part of an output

        Returns list.

        Identical to render_display_format_text
        """
        return self.render_display_format_text(output)

    def render_pyout(self, output):
        """convert pyout part of a code cell

        Returns list."""
        raise NotImplementedError

    def render_pyerr(self, output):
        """convert pyerr part of a code cell

        Returns list."""
        raise NotImplementedError

    def _unknown_lines(self, data):
        """Return list of lines for an unknown cell.

        Parameters
        ----------
        data : str
          The content of the unknown data as a single string.
        """
        raise NotImplementedError

    # These are the possible format types in an output node

    def render_display_format_text(self, output):
        """render the text part of an output

        Returns list.
        """
        raise NotImplementedError

    def render_display_format_html(self, output):
        """render the html part of an output

        Returns list.
        """
        raise NotImplementedError

    def render_display_format_latex(self, output):
        """render the latex part of an output

        Returns list.
        """
        raise NotImplementedError

    def render_display_format_json(self, output):
        """render the json part of an output

        Returns list.
        """
        raise NotImplementedError

    def render_display_format_javascript(self, output):
        """render the javascript part of an output

        Returns list.
        """
        raise NotImplementedError

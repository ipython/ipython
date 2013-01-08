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
import jinja2
import codecs
import io
import logging
import os
import pprint
import re
from types import FunctionType

from jinja2 import Environment, PackageLoader, FileSystemLoader
env = Environment(loader=FileSystemLoader('./templates/'))

# IPython imports
from IPython.nbformat import current as nbformat
from IPython.config.configurable import Configurable, SingletonConfigurable
from IPython.utils.traitlets import (List, Unicode, Type, Bool, Dict, CaselessStrEnum,
                                    Any)

# Our own imports
from IPython.utils.text import indent
from .utils import remove_ansi
from markdown import markdown
from .utils import highlight
#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------
def rm_fake(strng):
    return strng.replace('/files/', '')

class ConversionException(Exception):
    pass


def python_comment(string):
    return '# '+'\n# '.join(string.split('\n'))

env.filters['pycomment'] = python_comment
env.filters['indent'] = indent
env.filters['rm_fake'] = rm_fake
env.filters['rm_ansi'] = remove_ansi
env.filters['markdown'] = markdown
env.filters['highlight'] = highlight

class ConverterTemplate(Configurable):

    display_data_priority = ['pdf', 'svg', 'png', 'jpg', 'text']
    #-------------------------------------------------------------------------
    # Instance-level attributes that are set in the constructor for this
    # class.
    #-------------------------------------------------------------------------
    infile = Any()


    infile_dir = Unicode()

    def __init__(self, tplfile='fullhtml', config=None, **kw):
        self.template = env.get_template(tplfile+'.tpl')
        super(ConverterTemplate,self).__init__(config=config)

    def _get_prompt_number(self, cell):
        return cell.prompt_number if hasattr(cell, 'prompt_number') \
            else self.blank_symbol


    def process(self):
        converted_cells = []
        for worksheet in self.nb.worksheets:
            for cell in worksheet.cells:
                cell.type = cell.cell_type
            converted_cells.append(worksheet)

        return converted_cells

    def convert(self, cell_separator='\n'):
        return self.template.render(worksheets=self.process())


    def read(self, filename):
        "read and parse notebook into NotebookNode called self.nb"
        with io.open(filename) as f:
            self.nb = nbformat.read(f, 'json')


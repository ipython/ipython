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
import io
import os
from IPython.utils import path

from jinja2 import Environment, FileSystemLoader
env = Environment(
        loader=FileSystemLoader('./templates/'), 
        extensions=['jinja2.ext.loopcontrols']
        )

# IPython imports
from IPython.nbformat import current as nbformat
from IPython.config.configurable import Configurable
from IPython.utils.traitlets import ( Unicode, Any)

# Our own imports
from IPython.utils.text import indent
from .utils import remove_ansi
from markdown import markdown
from .utils import highlight, ansi2html
#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------
def rm_fake(strng):
    return strng.replace('/files/', '')

class ConversionException(Exception):
    pass


def python_comment(string):
    return '# '+'\n# '.join(string.split('\n'))



def header_body():
    """Return the body of the header as a list of strings."""

    from pygments.formatters import HtmlFormatter

    header = []
    static = os.path.join(path.get_ipython_package_dir(),
    'frontend', 'html', 'notebook', 'static',
    )
    here = os.path.split(os.path.realpath(__file__))[0]
    css = os.path.join(static, 'css')
    for sheet in [
        # do we need jquery and prettify?
        # os.path.join(static, 'jquery', 'css', 'themes', 'base',
        # 'jquery-ui.min.css'),
        # os.path.join(static, 'prettify', 'prettify.css'),
        os.path.join(css, 'boilerplate.css'),
        os.path.join(css, 'fbm.css'),
        os.path.join(css, 'notebook.css'),
        os.path.join(css, 'renderedhtml.css'),
        # our overrides:
        os.path.join(here, '..', 'css', 'static_html.css'),
    ]:

        with io.open(sheet, encoding='utf-8') as f:
            s = f.read()
            header.append(s)

    pygments_css = HtmlFormatter().get_style_defs('.highlight')
    header.append(pygments_css)
    return header

inlining = {}
inlining['css'] = header_body()


def filter_data_type(output):
    for fmt in ['html', 'pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg' , 'text']:
        if fmt in output:
            return [fmt]


env.filters['filter_data_type'] = filter_data_type
env.filters['pycomment'] = python_comment
env.filters['indent'] = indent
env.filters['rm_fake'] = rm_fake
env.filters['rm_ansi'] = remove_ansi
env.filters['markdown'] = markdown
env.filters['highlight'] = highlight
env.filters['ansi2html'] = ansi2html

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
        self.nb = None
        super(ConverterTemplate, self).__init__(config=config, **kw)

    def process(self):
        converted_cells = []
        for worksheet in self.nb.worksheets:
            for cell in worksheet.cells:
                cell.type = cell.cell_type
                cell.haspyout = False
                for out in cell.get('outputs', []):
                    if out.output_type == 'pyout':
                        cell.haspyout = True
                        break
            converted_cells.append(worksheet)

        return converted_cells

    def convert(self):
        """ convert the ipynb file

        return both the converted ipynb file and a dict containing potential
        other resources
        """
        return self.template.render(worksheets=self.process(), inlining=inlining), {}


    def read(self, filename):
        "read and parse notebook into NotebookNode called self.nb"
        with io.open(filename) as f:
            self.nb = nbformat.read(f, 'json')


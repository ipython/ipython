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
import re
from IPython.utils import path

from jinja2 import Environment, FileSystemLoader
env = Environment(
        loader=FileSystemLoader('./templates/'),
        extensions=['jinja2.ext.loopcontrols']
        )

texenv = Environment(
        loader=FileSystemLoader('./templates/tex/'),
        extensions=['jinja2.ext.loopcontrols']
        )

# IPython imports
from IPython.nbformat import current as nbformat
from IPython.config.configurable import Configurable
from IPython.utils.traitlets import ( Unicode, Any, List)

# Our own imports
from IPython.utils.text import indent
from .utils import remove_ansi
from markdown import markdown
from .utils import highlight, ansi2html
from .utils import markdown2latex
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


def _new_figure(data, fmt, count):
    """Create a new figure file in the given format.

    Returns a path relative to the input file.
    """
    figname = '_fig_%02i.%s' % (count, fmt)

    # Binary files are base64-encoded, SVG is already XML
    if fmt in ('png', 'jpg', 'pdf'):
        data = data.decode('base64')

    return figname,data




inlining = {}
inlining['css'] = header_body()






env.filters['pycomment'] = python_comment
env.filters['indent'] = indent
env.filters['rm_fake'] = rm_fake
env.filters['rm_ansi'] = remove_ansi
env.filters['markdown'] = markdown
env.filters['highlight'] = highlight
env.filters['ansi2html'] = ansi2html



LATEX_SUBS = (
    (re.compile(r'\\'), r'\\textbackslash'),
    (re.compile(r'([{}_#%&$])'), r'\\\1'),
    (re.compile(r'~'), r'\~{}'),
    (re.compile(r'\^'), r'\^{}'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\.\.\.+'), r'\\ldots'),
)

def escape_tex(value):
    newval = value
    for pattern, replacement in LATEX_SUBS:
        newval = pattern.sub(replacement, newval)
    return newval

texenv.block_start_string = '((*'
texenv.block_end_string = '*))'
texenv.variable_start_string = '((('
texenv.variable_end_string = ')))'
texenv.comment_start_string = '((='
texenv.comment_end_string = '=))'
texenv.filters['escape_tex'] = escape_tex

texenv.filters['pycomment'] = python_comment
texenv.filters['indent'] = indent
texenv.filters['rm_fake'] = rm_fake
texenv.filters['rm_ansi'] = remove_ansi
texenv.filters['markdown'] = markdown
texenv.filters['highlight'] = highlight
texenv.filters['ansi2html'] = ansi2html
texenv.filters['markdown2latex'] = markdown2latex
markdown2latex


def haspyout_transformer(nb,_):
    for worksheet in nb.worksheets:
        for cell in worksheet.cells:
            cell.type = cell.cell_type
            cell.haspyout = False
            for out in cell.get('outputs', []):
                if out.output_type == 'pyout':
                    cell.haspyout = True
                    break
    return nb,_


def outline_figure_transformer(nb,other):
    count=0
    for worksheet in nb.worksheets:
        for cell in worksheet.cells:
            cell.type = cell.cell_type
            for i,out in enumerate(cell.get('outputs', [])):
                print('loop outputs',out.output_type) 
                for type in ['html', 'pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg']:
                    if out.hasattr(type):
                        figname,data = _new_figure(out[type], type,count)
                        cell.outputs[i][type] = figname
                        out[type] = figname
                        print('set',type, 'to' ,figname)
                        other[figname] = data
                        count = count+1
    return nb,other


def print_transformer(nb,other):
    count=0
    for worksheet in nb.worksheets:
        for cell in worksheet.cells:
            cell.type = cell.cell_type
            for i,out in enumerate(cell.get('outputs', [])):
                print(cell.outputs) 
    return nb,other

class ConverterTemplate(Configurable):
    """ A Jinja2 base converter templates"""

    display_data_priority = List(['html', 'pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg' , 'text'],
            config=True,
              help= """
                    A list of ast.NodeTransformer subclass instances, which will be applied
                    to user input before code is run.
                    """
            )
    #-------------------------------------------------------------------------
    # Instance-level attributes that are set in the constructor for this
    # class.
    #-------------------------------------------------------------------------
    infile = Any()


    infile_dir = Unicode()
    def display_data_priority_changed(self, name, old, new):
        print('== changed', name,old,new)

    def filter_data_type(self,output):
        for fmt in self.display_data_priority:
            if fmt in output:
                return [fmt]

    def __init__(self, tplfile='fullhtml', preprocessors=[], config=None,tex_environement=False, **kw):
        """
        tplfile : jinja template file to process.

        config: the Configurable confg object to pass around

        preprocessors: list of function to run on ipynb json data before conversion
        to extract/inline file,

        """
        self.env = texenv if tex_environement else env
        self.ext = '.tplx' if tex_environement else '.tpl' 
        self.nb = None
        self.preprocessors = preprocessors
        self.preprocessors.append(haspyout_transformer)
        self.preprocessors.append(outline_figure_transformer)
        self.preprocessors.append(print_transformer)
        super(ConverterTemplate, self).__init__(config=config, **kw)
        self.env.filters['filter_data_type'] = self.filter_data_type
        self.template = self.env.get_template(tplfile+self.ext)



    def process(self):
        """
        preprocess the notebook json for easier use with the templates. 
        will call all the `preprocessor`s in order before returning it. 
        """
        nb = self.nb

        for preprocessor in self.preprocessors:
            nb,others = preprocessor(nb,{})

        return nb

    def convert(self):
        """ convert the ipynb file

        return both the converted ipynb file and a dict containing potential
        other resources
        """
        return self.template.render(nb=self.process(), inlining=inlining), {}


    def read(self, filename):
        "read and parse notebook into NotebookNode called self.nb"
        with io.open(filename) as f:
            self.nb = nbformat.read(f, 'json')


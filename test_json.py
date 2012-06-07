import nbconvert as nb
import json
from decorators import DocInherit

from IPython.external import argparse
from IPython.nbformat import current as nbformat
from IPython.utils.text import indent


_multiline_outputs = ['text', 'html', 'svg', 'latex', 'javascript', 'json']
def split_lines_cell(cell):
    """
    Split lines within a cell as in 
    IPython.nbformat.v3.rwbase.split_lines

    """
    if cell.cell_type == 'code':
        if 'input' in cell and isinstance(cell.input, basestring):
            cell.input = (cell.input + '\n').splitlines()
        for output in cell.outputs:
            for key in _multiline_outputs:
                item = output.get(key, None)
                if isinstance(item, basestring):
                    output[key] = (item + '\n').splitlines()
    else: # text, heading cell
        for key in ['source', 'rendered']:
            item = cell.get(key, None)
            if isinstance(item, basestring):
                cell[key] = (item + '\n').splitlines()



class ConverterJSON(nb.Converter):
    """
    A null-op converter that can be subclassed
    for custom handling of .ipynb files.
    Writes out a JSON file.

    """
    extension = 'json'
    name = 'new_notebook'
    indent_level = 4

    def optional_header(self):
        s = \
"""{
 "metadata": {
 "name": "%(name)s"
 },
 "nbformat": 3,
 "worksheets": [
 {
 "cells": [""" % {'name':self.name}

        return s.split('\n')

    def optional_footer(self):
        s = \
"""
   ]
  }
 ]
}"""
        return s.split('\n')

    def render(self, outfile):
        "read, convert, and save self.infile"
        self.read()
        self.output = self.convert()
        return self.save(outfile)

    def save(self, outfile, encoding=None):
        "read and parse notebook into self.nb"
        if encoding is None:
            encoding = self.default_encoding
        with open(outfile, 'w') as f:
            f.write(self.output.encode(encoding))
        return os.path.abspath(outfile)

    def tolines(self, cell):
        '''
        Write a cell to json.
        '''
        split_lines_cell(cell)
        return [json.dumps(cell)]

    @DocInherit
    def render_heading(self, cell):
        return self.tolines(cell)

    @DocInherit
    def render_code(self, cell):
        return self.tolines(cell)

    @DocInherit
    def render_markdown(self, cell):
        return self.tolines(cell)

    @DocInherit
    def render_raw(self, cell):
        return self.tolines(cell)

    @DocInherit
    def render_pyout(self, output):
        return self.tolines(cell)

    @DocInherit
    def render_pyerr(self, output):
        return self.tolines(cell)

class ConverterNoCodeInput(nb.Converter):
    extension = 'rst'
    heading_level = {1: '=', 2: '-', 3: '`', 4: '\'', 5: '.', 6: '~'}

    @DocInherit
    def render_heading(self, cell):
        marker = self.heading_level[cell.level]
        return ['{0}\n{1}\n'.format(cell.source, marker * len(cell.source))]

    @DocInherit
    def render_markdown(self, cell):
        return [cell.source]

    @DocInherit
    def render_raw(self, cell):
        if self.raw_as_verbatim:
            return ['::', '', indent(cell.source), '']
        else:
            return [cell.source]

    @DocInherit
    def render_pyout(self, output):
        lines = ['Out[%s]:' % output.prompt_number, '']

        # output is a dictionary like object with type as a key
        if 'latex' in output:
            lines.extend(rst_directive('.. math::', output.latex))

        if 'text' in output:
            lines.extend(rst_directive('.. parsed-literal::', output.text))

        return lines

    @DocInherit
    def render_pyerr(self, output):
        # Note: a traceback is a *list* of frames.
        return ['::', '', indent(remove_ansi('\n'.join(output.traceback))), '']

    @DocInherit
    def _img_lines(self, img_file):
        return ['.. image:: %s' % img_file, '']
    
    @DocInherit
    def render_stream(self, output):
        lines = []

        if 'text' in output:
            lines.extend(rst_directive('.. parsed-literal::', output.text))

        return lines

    @DocInherit
    def _unknown_lines(self, data):
        return rst_directive('.. warning:: Unknown cell') + [data]

    @DocInherit
    def render_code(self, cell):

        lines = []

        for output in cell.outputs:
            conv_fn = self.dispatch(output.output_type)
            lines.extend(conv_fn(output))

        return lines


def mytest():
    converter = nb.ConverterJSON('Test_notebook.ipynb')
    converter.render('new_notebook.ipynb')
    1/0


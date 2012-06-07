import os, copy

import nbconvert as nb
import json
from decorators import DocInherit

from IPython.external import argparse
from IPython.nbformat import current as nbformat
from IPython.nbformat.v3.nbjson import from_dict, rejoin_lines, BytesEncoder
from IPython.utils.text import indent
from IPython.utils import py3compat


class CustomNotebookConverter(nb.ConverterNotebook):

    def render_code(self, cell):

        captured_outputs = ['text', 'html', 'svg', 'latex', 'javascript']

        cell = copy.deepcopy(cell)
        cell['input'] = ''

        for output in cell.outputs:
            if output.output_type != 'display_data':
                cell.outputs.remove(output)
        return nb.ConverterNotebook.render_code(self, cell)

if __name__ == '__main__':
    infile = 'tests/test_display.ipynb'
    converter = CustomNotebookConverter(infile, 'test_only_display')
    converter.render()


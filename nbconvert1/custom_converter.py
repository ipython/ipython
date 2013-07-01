"""
This module gives a simple example of a custom notebook converter that only
captures display data and deletes the cell inputs.
"""

import copy
import nbconvert as nb


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

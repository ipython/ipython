from IPython.nbformat.nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook
)



ws = new_worksheet(name='worksheet1')

ws.cells.append(new_text_cell(
    text='Some NumPy Examples'
))


ws.cells.append(new_code_cell(
    input='import numpy'
))

ws.cells.append(new_code_cell(
    input='a = numpy.random.rand(100)'
))

ws.cells.append(new_code_cell(
    input='print a',
    output_text='<array a>',
    output_html='The HTML rep',
    output_latex='$a$',
    output_png=b'data',
    output_svg='<svg>',
    output_json='json data',
    output_javascript='var i=0;'
))

nb0 = new_notebook(
    name='nb0',
    worksheets=[ws, new_worksheet(name='worksheet2')]
)

nb0_py = """# <codecell>

import numpy

# <codecell>

a = numpy.random.rand(100)

# <codecell>

print a
"""



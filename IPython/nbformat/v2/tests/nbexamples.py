from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output
)



ws = new_worksheet(name='worksheet1')

ws.cells.append(new_text_cell(
    u'html',
    source='Some NumPy Examples',
    rendered='Some NumPy Examples'
))


ws.cells.append(new_code_cell(
    input='import numpy',
    prompt_number=1,
    collapsed=False
))

ws.cells.append(new_text_cell(
    u'markdown',
    source='Some NumPy Examples',
    rendered='Some NumPy Examples'
))

ws.cells.append(new_code_cell(
    input='a = numpy.random.rand(100)',
    prompt_number=2,
    collapsed=True
))

ws.cells.append(new_code_cell(
    input='print a',
    prompt_number=3,
    collapsed=False,
    outputs=[new_output(
        output_type=u'pyout',
        output_text=u'<array a>',
        output_html=u'The HTML rep',
        output_latex=u'$a$',
        output_png=b'data',
        output_jpeg=b'data',
        output_svg=u'<svg>',
        output_json=u'json data',
        output_javascript=u'var i=0;',
        prompt_number=3
    ),new_output(
        output_type=u'display_data',
        output_text=u'<array a>',
        output_html=u'The HTML rep',
        output_latex=u'$a$',
        output_png=b'data',
        output_jpeg=b'data',
        output_svg=u'<svg>',
        output_json=u'json data',
        output_javascript=u'var i=0;',
        prompt_number=4
    )]
))

nb0 = new_notebook(
    name='nb0',
    worksheets=[ws, new_worksheet(name='worksheet2')]
)

nb0_py = """# <nbformat>2</nbformat>

# <codecell>

import numpy

# </codecell>
# <codecell>

a = numpy.random.rand(100)

# </codecell>
# <codecell>

print a

# </codecell>
"""



from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_notebook
)



nb0 = new_notebook()

nb0.cells.append(new_text_cell(
    text='Some NumPy Examples'
))


nb0.cells.append(new_code_cell(
    code='import numpy',
    prompt_number=1
))

nb0.cells.append(new_code_cell(
    code='a = numpy.random.rand(100)',
    prompt_number=2
))

nb0.cells.append(new_code_cell(
    code='print a',
    prompt_number=3
))


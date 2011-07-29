from .nbbase import (
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output
)

def convert_to_this_nbformat(nb, orig_version=1):
    if orig_version == 1:
        newnb = new_notebook()
        ws = new_worksheet()
        for cell in nb.cells:
            if cell.cell_type == 'code':
                newcell = new_code_cell(input=cell.get('code'),prompt_number=cell.get('prompt_number'))
            elif cell.cell_type == 'text':
                newcell = new_text_cell(text=cell.get('text'))
            ws.cells.append(newcell)
        newnb.worksheets.append(ws)
        return newnb
    else:
        raise ValueError('Cannot convert a notebook from v%s to v2' % orig_version)



"""Code for converting notebooks to and from the v2 format.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .nbbase import (
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def convert_to_this_nbformat(nb, orig_version=1):
    """Convert a notebook to the v2 format.

    Parameters
    ----------
    nb : NotebookNode
        The Python representation of the notebook to convert.
    orig_version : int
        The original version of the notebook to convert.
    """
    if orig_version == 1:
        newnb = new_notebook()
        ws = new_worksheet()
        for cell in nb.cells:
            if cell.cell_type == u'code':
                newcell = new_code_cell(input=cell.get('code'),prompt_number=cell.get('prompt_number'))
            elif cell.cell_type == u'text':
                newcell = new_text_cell(u'markdown',source=cell.get('text'))
            ws.cells.append(newcell)
        newnb.worksheets.append(ws)
        return newnb
    else:
        raise ValueError('Cannot convert a notebook from v%s to v2' % orig_version)


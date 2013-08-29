"""Module that allows latex output notebooks to be conditioned before
they are converted.  Exposes a decorator (@cell_preprocessor) in
addition to the coalesce_streams pre-proccessor.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def cell_preprocessor(function):
    """
    Wrap a function to be executed on all cells of a notebook
    
    Wrapped Parameters
    ----------
    cell : NotebookNode cell
        Notebook cell being processed
    resources : dictionary
        Additional resources used in the conversion process.  Allows
        transformers to pass variables into the Jinja engine.
    index : int
        Index of the cell being processed
    """
    
    def wrappedfunc(nb, resources):
        for worksheet in nb.worksheets :
            for index, cell in enumerate(worksheet.cells):
                worksheet.cells[index], resources = function(cell, resources, index)
        return nb, resources
    return wrappedfunc


@cell_preprocessor
def coalesce_streams(cell, resources, index):
    """
    Merge consecutive sequences of stream output into single stream
    to prevent extra newlines inserted at flush calls
    
    Parameters
    ----------
    cell : NotebookNode cell
        Notebook cell being processed
    resources : dictionary
        Additional resources used in the conversion process.  Allows
        transformers to pass variables into the Jinja engine.
    index : int
        Index of the cell being processed
    """
    
    outputs = cell.get('outputs', [])
    if not outputs:
        return cell, resources
    
    last = outputs[0]
    new_outputs = [last]
    
    for output in outputs[1:]:
        if (output.output_type == 'stream' and
            last.output_type == 'stream' and
            last.stream == output.stream
        ):
            last.text += output.text
        else:
            new_outputs.append(output)
            last = output

    cell.outputs = new_outputs
    return cell, resources


def cell_preprocessor(function):
    """ wrap a function to be executed on all cells of a notebook

wrapped function parameters :
cell : the cell
other : external resources
index : index of the cell
"""
    def wrappedfunc(nb, other):
        for worksheet in nb.worksheets :
            for index, cell in enumerate(worksheet.cells):
                worksheet.cells[index], other = function(cell, other, index)
        return nb, other
    return wrappedfunc


@cell_preprocessor
def coalesce_streams(cell, other, count):
    """merge consecutive sequences of stream output into single stream

to prevent extra newlines inserted at flush calls

TODO: handle \r deletion
"""
    outputs = cell.get('outputs', [])
    if not outputs:
        return cell, other
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

    cell.outputs = new_outputs
    return cell, other


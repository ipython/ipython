"""

"""

def cell_preprocessor(function):
    """ wrap a function to be executed on all cells of a notebook

    wrapped function  parameters :
    cell  : the cell
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
def haspyout_transformer(cell, other, count):
    """
    Add a haspyout flag to cell that have it
    
    Easier for templating, where you can't know in advance
    wether to write the out prompt

    """
    cell.type = cell.cell_type
    cell.haspyout = False
    for out in cell.get('outputs', []):
        if out.output_type == 'pyout':
            cell.haspyout = True
            break
    return cell, other


# todo, make the key part configurable.
def _new_figure(data, fmt, count):
    """Create a new figure file in the given format.

    Returns a path relative to the input file.
    """
    figname = '_fig_%02i.%s' % (count, fmt)

    # Binary files are base64-encoded, SVG is already XML
    if fmt in ('png', 'jpg', 'pdf'):
        data = data.decode('base64')

    return figname, data

@cell_preprocessor
def extract_figure_transformer(cell, other, count):
    for i, out in enumerate(cell.get('outputs', [])):
        for type in ['html', 'pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg']:
            if out.hasattr(type):
                figname, data = _new_figure(out[type], type, count)
                cell.outputs[i][type] = figname
                out['key_'+type] = figname
                other[figname] = data
                count = count+1
    return cell, other


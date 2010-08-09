"""Return compact set of columns as a string with newlines for an
array of strings.

Adapted from the routine of the same name inside cmd.py

Author: Rocky Bernstein.
License: MIT Open Source License.
"""

import types

def columnize(array, displaywidth=80, colsep = '  ', 
              arrange_vertical=True, ljust=True, lineprefix=''):
    """Return a list of strings as a compact set of columns arranged 
    horizontally or vertically.

    For example, for a line width of 4 characters (arranged vertically):
        ['1', '2,', '3', '4'] => '1  3\n2  4\n'
   
    or arranged horizontally:
        ['1', '2,', '3', '4'] => '1  2\n3  4\n'
        
    Each column is only as wide as necessary.  By default, columns are
    separated by two spaces - one was not legible enough. Set "colsep"
    to adjust the string separate columns. Set `displaywidth' to set
    the line width. 

    Normally, consecutive items go down from the top to bottom from
    the left-most column to the right-most. If "arrange_vertical" is
    set false, consecutive items will go across, left to right, top to
    bottom."""
    if not isinstance(array, list) and not isinstance(array, tuple): 
        raise TypeError, (
            'array needs to be an instance of a list or a tuple')

    array = [str(i) for i in array]

    # Some degenerate cases
    size = len(array)
    if 0 == size: 
        return "<empty>\n"
    elif size == 1:
        return '%s\n' % str(array[0])

    displaywidth = max(4, displaywidth - len(lineprefix))
    if arrange_vertical:
        array_index = lambda nrows, row, col: nrows*col + row
        # Try every row count from 1 upwards
        for nrows in range(1, size):
            ncols = (size+nrows-1) // nrows
            colwidths = []
            totwidth = -len(colsep)
            for col in range(ncols):
                # get max column width for this column
                colwidth = 0
                for row in range(nrows):
                    i = array_index(nrows, row, col)
                    if i >= size: break
                    x = array[i]
                    colwidth = max(colwidth, len(x))
                    pass
                colwidths.append(colwidth)
                totwidth += colwidth + len(colsep)
                if totwidth > displaywidth: 
                    break
                pass
            if totwidth <= displaywidth: 
                break
            pass
        # The smallest number of rows computed and the
        # max widths for each column has been obtained.
        # Now we just have to format each of the
        # rows.
        s = ''
        for row in range(nrows):
            texts = []
            for col in range(ncols):
                i = row + nrows*col
                if i >= size:
                    x = ""
                else:
                    x = array[i]
                texts.append(x)
            while texts and not texts[-1]:
                del texts[-1]
            for col in range(len(texts)):
                if ljust:
                    texts[col] = texts[col].ljust(colwidths[col])
                else:
                    texts[col] = texts[col].rjust(colwidths[col])
                    pass
                pass
            s += "%s%s\n" % (lineprefix, str(colsep.join(texts)))
            pass
        return s
    else:
        array_index = lambda nrows, row, col: ncols*(row-1) + col
        # Try every column count from size downwards
        prev_colwidths = []
        colwidths = []
        for ncols in range(size, 0, -1):
            # Try every row count from 1 upwards
            min_rows = (size+ncols-1) // ncols
            for nrows in range(min_rows, size):
                rounded_size = nrows * ncols
                colwidths = []
                totwidth  = -len(colsep)
                for col in range(ncols):
                    # get max column width for this column
                    colwidth  = 0
                    for row in range(1, nrows+1):
                        i = array_index(nrows, row, col)
                        if i >= rounded_size: break
                        elif i < size:
                            x = array[i]
                            colwidth = max(colwidth, len(x))
                            pass
                        pass
                    colwidths.append(colwidth)
                    totwidth += colwidth + len(colsep)
                    if totwidth >= displaywidth: 
                        break
                    pass
                if totwidth <= displaywidth and i >= rounded_size-1:
                    # Found the right nrows and ncols
                    nrows  = row
                    break
                elif totwidth >= displaywidth:
                    # Need to reduce ncols
                    break
                pass
            if totwidth <= displaywidth and i >= rounded_size-1:
                break
            pass
        # The smallest number of rows computed and the
        # max widths for each column has been obtained.
        # Now we just have to format each of the
        # rows.
        s = ''
        for row in range(1, nrows+1):
            texts = []
            for col in range(ncols):
                i = array_index(nrows, row, col)
                if i >= size:
                    break
                else: x = array[i]
                texts.append(x)
                pass
            for col in range(len(texts)):
                if ljust:
                    texts[col] = texts[col].ljust(colwidths[col])
                else:
                    texts[col] = texts[col].rjust(colwidths[col])
                    pass
                pass
            s += "%s%s\n" % (lineprefix, str(colsep.join(texts)))
            pass
        return s
    pass


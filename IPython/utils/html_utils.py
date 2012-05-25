"""some html utilis"""
from IPython.core.display import HTML


def columnize_info(items, separator_width=1, displaywidth=80, empty=None):
    """ Get info on a list of string to display it as a multicolumns list

    returns :
    ---------

    a dict containing several parameters:

    'item_matrix'  : list of list with the innermost list representing a row
    'columns_number': number of columns
    'rows_number'   : number of rown
    'columns_width' : a list indicating the maximum length of the element in each columns

    Parameters :
    ------------
    separator_width : when trying to ajust the number of column, consider a separator size of this much caracters
    displaywidth    : try to fit the columns in this width
    empty           : if the number of items is different from nrows * ncols, fill with empty

    """
    # Note: this code is adapted from columnize 0.3.2.
    # See http://code.google.com/p/pycolumnize/

    # Some degenerate cases.
    size = len(items)
    if size == 0:
        return {'item_matrix' :[[empty]],
                'columns_number':1,
                'rows_number':1,
                'columns_width':[0]}
    elif size == 1:
        return {'item_matrix' :[[items[0]]],
                'columns_number':1,
                'rows_number':1,
                'columns_width':[len(items[0])]}

    # Special case: if any item is longer than the maximum width, there's no
    # point in triggering the logic below...
    item_len = map(len, items) # save these, we can reuse them below
    #longest = max(item_len)
    #if longest >= displaywidth:
    #    return (items, [longest])

    # Try every row count from 1 upwards
    array_index = lambda nrows, row, col: nrows*col + row
    nrows = 1
    for nrows in range(1, size):
        ncols = (size + nrows - 1) // nrows
        colwidths = []
        totwidth = -separator_width
        for col in range(ncols):
            # Get max column width for this column
            colwidth = 0
            for row in range(nrows):
                i = array_index(nrows, row, col)
                if i >= size:
                    break
                len_x = item_len[i]
                colwidth = max(colwidth, len_x)
            colwidths.append(colwidth)
            totwidth += colwidth + separator_width
            if totwidth > displaywidth:
                break
        if totwidth <= displaywidth:
            break

    # The smallest number of rows computed and the max widths for each
    # column has been obtained. Now we just have to format each of the rows.
    reorderd_items = []
    for row in range(nrows):
        texts = []
        for col in range(ncols):
            i = row + nrows*col
            if i >= size:
                texts.append(empty)
            else:
                texts.append(items[i])
        #while texts and not texts[-1]:
        #    del texts[-1]
        #for col in range(len(texts)):
        #    texts[col] = texts[col].ljust(colwidths[col])
        reorderd_items.append(texts)

    return {'item_matrix' :reorderd_items,
            'columns_number':ncols,
            'rows_number':nrows,
            'columns_width':colwidths}


def column_table(items, select=None) :
    """ return a html table of the item with a select class on one"""
    items_m = columnize_info(items)['item_matrix']
    return HTML(html_tableify(items_m, select=select))

def html_tableify(item_matrix, select=None) :
    """ returnr a string for an html table"""
    if not item_matrix :
        return ''
    html_cols = []
    tds = lambda text : u'<td>'+text+u'</td>'
    trs = lambda text : u'<tr>'+text+u'</tr>'
    tds_items = [map(tds, row) for row in item_matrix ]
    if select :
        row, col = select
        try :
            tds_items[row][col] = u'<td class="inverted">'\
                    +item_matrix[row][col]\
                    +u'</td>'
        except IndexError :
            pass
    #select the right item
    html_cols = map(trs, (u''.join(row) for row in tds_items))
    html = (u'<table class="completion">'+(u''.join(html_cols))+u'</table>')
    css = u"""
    <style>
    table.completion tr td
    { padding-right : 4px; }
    </style>
    """
    return css+html

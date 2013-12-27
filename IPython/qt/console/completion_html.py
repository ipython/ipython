"""A navigable completer for the qtconsole"""
# coding : utf-8
#-----------------------------------------------------------------------------
# Copyright (c) 2012, IPython Development Team.$
#
# Distributed under the terms of the Modified BSD License.$
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

# System library imports
import IPython.utils.text as text

from IPython.external.qt import QtCore, QtGui

#--------------------------------------------------------------------------
# Return an HTML table with selected item in a special class
#--------------------------------------------------------------------------
def html_tableify(item_matrix, select=None, header=None , footer=None) :
    """ returnr a string for an html table"""
    if not item_matrix :
        return ''
    html_cols = []
    tds = lambda text : u'<td>'+text+u'  </td>'
    trs = lambda text : u'<tr>'+text+u'</tr>'
    tds_items = [list(map(tds, row)) for row in item_matrix]
    if select :
        row, col = select
        tds_items[row][col] = u'<td class="inverted">'\
                +item_matrix[row][col]\
                +u'  </td>'
    #select the right item
    html_cols = map(trs, (u''.join(row) for row in tds_items))
    head = ''
    foot = ''
    if header :
        head = (u'<tr>'\
            +''.join((u'<td>'+header+u'</td>')*len(item_matrix[0]))\
            +'</tr>')

    if footer : 
        foot = (u'<tr>'\
            +''.join((u'<td>'+footer+u'</td>')*len(item_matrix[0]))\
            +'</tr>')
    html = (u'<table class="completion" style="white-space:pre">'+head+(u''.join(html_cols))+foot+u'</table>')
    return html

class SlidingInterval(object): 
    """a bound interval that follows a cursor
    
    internally used to scoll the completion view when the cursor 
    try to go beyond the edges, and show '...' when rows are hidden
    """
    
    _min = 0
    _max = 1
    _current = 0
    def __init__(self, maximum=1, width=6, minimum=0, sticky_lenght=1):
        """Create a new bounded interval
        
        any value return by this will be bound between maximum and 
        minimum. usual width will be 'width', and sticky_length 
        set when the return  interval should expand to max and min
        """
        self._min = minimum 
        self._max = maximum
        self._start = 0
        self._width = width
        self._stop = self._start+self._width+1
        self._sticky_lenght = sticky_lenght
        
    @property
    def current(self):
        """current cursor position"""
        return self._current
    
    @current.setter
    def current(self, value):
        """set current cursor position"""
        current = min(max(self._min, value), self._max)

        self._current = current

        if current > self._stop : 
            self._stop = current
            self._start = current-self._width
        elif current < self._start : 
            self._start = current
            self._stop = current + self._width

        if abs(self._start - self._min) <= self._sticky_lenght :
            self._start = self._min
        
        if abs(self._stop - self._max) <= self._sticky_lenght :
            self._stop = self._max

    @property 
    def start(self):
        """begiiing of interval to show"""
        return self._start
        
    @property
    def stop(self):
        """end of interval to show"""
        return self._stop

    @property
    def width(self):
        return self._stop - self._start

    @property 
    def nth(self):
        return self.current - self.start

class CompletionHtml(QtGui.QWidget):
    """ A widget for tab completion,  navigable by arrow keys """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    _items = ()
    _index = (0, 0)
    _consecutive_tab = 0
    _size = (1, 1)
    _old_cursor = None
    _start_position = 0
    _slice_start = 0
    _slice_len = 4

    def __init__(self, console_widget):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(console_widget._control, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CompletionHtml, self).__init__()

        self._text_edit = console_widget._control
        self._console_widget = console_widget
        self._text_edit.installEventFilter(self)
        self._sliding_interval = None
        self._justified_items = None

        # Ensure that the text edit keeps focus when widget is displayed.
        self.setFocusProxy(self._text_edit)


    def eventFilter(self, obj, event):
        """ Reimplemented to handle keyboard input and to auto-hide when the
            text edit loses focus.
        """
        if obj == self._text_edit:
            etype = event.type()
            if etype == QtCore.QEvent.KeyPress:
                key = event.key()
                if self._consecutive_tab == 0 and key in (QtCore.Qt.Key_Tab,):
                    return False
                elif self._consecutive_tab == 1 and key in (QtCore.Qt.Key_Tab,):
                    # ok , called twice, we grab focus, and show the cursor
                    self._consecutive_tab = self._consecutive_tab+1
                    self._update_list()
                    return True
                elif self._consecutive_tab == 2:
                    if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                        self._complete_current()
                        return True
                    if key in (QtCore.Qt.Key_Tab,):
                        self.select_right()
                        self._update_list()
                        return True
                    elif key in ( QtCore.Qt.Key_Down,):
                        self.select_down()
                        self._update_list()
                        return True
                    elif key in (QtCore.Qt.Key_Right,):
                        self.select_right()
                        self._update_list()
                        return True
                    elif key in ( QtCore.Qt.Key_Up,):
                        self.select_up()
                        self._update_list()
                        return True
                    elif key in ( QtCore.Qt.Key_Left,):
                        self.select_left()
                        self._update_list()
                        return True
                    elif key in ( QtCore.Qt.Key_Escape,):
                        self.cancel_completion()
                        return True
                    else :
                        self.cancel_completion()
                else:
                    self.cancel_completion()

            elif etype == QtCore.QEvent.FocusOut:
                self.cancel_completion()

        return super(CompletionHtml, self).eventFilter(obj, event)

    #--------------------------------------------------------------------------
    # 'CompletionHtml' interface
    #--------------------------------------------------------------------------
    def cancel_completion(self):
        """Cancel the completion

        should be called when the completer have to be dismissed

        This reset internal variable, clearing the temporary buffer
        of the console where the completion are shown.
        """
        self._consecutive_tab = 0
        self._slice_start = 0
        self._console_widget._clear_temporary_buffer()
        self._index = (0, 0)
        if(self._sliding_interval):
            self._sliding_interval = None

    #
    #  ...  2 4 4 4 4 4 4 4 4 4 4  4  4
    #   2   2 4 4 4 4 4 4 4 4 4 4  4  4
    #
    #2  2   x x x x x x x x x x x  5  5
    #6  6   x x x x x x x x x x x  5  5
    #6  6   x x x x x x x x x x ?  5  5
    #6  6   x x x x x x x x x x ?  1  1
    #
    #3  3   3 3 3 3 3 3 3 3 3 3 1  1  1 ...
    #3  3   3 3 3 3 3 3 3 3 3 3 1  1  1 ...
    def _select_index(self, row, col):
        """Change the selection index, and make sure it stays in the right range

        A little more complicated than just dooing modulo the number of row columns
        to be sure to cycle through all element.

        horizontaly, the element are maped like this :
        to r <-- a b c d e f --> to g
        to f <-- g h i j k l --> to m
        to l <-- m n o p q r --> to a

        and vertically
        a d g j m p
        b e h k n q
        c f i l o r
        """

        nr, nc = self._size
        nr = nr-1
        nc = nc-1

        # case 1
        if (row > nr and col >= nc) or (row >= nr and col > nc):
            self._select_index(0, 0)
        # case 2
        elif (row <= 0 and col < 0) or  (row < 0 and col <= 0):
            self._select_index(nr, nc)
        # case 3
        elif row > nr :
            self._select_index(0, col+1)
        # case 4
        elif row < 0 :
            self._select_index(nr, col-1)
        # case 5
        elif col > nc :
            self._select_index(row+1, 0)
        # case 6
        elif col < 0 :
            self._select_index(row-1, nc)
        elif 0 <= row and row <= nr and 0 <= col and col <= nc :
            self._index = (row, col)
        else :
            raise NotImplementedError("you'r trying to go where no completion\
                           have gone before : %d:%d (%d:%d)"%(row, col, nr, nc) )


    @property
    def _slice_end(self):
        end = self._slice_start+self._slice_len
        if end > len(self._items) :
            return None
        return end

    def select_up(self):
        """move cursor up"""
        r, c = self._index
        self._select_index(r-1, c)

    def select_down(self):
        """move cursor down"""
        r, c = self._index
        self._select_index(r+1, c)

    def select_left(self):
        """move cursor left"""
        r, c = self._index
        self._select_index(r, c-1)

    def select_right(self):
        """move cursor right"""
        r, c = self._index
        self._select_index(r, c+1)

    def show_items(self, cursor, items):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        if not items :
            return
        self._start_position = cursor.position()
        self._consecutive_tab = 1
        items_m, ci = text.compute_item_matrix(items, empty=' ')
        self._sliding_interval = SlidingInterval(len(items_m)-1)

        self._items = items_m
        self._size = (ci['rows_numbers'], ci['columns_numbers'])
        self._old_cursor = cursor
        self._index = (0, 0)
        sjoin = lambda x : [ y.ljust(w, ' ') for y, w in zip(x, ci['columns_width'])]
        self._justified_items = list(map(sjoin, items_m))
        self._update_list(hilight=False)




    def _update_list(self, hilight=True):
        """ update the list of completion and hilight the currently selected completion """
        self._sliding_interval.current = self._index[0]
        head = None
        foot = None
        if self._sliding_interval.start > 0 : 
            head = '...'

        if self._sliding_interval.stop < self._sliding_interval._max:
            foot = '...'
        items_m = self._justified_items[\
                       self._sliding_interval.start:\
                       self._sliding_interval.stop+1\
                                       ]

        self._console_widget._clear_temporary_buffer()
        if(hilight):
            sel = (self._sliding_interval.nth, self._index[1])
        else :
            sel = None

        strng = html_tableify(items_m, select=sel, header=head, footer=foot)
        self._console_widget._fill_temporary_buffer(self._old_cursor, strng, html=True)

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _complete_current(self):
        """ Perform the completion with the currently selected item.
        """
        i = self._index
        item = self._items[i[0]][i[1]]
        item = item.strip()
        if item :
            self._current_text_cursor().insertText(item)
        self.cancel_completion()

    def _current_text_cursor(self):
        """ Returns a cursor with text between the start position and the
            current position selected.
        """
        cursor = self._text_edit.textCursor()
        if cursor.position() >= self._start_position:
            cursor.setPosition(self._start_position,
                               QtGui.QTextCursor.KeepAnchor)
        return cursor


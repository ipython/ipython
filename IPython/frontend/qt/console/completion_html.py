# System library imports
from IPython.external.qt import QtCore, QtGui
import IPython.utils.html_utils as html_utils


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

    def __init__(self, console_widget):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(console_widget._control, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CompletionHtml, self).__init__()

        self._text_edit = console_widget._control
        self._console_widget = console_widget
        self._text_edit.installEventFilter(self)

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
                    else :
                        self._cancel_completion()
                else:
                    self._cancel_completion()

            elif etype == QtCore.QEvent.FocusOut:
                self._cancel_completion()

        return super(CompletionHtml, self).eventFilter(obj, event)

    #--------------------------------------------------------------------------
    # 'CompletionHtml' interface
    #--------------------------------------------------------------------------
    def _cancel_completion(self):
        """Cancel the completion, reseting internal variable, clearing buffer """
        self._consecutive_tab = 0
        self._console_widget._clear_temporary_buffer()
        self._index = (0, 0)

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
        ci = html_utils.columnize_info(items, empty=' ')
        self._items = ci['item_matrix']
        self._size = (ci['rows_number'], ci['columns_number'])
        self._old_cursor = cursor
        self._index = (0, 0)
        self._update_list(hilight=False)


    def _update_list(self, hilight=True):
        """ update the list of completion and hilight the currently selected completion """
        if len(self._items) > 100:
            items = self._items[:100]
        else :
            items = self._items
        items_m = items

        self._console_widget._clear_temporary_buffer()
        if(hilight):
            strng = html_utils.html_tableify(items_m, select=self._index)
        else:
            strng = html_utils.html_tableify(items_m, select=None)
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
        self._cancel_completion()

    def _current_text_cursor(self):
        """ Returns a cursor with text between the start position and the
            current position selected.
        """
        cursor = self._text_edit.textCursor()
        if cursor.position() >= self._start_position:
            cursor.setPosition(self._start_position,
                               QtGui.QTextCursor.KeepAnchor)
        return cursor



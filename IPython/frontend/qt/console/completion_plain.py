# System library imports
from IPython.external.qt import QtCore, QtGui
import IPython.utils.html_utils as html_utils


class CompletionPlain(QtGui.QWidget):
    """ A widget for tab completion,  navigable by arrow keys """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    _items = ()
    _index = (0, 0)
    _old_cursor = None

    def __init__(self, console_widget):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(console_widget._control, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CompletionPlain, self).__init__()

        self._text_edit = console_widget._control
        self._console_widget = console_widget

        self._text_edit.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ Reimplemented to handle keyboard input and to auto-hide when the
            text edit loses focus.
        """
        if obj == self._text_edit:
            etype = event.type()

            if etype == QtCore.QEvent.KeyPress:
                self._cancel_completion()

        return super(CompletionPlain, self).eventFilter(obj, event)

    #--------------------------------------------------------------------------
    # 'CompletionPlain' interface
    #--------------------------------------------------------------------------
    def _cancel_completion(self):
        """Cancel the completion, reseting internal variable, clearing buffer """
        self._console_widget._clear_temporary_buffer()
        self._index = (0, 0)


    def show_items(self, cursor, items):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        if not items :
            return

        ci = html_utils.columnize_info(items, empty=' ')
        self._items = ci['item_matrix']
        self._old_cursor = cursor
        self._update_list()


    def _update_list(self):
        """ update the list of completion and hilight the currently selected completion """
        if len(self._items) > 100:
            items = self._items[:100]
        else :
            items = self._items
        items_m = items

        self._console_widget._clear_temporary_buffer()
        strng = html_utils.html_tableify(items_m, select=None)
        self._console_widget._fill_temporary_buffer(self._old_cursor, strng, html=True)

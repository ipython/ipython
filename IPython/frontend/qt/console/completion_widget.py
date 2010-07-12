# System library imports
from PyQt4 import QtCore, QtGui


class CompletionWidget(QtGui.QListWidget):
    """ A widget for GUI tab completion.
    """

    #--------------------------------------------------------------------------
    # 'QWidget' interface
    #--------------------------------------------------------------------------

    def __init__(self, parent):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(parent, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        QtGui.QListWidget.__init__(self, parent)

        self.setWindowFlags(QtCore.Qt.ToolTip | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_StaticContents)

        # Ensure that parent keeps focus when widget is displayed.
        self.setFocusProxy(parent)

        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setFrameShape(QtGui.QFrame.StyledPanel)

        self.itemActivated.connect(self._complete_current)

    def hideEvent(self, event):
        """ Reimplemented to disconnect the cursor movement handler.
        """
        QtGui.QListWidget.hideEvent(self, event)
        self.parent().cursorPositionChanged.disconnect(self._update_current)
        
    def keyPressEvent(self, event):
        """ Reimplemented to update the list.
        """
        key, text = event.key(), event.text()

        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, 
                   QtCore.Qt.Key_Tab):
            self._complete_current()
            event.accept()

        elif key == QtCore.Qt.Key_Escape:
            self.hide()
            event.accept()

        elif key in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, 
                     QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown, 
                     QtCore.Qt.Key_Home, QtCore.Qt.Key_End):
            QtGui.QListWidget.keyPressEvent(self, event)
            event.accept()

        else:
            event.ignore()

    def showEvent(self, event):
        """ Reimplemented to connect the cursor movement handler.
        """
        QtGui.QListWidget.showEvent(self, event)
        self.parent().cursorPositionChanged.connect(self._update_current)

    #--------------------------------------------------------------------------
    # 'CompletionWidget' interface
    #--------------------------------------------------------------------------

    def show_items(self, cursor, items):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        text_edit = self.parent()
        point = text_edit.cursorRect(cursor).bottomRight()
        point = text_edit.mapToGlobal(point)
        screen_rect = QtGui.QApplication.desktop().availableGeometry(self)
        if screen_rect.size().height() - point.y() - self.height() < 0:
            point = text_edit.mapToGlobal(text_edit.cursorRect().topRight())
            point.setY(point.y() - self.height())
        self.move(point)

        self._start_position = cursor.position()
        self.clear()
        self.addItems(items)
        self.setCurrentRow(0)
        self.show()

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _complete_current(self):
        """ Perform the completion with the currently selected item.
        """
        self._current_text_cursor().insertText(self.currentItem().text())
        self.hide()

    def _current_text_cursor(self):
        """ Returns a cursor with text between the start position and the
            current position selected.
        """
        cursor = self.parent().textCursor()
        if cursor.position() >= self._start_position:
            cursor.setPosition(self._start_position, 
                               QtGui.QTextCursor.KeepAnchor)
        return cursor
        
    def _update_current(self):
        """ Updates the current item based on the current text.
        """
        prefix = self._current_text_cursor().selectedText()
        if prefix:
            items = self.findItems(prefix, (QtCore.Qt.MatchStartsWith | 
                                            QtCore.Qt.MatchCaseSensitive))
            if items:
                self.setCurrentItem(items[0])
            else:
                self.hide()
        else:
            self.hide()

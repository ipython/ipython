# System library imports
from IPython.external.qt import QtCore, QtGui


class CompletionWidget(QtGui.QListWidget):
    """ A widget for GUI tab completion.
    """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    def __init__(self, console_widget):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        text_edit = console_widget._control
        assert isinstance(text_edit, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CompletionWidget, self).__init__()

        self._text_edit = text_edit

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        self.setWindowFlags(QtCore.Qt.ToolTip | QtCore.Qt.WindowStaysOnTopHint)

        # Ensure that the text edit keeps focus when widget is displayed.
        self.setFocusProxy(self._text_edit)

        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setFrameShape(QtGui.QFrame.StyledPanel)

        self.itemActivated.connect(self._complete_current)

    def eventFilter(self, obj, event):
        """ Reimplemented to handle keyboard input and to auto-hide when the
            text edit loses focus.
        """
        if obj == self._text_edit:
            etype = event.type()

            if etype == QtCore.QEvent.KeyPress:
                key, text = event.key(), event.text()
                if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter,
                           QtCore.Qt.Key_Tab):
                    self._complete_current()
                    return True
                elif key == QtCore.Qt.Key_Escape:
                    self.hide()
                    return True
                elif key in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down,
                             QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown,
                             QtCore.Qt.Key_Home, QtCore.Qt.Key_End):
                    self.keyPressEvent(event)
                    return True

            elif etype == QtCore.QEvent.FocusOut:
                self.hide()

        return super(CompletionWidget, self).eventFilter(obj, event)

    #--------------------------------------------------------------------------
    # 'QWidget' interface
    #--------------------------------------------------------------------------

    def hideEvent(self, event):
        """ Reimplemented to disconnect signal handlers and event filter.
        """
        super(CompletionWidget, self).hideEvent(event)
        self._text_edit.cursorPositionChanged.disconnect(self._update_current)
        self._text_edit.removeEventFilter(self)

    def showEvent(self, event):
        """ Reimplemented to connect signal handlers and event filter.
        """
        super(CompletionWidget, self).showEvent(event)
        self._text_edit.cursorPositionChanged.connect(self._update_current)
        self._text_edit.installEventFilter(self)

    #--------------------------------------------------------------------------
    # 'CompletionWidget' interface
    #--------------------------------------------------------------------------

    def show_items(self, cursor, items):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        text_edit = self._text_edit
        point = text_edit.cursorRect(cursor).bottomRight()
        point = text_edit.mapToGlobal(point)
        height = self.sizeHint().height()
        screen_rect = QtGui.QApplication.desktop().availableGeometry(self)
        if screen_rect.size().height() - point.y() - height < 0:
            point = text_edit.mapToGlobal(text_edit.cursorRect().topRight())
            point.setY(point.y() - height)
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
        cursor = self._text_edit.textCursor()
        if cursor.position() >= self._start_position:
            cursor.setPosition(self._start_position,
                               QtGui.QTextCursor.KeepAnchor)
        return cursor

    def _update_current(self):
        """ Updates the current item based on the current text.
        """
        prefix = self._current_text_cursor().selection().toPlainText()
        if prefix:
            items = self.findItems(prefix, (QtCore.Qt.MatchStartsWith |
                                            QtCore.Qt.MatchCaseSensitive))
            if items:
                self.setCurrentItem(items[0])
            else:
                self.hide()
        else:
            self.hide()

    def cancel_completion(self):
        self.hide()

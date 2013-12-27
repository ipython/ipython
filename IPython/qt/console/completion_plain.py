"""A simple completer for the qtconsole"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, IPython Development Team.$
#
# Distributed under the terms of the Modified BSD License.$
#
# The full license is in the file COPYING.txt, distributed with this software.
#-------------------------------------------------------------------

# System library imports
from IPython.external.qt import QtCore, QtGui
import IPython.utils.text as text


class CompletionPlain(QtGui.QWidget):
    """ A widget for tab completion,  navigable by arrow keys """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

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

            if etype in( QtCore.QEvent.KeyPress, QtCore.QEvent.FocusOut ):
                self.cancel_completion()

        return super(CompletionPlain, self).eventFilter(obj, event)

    #--------------------------------------------------------------------------
    # 'CompletionPlain' interface
    #--------------------------------------------------------------------------
    def cancel_completion(self):
        """Cancel the completion, reseting internal variable, clearing buffer """
        self._console_widget._clear_temporary_buffer()


    def show_items(self, cursor, items):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        if not items :
            return
        self.cancel_completion()
        strng = text.columnize(items)
        self._console_widget._fill_temporary_buffer(cursor, strng, html=False)

""" Provides bracket matching for Q[Plain]TextEdit widgets.
"""

# System library imports
from IPython.external.qt import QtCore, QtGui


class BracketMatcher(QtCore.QObject):
    """ Matches square brackets, braces, and parentheses based on cursor
        position.
    """

    # Protected class variables.
    _opening_map = { '(':')', '{':'}', '[':']' }
    _closing_map = { ')':'(', '}':'{', ']':'[' }

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    def __init__(self, text_edit):
        """ Create a call tip manager that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(text_edit, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(BracketMatcher, self).__init__()

        # The format to apply to matching brackets.
        self.format = QtGui.QTextCharFormat()
        self.format.setBackground(QtGui.QColor('silver'))

        self._text_edit = text_edit
        text_edit.cursorPositionChanged.connect(self._cursor_position_changed)

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _find_match(self, position):
        """ Given a valid position in the text document, try to find the
            position of the matching bracket. Returns -1 if unsuccessful.
        """
        # Decide what character to search for and what direction to search in.
        document = self._text_edit.document()
        start_char = document.characterAt(position)
        search_char = self._opening_map.get(start_char)
        if search_char:
            increment = 1
        else:
            search_char = self._closing_map.get(start_char)
            if search_char:
                increment = -1
            else:
                return -1

        # Search for the character.
        char = start_char
        depth = 0
        while position >= 0 and position < document.characterCount():
            if char == start_char:
                depth += 1
            elif char == search_char:
                depth -= 1
            if depth == 0:
                break
            position += increment
            char = document.characterAt(position)
        else:
            position = -1
        return position

    def _selection_for_character(self, position):
        """ Convenience method for selecting a character.
        """
        selection = QtGui.QTextEdit.ExtraSelection()
        cursor = self._text_edit.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(QtGui.QTextCursor.NextCharacter,
                            QtGui.QTextCursor.KeepAnchor)
        selection.cursor = cursor
        selection.format = self.format
        return selection

    #------ Signal handlers ----------------------------------------------------

    def _cursor_position_changed(self):
        """ Updates the document formatting based on the new cursor position.
        """
        # Clear out the old formatting.
        self._text_edit.setExtraSelections([])

        # Attempt to match a bracket for the new cursor position.
        cursor = self._text_edit.textCursor()
        if not cursor.hasSelection():
            position = cursor.position() - 1
            match_position = self._find_match(position)
            if match_position != -1:
                extra_selections = [ self._selection_for_character(pos)
                                     for pos in (position, match_position) ]
                self._text_edit.setExtraSelections(extra_selections)

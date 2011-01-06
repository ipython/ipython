# System library imports
from IPython.external.qt import QtGui

# Local imports
from console_widget import ConsoleWidget


class HistoryConsoleWidget(ConsoleWidget):
    """ A ConsoleWidget that keeps a history of the commands that have been
        executed and provides a readline-esque interface to this history.
    """
    
    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        super(HistoryConsoleWidget, self).__init__(*args, **kw)

        # HistoryConsoleWidget protected variables.
        self._history = []
        self._history_index = 0
        self._history_prefix = ''

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def execute(self, source=None, hidden=False, interactive=False):
        """ Reimplemented to the store history.
        """
        if not hidden:
            history = self.input_buffer if source is None else source

        executed = super(HistoryConsoleWidget, self).execute(
            source, hidden, interactive)

        if executed and not hidden:
            # Save the command unless it was an empty string or was identical 
            # to the previous command.
            history = history.rstrip()
            if history and (not self._history or self._history[-1] != history):
                self._history.append(history)

            # Move the history index to the most recent item.
            self._history_index = len(self._history)

        return executed

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _up_pressed(self):
        """ Called when the up key is pressed. Returns whether to continue
            processing the event.
        """
        prompt_cursor = self._get_prompt_cursor()
        if self._get_cursor().blockNumber() == prompt_cursor.blockNumber():

            # Set a search prefix based on the cursor position.
            col = self._get_input_buffer_cursor_column()
            input_buffer = self.input_buffer
            if self._history_index == len(self._history) or \
                    (self._history_prefix and col != len(self._history_prefix)):
                self._history_index = len(self._history)
                self._history_prefix = input_buffer[:col]

            # Perform the search.
            self.history_previous(self._history_prefix)

            # Go to the first line of the prompt for seemless history scrolling.
            # Emulate readline: keep the cursor position fixed for a prefix
            # search.
            cursor = self._get_prompt_cursor()
            if self._history_prefix:
                cursor.movePosition(QtGui.QTextCursor.Right, 
                                    n=len(self._history_prefix))
            else:
                cursor.movePosition(QtGui.QTextCursor.EndOfLine)
            self._set_cursor(cursor)

            return False

        return True

    def _down_pressed(self):
        """ Called when the down key is pressed. Returns whether to continue
            processing the event.
        """
        end_cursor = self._get_end_cursor()
        if self._get_cursor().blockNumber() == end_cursor.blockNumber():

            # Perform the search.
            self.history_next(self._history_prefix)

            # Emulate readline: keep the cursor position fixed for a prefix
            # search. (We don't need to move the cursor to the end of the buffer
            # in the other case because this happens automatically when the
            # input buffer is set.)
            if self._history_prefix:
                cursor = self._get_prompt_cursor()
                cursor.movePosition(QtGui.QTextCursor.Right, 
                                    n=len(self._history_prefix))
                self._set_cursor(cursor)

            return False

        return True

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def history_previous(self, prefix=''):
        """ If possible, set the input buffer to a previous item in the history.

        Parameters:
        -----------
        prefix : str, optional
            If specified, search for an item with this prefix.
        """
        index = self._history_index
        while index > 0:
            index -= 1
            history = self._history[index]
            if history.startswith(prefix):
                break
        else:
            history = None
        
        if history is not None:
            self._history_index = index
            self.input_buffer = history

    def history_next(self, prefix=''):
        """ Set the input buffer to a subsequent item in the history, or to the
        original search prefix if there is no such item.

        Parameters:
        -----------
        prefix : str, optional
            If specified, search for an item with this prefix.
        """
        while self._history_index < len(self._history) - 1:
            self._history_index += 1
            history = self._history[self._history_index]
            if history.startswith(prefix):
                break
        else:
            self._history_index = len(self._history)
            history = prefix
        self.input_buffer = history

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _set_history(self, history):
        """ Replace the current history with a sequence of history items.
        """
        self._history = list(history)
        self._history_index = len(self._history)

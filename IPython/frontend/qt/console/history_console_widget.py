# System library imports
from PyQt4 import QtGui

# Local imports
from console_widget import ConsoleWidget


class HistoryConsoleWidget(ConsoleWidget):
    """ A ConsoleWidget that keeps a history of the commands that have been
        executed.
    """
    
    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        super(HistoryConsoleWidget, self).__init__(*args, **kw)
        self._history = []
        self._history_index = 0

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
            self.history_previous()

            # Go to the first line of prompt for seemless history scrolling.
            cursor = self._get_prompt_cursor()
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
            self.history_next()
            return False
        return True

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def history_previous(self):
        """ If possible, set the input buffer to the previous item in the
            history.
        """
        if self._history_index > 0:
            self._history_index -= 1
            self.input_buffer = self._history[self._history_index]

    def history_next(self):
        """ Set the input buffer to the next item in the history, or a blank
            line if there is no subsequent item.
        """
        if self._history_index < len(self._history):
            self._history_index += 1
            if self._history_index < len(self._history):
                self.input_buffer = self._history[self._history_index]
            else:
                self.input_buffer = ''

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _set_history(self, history):
        """ Replace the current history with a sequence of history items.
        """
        self._history = list(history)
        self._history_index = len(self._history)

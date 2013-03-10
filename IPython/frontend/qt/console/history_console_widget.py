# System library imports
from IPython.external.qt import QtGui

# Local imports
from IPython.utils.traitlets import Bool
from console_widget import ConsoleWidget


class HistoryConsoleWidget(ConsoleWidget):
    """ A ConsoleWidget that keeps a history of the commands that have been
        executed and provides a readline-esque interface to this history.
    """

    #------ Configuration ------------------------------------------------------

    # If enabled, the input buffer will become "locked" to history movement when
    # an edit is made to a multi-line input buffer. To override the lock, use
    # Shift in conjunction with the standard history cycling keys.
    history_lock = Bool(False, config=True)

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        super(HistoryConsoleWidget, self).__init__(*args, **kw)

        # HistoryConsoleWidget protected variables.
        self._history = []
        self._history_edits = {}
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

            # Emulate readline: reset all history edits.
            self._history_edits = {}

            # Move the history index to the most recent item.
            self._history_index = len(self._history)

        return executed

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _up_pressed(self, shift_modifier):
        """ Called when the up key is pressed. Returns whether to continue
            processing the event.
        """
        prompt_cursor = self._get_prompt_cursor()
        if self._get_cursor().blockNumber() == prompt_cursor.blockNumber():
            # Bail out if we're locked.
            if self._history_locked() and not shift_modifier:
                return False

            # Set a search prefix based on the cursor position.
            col = self._get_input_buffer_cursor_column()
            input_buffer = self.input_buffer
            # use the *shortest* of the cursor column and the history prefix
            # to determine if the prefix has changed
            n = min(col, len(self._history_prefix))
            
            # prefix changed, restart search from the beginning
            if (self._history_prefix[:n] != input_buffer[:n]):
                self._history_index = len(self._history)
            
            # the only time we shouldn't set the history prefix
            # to the line up to the cursor is if we are already
            # in a simple scroll (no prefix),
            # and the cursor is at the end of the first line
            
            # check if we are at the end of the first line
            c = self._get_cursor()
            current_pos = c.position()
            c.movePosition(QtGui.QTextCursor.EndOfLine)
            at_eol = (c.position() == current_pos)
            
            if self._history_index == len(self._history) or \
                not (self._history_prefix == '' and at_eol) or \
                not (self._get_edited_history(self._history_index)[:col] == input_buffer[:col]):
                self._history_prefix = input_buffer[:col]

            # Perform the search.
            self.history_previous(self._history_prefix,
                                    as_prefix=not shift_modifier)

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

    def _down_pressed(self, shift_modifier):
        """ Called when the down key is pressed. Returns whether to continue
            processing the event.
        """
        end_cursor = self._get_end_cursor()
        if self._get_cursor().blockNumber() == end_cursor.blockNumber():
            # Bail out if we're locked.
            if self._history_locked() and not shift_modifier:
                return False

            # Perform the search.
            replaced = self.history_next(self._history_prefix,
                                            as_prefix=not shift_modifier)

            # Emulate readline: keep the cursor position fixed for a prefix
            # search. (We don't need to move the cursor to the end of the buffer
            # in the other case because this happens automatically when the
            # input buffer is set.)
            if self._history_prefix and replaced:
                cursor = self._get_prompt_cursor()
                cursor.movePosition(QtGui.QTextCursor.Right,
                                    n=len(self._history_prefix))
                self._set_cursor(cursor)

            return False

        return True

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def history_previous(self, substring='', as_prefix=True):
        """ If possible, set the input buffer to a previous history item.

        Parameters:
        -----------
        substring : str, optional
            If specified, search for an item with this substring.
        as_prefix : bool, optional
            If True, the substring must match at the beginning (default).

        Returns:
        --------
        Whether the input buffer was changed.
        """
        index = self._history_index
        replace = False
        while index > 0:
            index -= 1
            history = self._get_edited_history(index)
            if (as_prefix and history.startswith(substring)) \
                or (not as_prefix and substring in history):
                replace = True
                break

        if replace:
            self._store_edits()
            self._history_index = index
            self.input_buffer = history

        return replace

    def history_next(self, substring='', as_prefix=True):
        """ If possible, set the input buffer to a subsequent history item.

        Parameters:
        -----------
        substring : str, optional
            If specified, search for an item with this substring.
        as_prefix : bool, optional
            If True, the substring must match at the beginning (default).

        Returns:
        --------
        Whether the input buffer was changed.
        """
        index = self._history_index
        replace = False
        while index < len(self._history):
            index += 1
            history = self._get_edited_history(index)
            if (as_prefix and history.startswith(substring)) \
                or (not as_prefix and substring in history):
                replace = True
                break

        if replace:
            self._store_edits()
            self._history_index = index
            self.input_buffer = history

        return replace

    def history_tail(self, n=10):
        """ Get the local history list.

        Parameters:
        -----------
        n : int
            The (maximum) number of history items to get.
        """
        return self._history[-n:]

    def _request_update_session_history_length(self):
        msg_id = self.kernel_client.shell_channel.execute('',
            silent=True,
            user_expressions={
                'hlen':'len(get_ipython().history_manager.input_hist_raw)',
                }
            )
        self._request_info['execute'][msg_id] = self._ExecutionRequest(msg_id, 'save_magic')

    def _handle_execute_reply(self, msg):
        """ Handles replies for code execution, here only session history length
        """
        msg_id = msg['parent_header']['msg_id']
        info = self._request_info['execute'].pop(msg_id,None)
        if info and info.kind == 'save_magic' and not self._hidden:
            content = msg['content']
            status = content['status']
            if status == 'ok':
                self._max_session_history=(int(content['user_expressions']['hlen']))

    def save_magic(self):
        # update the session history length
        self._request_update_session_history_length()

        file_name,extFilter = QtGui.QFileDialog.getSaveFileName(self,
            "Enter A filename",
            filter='Python File (*.py);; All files (*.*)'
            )

        # let's the user search/type for a file name, while the history length
        # is fetched

        if file_name:
            hist_range, ok = QtGui.QInputDialog.getText(self,
                'Please enter an interval of command to save',
                'Saving commands:',
                text=str('1-'+str(self._max_session_history))
                )
            if ok:
                self.execute("%save"+" "+file_name+" "+str(hist_range))

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _history_locked(self):
        """ Returns whether history movement is locked.
        """
        return (self.history_lock and
                (self._get_edited_history(self._history_index) !=
                 self.input_buffer) and
                (self._get_prompt_cursor().blockNumber() !=
                 self._get_end_cursor().blockNumber()))

    def _get_edited_history(self, index):
        """ Retrieves a history item, possibly with temporary edits.
        """
        if index in self._history_edits:
            return self._history_edits[index]
        elif index == len(self._history):
            return unicode()
        return self._history[index]

    def _set_history(self, history):
        """ Replace the current history with a sequence of history items.
        """
        self._history = list(history)
        self._history_edits = {}
        self._history_index = len(self._history)

    def _store_edits(self):
        """ If there are edits to the current input buffer, store them.
        """
        current = self.input_buffer
        if self._history_index == len(self._history) or \
                self._history[self._history_index] != current:
            self._history_edits[self._history_index] = current

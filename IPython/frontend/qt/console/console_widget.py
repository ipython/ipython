# Standard library imports
import re
import sys

# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from completion_widget import CompletionWidget


class AnsiCodeProcessor(object):
    """ Translates ANSI escape codes into readable attributes.
    """

    def __init__(self):
        self.ansi_colors = ( # Normal, Bright/Light
                             ('#000000', '#7f7f7f'), # 0: black
                             ('#cd0000', '#ff0000'), # 1: red
                             ('#00cd00', '#00ff00'), # 2: green
                             ('#cdcd00', '#ffff00'), # 3: yellow
                             ('#0000ee', '#0000ff'), # 4: blue
                             ('#cd00cd', '#ff00ff'), # 5: magenta
                             ('#00cdcd', '#00ffff'), # 6: cyan
                             ('#e5e5e5', '#ffffff')) # 7: white
        self.reset()
        
    def set_code(self, code):
        """ Set attributes based on code.
        """
        if code == 0:
            self.reset()
        elif code == 1:
            self.intensity = 1
            self.bold = True
        elif code == 3:
            self.italic = True
        elif code == 4:
            self.underline = True
        elif code == 22:
            self.intensity = 0
            self.bold = False
        elif code == 23:
            self.italic = False
        elif code == 24:
            self.underline = False
        elif code >= 30 and code <= 37:
            self.foreground_color = code - 30
        elif code == 39:
            self.foreground_color = None
        elif code >= 40 and code <= 47:
            self.background_color = code - 40
        elif code == 49:
            self.background_color = None
        
    def reset(self):
        """ Reset attributs to their default values.
        """
        self.intensity = 0
        self.italic = False
        self.bold = False
        self.underline = False
        self.foreground_color = None
        self.background_color = None


class QtAnsiCodeProcessor(AnsiCodeProcessor):
    """ Translates ANSI escape codes into QTextCharFormats.
    """
    
    def get_format(self):
        """ Returns a QTextCharFormat that encodes the current style attributes.
        """
        format = QtGui.QTextCharFormat()

        # Set foreground color
        if self.foreground_color is not None:
            color = self.ansi_colors[self.foreground_color][self.intensity]
            format.setForeground(QtGui.QColor(color))

        # Set background color
        if self.background_color is not None:
            color = self.ansi_colors[self.background_color][self.intensity]
            format.setBackground(QtGui.QColor(color))

        # Set font weight/style options
        if self.bold:
            format.setFontWeight(QtGui.QFont.Bold)
        else:
            format.setFontWeight(QtGui.QFont.Normal)
        format.setFontItalic(self.italic)
        format.setFontUnderline(self.underline)

        return format


class ConsoleWidget(QtGui.QPlainTextEdit):
    """ Base class for console-type widgets. This class is mainly concerned with
        dealing with the prompt, keeping the cursor inside the editing line, and
        handling ANSI escape sequences.
    """

    # Whether to process ANSI escape codes.
    ansi_codes = True

    # The maximum number of lines of text before truncation.
    buffer_size = 500

    # Whether to use a CompletionWidget or plain text output for tab completion.
    gui_completion = True

    # Whether to override ShortcutEvents for the keybindings defined by this
    # widget (Ctrl+n, Ctrl+a, etc). Enable this if you want this widget to take
    # priority (when it has focus) over, e.g., window-level menu shortcuts.
    override_shortcuts = False

    # Protected class variables.
    _ansi_pattern = re.compile('\x01?\x1b\[(.*?)m\x02?')
    _ctrl_down_remap = { QtCore.Qt.Key_B : QtCore.Qt.Key_Left,
                         QtCore.Qt.Key_F : QtCore.Qt.Key_Right,
                         QtCore.Qt.Key_A : QtCore.Qt.Key_Home,
                         QtCore.Qt.Key_E : QtCore.Qt.Key_End,
                         QtCore.Qt.Key_P : QtCore.Qt.Key_Up,
                         QtCore.Qt.Key_N : QtCore.Qt.Key_Down,
                         QtCore.Qt.Key_D : QtCore.Qt.Key_Delete, }
    _shortcuts = set(_ctrl_down_remap.keys() +
                     [ QtCore.Qt.Key_C, QtCore.Qt.Key_V ])

    #---------------------------------------------------------------------------
    # 'QObject' interface
    #---------------------------------------------------------------------------

    def __init__(self, parent=None):
        QtGui.QPlainTextEdit.__init__(self, parent)

        # Initialize protected variables.
        self._ansi_processor = QtAnsiCodeProcessor()
        self._completion_widget = CompletionWidget(self)
        self._continuation_prompt = '> '
        self._executing = False
        self._prompt = ''
        self._prompt_pos = 0
        self._reading = False

        # Set a monospaced font.
        self.reset_font()

        # Define a custom context menu.
        self._context_menu = QtGui.QMenu(self)

        copy_action = QtGui.QAction('Copy', self)
        copy_action.triggered.connect(self.copy)
        self.copyAvailable.connect(copy_action.setEnabled)
        self._context_menu.addAction(copy_action)

        self._paste_action = QtGui.QAction('Paste', self)
        self._paste_action.triggered.connect(self.paste)
        self._context_menu.addAction(self._paste_action)
        self._context_menu.addSeparator()

        select_all_action = QtGui.QAction('Select All', self)
        select_all_action.triggered.connect(self.selectAll)
        self._context_menu.addAction(select_all_action)

    def event(self, event):
        """ Reimplemented to override shortcuts, if necessary.
        """
        # On Mac OS, it is always unnecessary to override shortcuts, hence the
        # check below. Users should just use the Control key instead of the
        # Command key.
        if self.override_shortcuts and \
                sys.platform != 'darwin' and \
                event.type() == QtCore.QEvent.ShortcutOverride and \
                self._control_down(event.modifiers()) and \
                event.key() in self._shortcuts:
            event.accept()
            return True
        else:
            return QtGui.QPlainTextEdit.event(self, event)

    #---------------------------------------------------------------------------
    # 'QWidget' interface
    #---------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """ Reimplemented to create a menu without destructive actions like
            'Cut' and 'Delete'.
        """
        clipboard_empty = QtGui.QApplication.clipboard().text().isEmpty()
        self._paste_action.setEnabled(not clipboard_empty)
        
        self._context_menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        """ Reimplemented to create a console-like interface.
        """
        intercepted = False
        cursor = self.textCursor()
        position = cursor.position()
        key = event.key()
        ctrl_down = self._control_down(event.modifiers())
        alt_down = event.modifiers() & QtCore.Qt.AltModifier
        shift_down = event.modifiers() & QtCore.Qt.ShiftModifier

        # Even though we have reimplemented 'paste', the C++ level slot is still
        # called by Qt. So we intercept the key press here.
        if event.matches(QtGui.QKeySequence.Paste):
            self.paste()
            intercepted = True

        elif ctrl_down:
            if key in self._ctrl_down_remap:
                ctrl_down = False
                key = self._ctrl_down_remap[key]
                event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, key, 
                                        QtCore.Qt.NoModifier)

            elif key == QtCore.Qt.Key_K:
                if self._in_buffer(position):
                    cursor.movePosition(QtGui.QTextCursor.EndOfLine,
                                        QtGui.QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                intercepted = True

            elif key == QtCore.Qt.Key_X:
                intercepted = True

            elif key == QtCore.Qt.Key_Y:
                self.paste()
                intercepted = True

        elif alt_down:
            if key == QtCore.Qt.Key_B:
                self.setTextCursor(self._get_word_start_cursor(position))
                intercepted = True
                
            elif key == QtCore.Qt.Key_F:
                self.setTextCursor(self._get_word_end_cursor(position))
                intercepted = True

            elif key == QtCore.Qt.Key_Backspace:
                cursor = self._get_word_start_cursor(position)
                cursor.setPosition(position, QtGui.QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                intercepted = True

            elif key == QtCore.Qt.Key_D:
                cursor = self._get_word_end_cursor(position)
                cursor.setPosition(position, QtGui.QTextCursor.KeepAnchor)
                cursor.removeSelectedText()
                intercepted = True

        if self._completion_widget.isVisible():
            self._completion_widget.keyPressEvent(event)
            intercepted = event.isAccepted()
        
        else:
            if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                intercepted = True
                if self._reading:
                    intercepted = False
                    self._reading = False
                elif not self._executing:
                    self.execute(interactive=True)

            elif key == QtCore.Qt.Key_Up:
                if self._reading or not self._up_pressed():
                    intercepted = True
                else:
                    prompt_line = self._get_prompt_cursor().blockNumber()
                    intercepted = cursor.blockNumber() <= prompt_line

            elif key == QtCore.Qt.Key_Down:
                if self._reading or not self._down_pressed():
                    intercepted = True
                else:
                    end_line = self._get_end_cursor().blockNumber()
                    intercepted = cursor.blockNumber() == end_line

            elif key == QtCore.Qt.Key_Tab:
                if self._reading:
                    intercepted = False
                else:
                    intercepted = not self._tab_pressed()

            elif key == QtCore.Qt.Key_Left:
                intercepted = not self._in_buffer(position - 1)

            elif key == QtCore.Qt.Key_Home:
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                start_pos = cursor.position()
                start_line = cursor.blockNumber()
                if start_line == self._get_prompt_cursor().blockNumber():
                    start_pos += len(self._prompt)
                else:
                    start_pos += len(self._continuation_prompt)
                if shift_down and self._in_buffer(position):
                    self._set_selection(position, start_pos)
                else:
                    self._set_position(start_pos)
                intercepted = True

            elif key == QtCore.Qt.Key_Backspace and not alt_down:

                # Line deletion (remove continuation prompt)
                len_prompt = len(self._continuation_prompt)
                if cursor.columnNumber() == len_prompt and \
                        position != self._prompt_pos:
                    cursor.setPosition(position - len_prompt, 
                                       QtGui.QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()

                # Regular backwards deletion
                else:
                    anchor = cursor.anchor()
                    if anchor == position:
                        intercepted = not self._in_buffer(position - 1)
                    else:
                        intercepted = not self._in_buffer(min(anchor, position))

            elif key == QtCore.Qt.Key_Delete:
                anchor = cursor.anchor()
                intercepted = not self._in_buffer(min(anchor, position))

        # Don't move cursor if control is down to allow copy-paste using
        # the keyboard in any part of the buffer.
        if not ctrl_down:
            self._keep_cursor_in_buffer()

        if not intercepted:
            QtGui.QPlainTextEdit.keyPressEvent(self, event)

    #--------------------------------------------------------------------------
    # 'QPlainTextEdit' interface
    #--------------------------------------------------------------------------

    def appendPlainText(self, text):
        """ Reimplemented to not append text as a new paragraph, which doesn't
            make sense for a console widget. Also, if enabled, handle ANSI
            codes.
        """
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        if self.ansi_codes:
            format = QtGui.QTextCharFormat()
            previous_end = 0
            for match in self._ansi_pattern.finditer(text):
                cursor.insertText(text[previous_end:match.start()], format)
                previous_end = match.end()
                for code in match.group(1).split(';'):
                    self._ansi_processor.set_code(int(code))
                format = self._ansi_processor.get_format()
            cursor.insertText(text[previous_end:], format)
        else:
            cursor.insertText(text)

    def clear(self, keep_input=False):
        """ Reimplemented to write a new prompt. If 'keep_input' is set,
            restores the old input buffer when the new prompt is written.
        """
        super(ConsoleWidget, self).clear()

        if keep_input:
            input_buffer = self.input_buffer
        self._show_prompt()
        if keep_input:
            self.input_buffer = input_buffer

    def paste(self):
        """ Reimplemented to ensure that text is pasted in the editing region.
        """
        self._keep_cursor_in_buffer()
        QtGui.QPlainTextEdit.paste(self)

    def print_(self, printer):
        """ Reimplemented to work around a bug in PyQt: the C++ level 'print_'
            slot has the wrong signature.
        """
        QtGui.QPlainTextEdit.print_(self, printer)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def execute(self, source=None, hidden=False, interactive=False):
        """ Executes source or the input buffer, possibly prompting for more
        input.

        Parameters:
        -----------     
        source : str, optional

            The source to execute. If not specified, the input buffer will be
            used. If specified and 'hidden' is False, the input buffer will be
            replaced with the source before execution.

        hidden : bool, optional (default False)

            If set, no output will be shown and the prompt will not be modified.
            In other words, it will be completely invisible to the user that
            an execution has occurred.

        interactive : bool, optional (default False)

            Whether the console is to treat the source as having been manually
            entered by the user. The effect of this parameter depends on the
            subclass implementation.

        Raises:
        -------
        RuntimeError
            If incomplete input is given and 'hidden' is True. In this case,
            it not possible to prompt for more input.

        Returns:
        --------
        A boolean indicating whether the source was executed.
        """
        if not hidden:
            if source is not None:
                self.input_buffer = source

            self.appendPlainText('\n')
            self._executing_input_buffer = self.input_buffer
            self._executing = True
            self._prompt_finished()

        real_source = self.input_buffer if source is None else source
        complete = self._is_complete(real_source, interactive)
        if complete:
            if not hidden:
                # The maximum block count is only in effect during execution.
                # This ensures that _prompt_pos does not become invalid due to
                # text truncation.
                self.setMaximumBlockCount(self.buffer_size)
            self._execute(real_source, hidden)
        elif hidden:
            raise RuntimeError('Incomplete noninteractive input: "%s"' % source)
        else:
            self._show_continuation_prompt()

        return complete

    def _get_input_buffer(self):
        """ The text that the user has entered entered at the current prompt.
        """
        # If we're executing, the input buffer may not even exist anymore due to
        # the limit imposed by 'buffer_size'. Therefore, we store it.
        if self._executing:
            return self._executing_input_buffer

        cursor = self._get_end_cursor()
        cursor.setPosition(self._prompt_pos, QtGui.QTextCursor.KeepAnchor)

        # Use QTextDocumentFragment intermediate object because it strips
        # out the Unicode line break characters that Qt insists on inserting.
        input_buffer = str(cursor.selection().toPlainText())

        # Strip out continuation prompts.
        return input_buffer.replace('\n' + self._continuation_prompt, '\n')

    def _set_input_buffer(self, string):
        """ Replaces the text in the input buffer with 'string'.
        """
        # Add continuation prompts where necessary.
        lines = string.splitlines()
        for i in xrange(1, len(lines)):
            lines[i] = self._continuation_prompt + lines[i]
        string = '\n'.join(lines)

        # Replace buffer with new text.
        cursor = self._get_end_cursor()
        cursor.setPosition(self._prompt_pos, QtGui.QTextCursor.KeepAnchor)
        cursor.insertText(string)
        self.moveCursor(QtGui.QTextCursor.End)

    input_buffer = property(_get_input_buffer, _set_input_buffer)

    def _get_input_buffer_cursor_line(self):
        """ The text in the line of the input buffer in which the user's cursor
            rests. Returns a string if there is such a line; otherwise, None.
        """
        if self._executing:
            return None
        cursor = self.textCursor()
        if cursor.position() >= self._prompt_pos:
            text = str(cursor.block().text())
            if cursor.blockNumber() == self._get_prompt_cursor().blockNumber():
                return text[len(self._prompt):]
            else:
                return text[len(self._continuation_prompt):]
        else:
            return None

    input_buffer_cursor_line = property(_get_input_buffer_cursor_line)

    def _get_font(self):
        """ The base font being used by the ConsoleWidget.
        """
        return self.document().defaultFont()

    def _set_font(self, font):
        """ Sets the base font for the ConsoleWidget to the specified QFont.
        """
        self._completion_widget.setFont(font)
        self.document().setDefaultFont(font)

    font = property(_get_font, _set_font)

    def reset_font(self):
        """ Sets the font to the default fixed-width font for this platform.
        """
        if sys.platform == 'win32':
            name = 'Courier'
        elif sys.platform == 'darwin':
            name = 'Monaco'
        else:
            name = 'Monospace'
        font = QtGui.QFont(name, QtGui.qApp.font().pointSize())
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self._set_font(font)
        
    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _is_complete(self, source, interactive):
        """ Returns whether 'source' can be executed. When triggered by an
            Enter/Return key press, 'interactive' is True; otherwise, it is
            False.
        """
        raise NotImplementedError

    def _execute(self, source, hidden):
        """ Execute 'source'. If 'hidden', do not show any output.
        """
        raise NotImplementedError

    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        """
        pass

    def _prompt_finished_hook(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        pass

    def _up_pressed(self):
        """ Called when the up key is pressed. Returns whether to continue
            processing the event.
        """
        return True

    def _down_pressed(self):
        """ Called when the down key is pressed. Returns whether to continue
            processing the event.
        """
        return True

    def _tab_pressed(self):
        """ Called when the tab key is pressed. Returns whether to continue
            processing the event.
        """
        return False

    #--------------------------------------------------------------------------
    # 'ConsoleWidget' protected interface
    #--------------------------------------------------------------------------

    def _control_down(self, modifiers):
        """ Given a KeyboardModifiers flags object, return whether the Control
            key is down (on Mac OS, treat the Command key as a synonym for
            Control).
        """
        down = bool(modifiers & QtCore.Qt.ControlModifier)

        # Note: on Mac OS, ControlModifier corresponds to the Command key while
        # MetaModifier corresponds to the Control key.
        if sys.platform == 'darwin':
            down = down ^ bool(modifiers & QtCore.Qt.MetaModifier)
            
        return down
    
    def _complete_with_items(self, cursor, items):
        """ Performs completion with 'items' at the specified cursor location.
        """
        if len(items) == 1:
            cursor.setPosition(self.textCursor().position(), 
                               QtGui.QTextCursor.KeepAnchor)
            cursor.insertText(items[0])
        elif len(items) > 1:
            if self.gui_completion:
                self._completion_widget.show_items(cursor, items) 
            else:
                text = '\n'.join(items) + '\n'
                self._write_text_keeping_prompt(text)
                
    def _get_end_cursor(self):
        """ Convenience method that returns a cursor for the last character.
        """
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        return cursor

    def _get_prompt_cursor(self):
        """ Convenience method that returns a cursor for the prompt position.
        """
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_pos)
        return cursor

    def _get_selection_cursor(self, start, end):
        """ Convenience method that returns a cursor with text selected between
            the positions 'start' and 'end'.
        """
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
        return cursor

    def _get_word_start_cursor(self, position):
        """ Find the start of the word to the left the given position. If a
            sequence of non-word characters precedes the first word, skip over
            them. (This emulates the behavior of bash, emacs, etc.)
        """
        document = self.document()
        position -= 1
        while self._in_buffer(position) and \
                not document.characterAt(position).isLetterOrNumber():
            position -= 1
        while self._in_buffer(position) and \
                document.characterAt(position).isLetterOrNumber():
            position -= 1
        cursor = self.textCursor()
        cursor.setPosition(position + 1)
        return cursor

    def _get_word_end_cursor(self, position):
        """ Find the end of the word to the right the given position. If a
            sequence of non-word characters precedes the first word, skip over
            them. (This emulates the behavior of bash, emacs, etc.)
        """
        document = self.document()
        end = self._get_end_cursor().position()
        while position < end and \
                not document.characterAt(position).isLetterOrNumber():
            position += 1
        while position < end and \
                document.characterAt(position).isLetterOrNumber():
            position += 1
        cursor = self.textCursor()
        cursor.setPosition(position)
        return cursor

    def _prompt_started(self):
        """ Called immediately after a new prompt is displayed.
        """
        # Temporarily disable the maximum block count to permit undo/redo and 
        # to ensure that the prompt position does not change due to truncation.
        self.setMaximumBlockCount(0)
        self.setUndoRedoEnabled(True)

        self.setReadOnly(False)
        self.moveCursor(QtGui.QTextCursor.End)
        self.centerCursor()

        self._executing = False
        self._prompt_started_hook()

    def _prompt_finished(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        self.setUndoRedoEnabled(False)
        self.setReadOnly(True)
        self._prompt_finished_hook()

    def _readline(self, prompt=''):
        """ Read and return one line of input from the user. The trailing 
            newline is stripped.
        """
        if not self.isVisible():
            raise RuntimeError('Cannot read a line if widget is not visible!')

        self._reading = True
        self._show_prompt(prompt)
        while self._reading:
            QtCore.QCoreApplication.processEvents()
        return self.input_buffer.rstrip('\n\r')

    def _set_position(self, position):
        """ Convenience method to set the position of the cursor.
        """
        cursor = self.textCursor()
        cursor.setPosition(position)
        self.setTextCursor(cursor)

    def _set_selection(self, start, end):
        """ Convenience method to set the current selected text.
        """
        self.setTextCursor(self._get_selection_cursor(start, end))

    def _show_prompt(self, prompt=None):
        """ Writes a new prompt at the end of the buffer. If 'prompt' is not
            specified, the previous prompt is used.
        """
        # Use QTextDocumentFragment intermediate object because it strips
        # out the Unicode line break characters that Qt insists on inserting.
        cursor = self._get_end_cursor()
        cursor.movePosition(QtGui.QTextCursor.Left, 
                            QtGui.QTextCursor.KeepAnchor)
        if str(cursor.selection().toPlainText()) not in '\r\n':
            self.appendPlainText('\n')

        if prompt is not None:
            self._prompt = prompt
        self.appendPlainText(self._prompt)

        self._prompt_pos = self._get_end_cursor().position()
        self._prompt_started()

    def _show_continuation_prompt(self):
        """ Writes a new continuation prompt at the end of the buffer.
        """
        self.appendPlainText(self._continuation_prompt)
        self._prompt_started()

    def _write_text_keeping_prompt(self, text):
        """ Writes 'text' after the current prompt, then restores the old prompt
            with its old input buffer.
        """
        input_buffer = self.input_buffer
        self.appendPlainText('\n')
        self._prompt_finished()

        self.appendPlainText(text)
        self._show_prompt()
        self.input_buffer = input_buffer

    def _in_buffer(self, position):
        """ Returns whether the given position is inside the editing region.
        """
        return position >= self._prompt_pos

    def _keep_cursor_in_buffer(self):
        """ Ensures that the cursor is inside the editing region. Returns
            whether the cursor was moved.
        """
        cursor = self.textCursor()
        if cursor.position() < self._prompt_pos:
            cursor.movePosition(QtGui.QTextCursor.End)
            self.setTextCursor(cursor)
            return True
        else:
            return False


class HistoryConsoleWidget(ConsoleWidget):
    """ A ConsoleWidget that keeps a history of the commands that have been
        executed.
    """
    
    #---------------------------------------------------------------------------
    # 'QObject' interface
    #---------------------------------------------------------------------------

    def __init__(self, parent=None):
        super(HistoryConsoleWidget, self).__init__(parent)

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
            self._history.append(history.rstrip())
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
        if self.textCursor().blockNumber() == prompt_cursor.blockNumber():
            self.history_previous()

            # Go to the first line of prompt for seemless history scrolling.
            cursor = self._get_prompt_cursor()
            cursor.movePosition(QtGui.QTextCursor.EndOfLine)
            self.setTextCursor(cursor)

            return False
        return True

    def _down_pressed(self):
        """ Called when the down key is pressed. Returns whether to continue
            processing the event.
        """
        end_cursor = self._get_end_cursor()
        if self.textCursor().blockNumber() == end_cursor.blockNumber():
            self.history_next()
            return False
        return True

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' interface
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

# Standard library imports
import sys
from textwrap import dedent

# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from ansi_code_processor import QtAnsiCodeProcessor
from completion_widget import CompletionWidget


class ConsoleWidget(QtGui.QWidget):
    """ An abstract base class for console-type widgets. This class has 
        functionality for:

            * Maintaining a prompt and editing region
            * Providing the traditional Unix-style console keyboard shortcuts 
            * Performing tab completion
            * Paging text
            * Handling ANSI escape codes

        ConsoleWidget also provides a number of utility methods that will be
        convenient to implementors of a console-style widget.
    """

    # Whether to process ANSI escape codes.
    ansi_codes = True

    # The maximum number of lines of text before truncation.
    buffer_size = 500

    # Whether to use a list widget or plain text output for tab completion.
    gui_completion = True

    # Whether to override ShortcutEvents for the keybindings defined by this
    # widget (Ctrl+n, Ctrl+a, etc). Enable this if you want this widget to take
    # priority (when it has focus) over, e.g., window-level menu shortcuts.
    override_shortcuts = False

    # Signals that indicate ConsoleWidget state.
    copy_available = QtCore.pyqtSignal(bool)
    redo_available = QtCore.pyqtSignal(bool)
    undo_available = QtCore.pyqtSignal(bool)

    # Signal emitted when paging is needed and the paging style has been
    # specified as 'custom'.
    custom_page_requested = QtCore.pyqtSignal(QtCore.QString)

    # Protected class variables.
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

    def __init__(self, kind='plain', paging='inside', parent=None):
        """ Create a ConsoleWidget.
        
        Parameters
        ----------
        kind : str, optional [default 'plain']            
            The type of underlying text widget to use. Valid values are 'plain',
            which specifies a QPlainTextEdit, and 'rich', which specifies a
            QTextEdit.

        paging : str, optional [default 'inside']
            The type of paging to use. Valid values are:
                'inside' : The widget pages like a traditional terminal pager.
                'hsplit' : When paging is requested, the widget is split 
                           horizontally. The top pane contains the console,
                           and the bottom pane contains the paged text.
                'vsplit' : Similar to 'hsplit', except that a vertical splitter
                           used.
                'custom' : No action is taken by the widget beyond emitting a
                           'custom_page_requested(QString)' signal.
                'none'   : The text is written directly to the console.

        parent : QWidget, optional [default None]
            The parent for this widget.
        """
        super(ConsoleWidget, self).__init__(parent)

        # Create the layout and underlying text widget.
        layout = QtGui.QStackedLayout(self)
        layout.setMargin(0)
        self._control = self._create_control(kind)
        self._page_control = None
        self._splitter = None
        if paging in ('hsplit', 'vsplit'):
            self._splitter = QtGui.QSplitter()
            if paging == 'hsplit':
                self._splitter.setOrientation(QtCore.Qt.Horizontal)
            else:
                self._splitter.setOrientation(QtCore.Qt.Vertical)
            self._splitter.addWidget(self._control)
            layout.addWidget(self._splitter)
        else:
            layout.addWidget(self._control)

        # Create the paging widget, if necessary.
        self._page_style = paging
        if paging in ('inside', 'hsplit', 'vsplit'):
            self._page_control = self._create_page_control()
            if self._splitter:
                self._page_control.hide()
                self._splitter.addWidget(self._page_control)
            else:
                layout.addWidget(self._page_control)
        elif paging not in ('custom', 'none'):
            raise ValueError('Paging style %s unknown.' % repr(paging))

        # Initialize protected variables. Some variables contain useful state
        # information for subclasses; they should be considered read-only.
        self._ansi_processor = QtAnsiCodeProcessor()
        self._completion_widget = CompletionWidget(self._control)
        self._continuation_prompt = '> '
        self._continuation_prompt_html = None
        self._executing = False
        self._prompt = ''
        self._prompt_html = None
        self._prompt_pos = 0
        self._reading = False
        self._reading_callback = None
        self._tab_width = 8

        # Set a monospaced font.
        self.reset_font()

    def eventFilter(self, obj, event):
        """ Reimplemented to ensure a console-like behavior in the underlying
            text widget.
        """
        # Re-map keys for all filtered widgets.
        etype = event.type()
        if etype == QtCore.QEvent.KeyPress and \
                self._control_key_down(event.modifiers()) and \
                event.key() in self._ctrl_down_remap:
            new_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, 
                                        self._ctrl_down_remap[event.key()],
                                        QtCore.Qt.NoModifier)
            QtGui.qApp.sendEvent(obj, new_event)
            return True

        # Override shortucts for all filtered widgets. Note that on Mac OS it is
        # always unnecessary to override shortcuts, hence the check below (users
        # should just use the Control key instead of the Command key).
        elif etype == QtCore.QEvent.ShortcutOverride and \
                sys.platform != 'darwin' and \
                self._control_key_down(event.modifiers()) and \
                event.key() in self._shortcuts:
            event.accept()
            return False

        elif obj == self._control:
            # Disable moving text by drag and drop.
            if etype == QtCore.QEvent.DragMove:
                return True

            elif etype == QtCore.QEvent.KeyPress:
                return self._event_filter_console_keypress(event)

        elif obj == self._page_control:
            if etype == QtCore.QEvent.KeyPress:
                return self._event_filter_page_keypress(event)

        return super(ConsoleWidget, self).eventFilter(obj, event)

    #---------------------------------------------------------------------------
    # 'QWidget' interface
    #---------------------------------------------------------------------------

    def sizeHint(self):
        """ Reimplemented to suggest a size that is 80 characters wide and
            25 lines high.
        """
        style = self.style()
        opt = QtGui.QStyleOptionHeader()
        font_metrics = QtGui.QFontMetrics(self.font)
        splitwidth = style.pixelMetric(QtGui.QStyle.PM_SplitterWidth, opt, self)

        width = font_metrics.width(' ') * 80
        width += style.pixelMetric(QtGui.QStyle.PM_ScrollBarExtent, opt, self)
        if self._page_style == 'hsplit':
            width = width * 2 + splitwidth

        height = font_metrics.height() * 25
        if self._page_style == 'vsplit':
            height = height * 2 + splitwidth

        return QtCore.QSize(width, height)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def can_paste(self):
        """ Returns whether text can be pasted from the clipboard.
        """
        # Accept only text that can be ASCII encoded.
        if self._control.textInteractionFlags() & QtCore.Qt.TextEditable:
            text = QtGui.QApplication.clipboard().text()
            if not text.isEmpty():
                try:
                    str(text)
                    return True
                except UnicodeEncodeError:
                    pass
        return False

    def clear(self, keep_input=False):
        """ Clear the console, then write a new prompt. If 'keep_input' is set,
            restores the old input buffer when the new prompt is written.
        """
        self._control.clear()
        if keep_input:
            input_buffer = self.input_buffer
        self._show_prompt()
        if keep_input:
            self.input_buffer = input_buffer

    def copy(self):
        """ Copy the current selected text to the clipboard.
        """
        self._control.copy()

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
            it is not possible to prompt for more input.

        Returns:
        --------
        A boolean indicating whether the source was executed.
        """
        if not hidden:
            if source is not None:
                self.input_buffer = source

            self._append_plain_text('\n')
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
                self._control.document().setMaximumBlockCount(self.buffer_size)
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
        input_buffer = str(cursor.selection().toPlainText())

        # Strip out continuation prompts.
        return input_buffer.replace('\n' + self._continuation_prompt, '\n')

    def _set_input_buffer(self, string):
        """ Replaces the text in the input buffer with 'string'.
        """
        # For now, it is an error to modify the input buffer during execution.
        if self._executing:
            raise RuntimeError("Cannot change input buffer during execution.")

        # Remove old text.
        cursor = self._get_end_cursor()
        cursor.beginEditBlock()
        cursor.setPosition(self._prompt_pos, QtGui.QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

        # Insert new text with continuation prompts.
        lines = string.splitlines(True)
        if lines:
            self._append_plain_text(lines[0])
            for i in xrange(1, len(lines)):
                if self._continuation_prompt_html is None:
                    self._append_plain_text(self._continuation_prompt)
                else:
                    self._append_html(self._continuation_prompt_html)
                self._append_plain_text(lines[i])
        cursor.endEditBlock()
        self._control.moveCursor(QtGui.QTextCursor.End)

    input_buffer = property(_get_input_buffer, _set_input_buffer)

    def _get_font(self):
        """ The base font being used by the ConsoleWidget.
        """
        return self._control.document().defaultFont()

    def _set_font(self, font):
        """ Sets the base font for the ConsoleWidget to the specified QFont.
        """
        font_metrics = QtGui.QFontMetrics(font)
        self._control.setTabStopWidth(self.tab_width * font_metrics.width(' '))

        self._completion_widget.setFont(font)
        self._control.document().setDefaultFont(font)

    font = property(_get_font, _set_font)

    def paste(self):
        """ Paste the contents of the clipboard into the input region.
        """
        if self._control.textInteractionFlags() & QtCore.Qt.TextEditable:
            try:
                text = str(QtGui.QApplication.clipboard().text())
            except UnicodeEncodeError:
                pass
            else:
                self._insert_into_buffer(dedent(text))

    def print_(self, printer):
        """ Print the contents of the ConsoleWidget to the specified QPrinter.
        """
        self._control.print_(printer)

    def redo(self):
        """ Redo the last operation. If there is no operation to redo, nothing
            happens.
        """
        self._control.redo()

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

    def select_all(self):
        """ Selects all the text in the buffer.
        """
        self._control.selectAll()

    def _get_tab_width(self):
        """ The width (in terms of space characters) for tab characters.
        """
        return self._tab_width

    def _set_tab_width(self, tab_width):
        """ Sets the width (in terms of space characters) for tab characters.
        """
        font_metrics = QtGui.QFontMetrics(self.font)
        self._control.setTabStopWidth(tab_width * font_metrics.width(' '))

        self._tab_width = tab_width

    tab_width = property(_get_tab_width, _set_tab_width)

    def undo(self):
        """ Undo the last operation. If there is no operation to undo, nothing
            happens.
        """
        self._control.undo()

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

    def _execute_interrupt(self):
        """ Attempts to stop execution. Returns whether this method has an
            implementation.
        """
        return False

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

    def _append_html(self, html):
        """ Appends html at the end of the console buffer.
        """
        cursor = self._get_end_cursor()
        self._insert_html(cursor, html)

    def _append_html_fetching_plain_text(self, html):
        """ Appends 'html', then returns the plain text version of it.
        """
        anchor = self._get_end_cursor().position()
        self._append_html(html)
        cursor = self._get_end_cursor()
        cursor.setPosition(anchor, QtGui.QTextCursor.KeepAnchor)
        return str(cursor.selection().toPlainText())

    def _append_plain_text(self, text):
        """ Appends plain text at the end of the console buffer, processing
            ANSI codes if enabled.
        """
        cursor = self._get_end_cursor()
        self._insert_plain_text(cursor, text)

    def _append_plain_text_keeping_prompt(self, text):
        """ Writes 'text' after the current prompt, then restores the old prompt
            with its old input buffer.
        """
        input_buffer = self.input_buffer
        self._append_plain_text('\n')
        self._prompt_finished()

        self._append_plain_text(text)
        self._show_prompt()
        self.input_buffer = input_buffer

    def _complete_with_items(self, cursor, items):
        """ Performs completion with 'items' at the specified cursor location.
        """
        if len(items) == 1:
            cursor.setPosition(self._control.textCursor().position(), 
                               QtGui.QTextCursor.KeepAnchor)
            cursor.insertText(items[0])
        elif len(items) > 1:
            if self.gui_completion:
                self._completion_widget.show_items(cursor, items) 
            else:
                text = self._format_as_columns(items)
                self._append_plain_text_keeping_prompt(text)

    def _control_key_down(self, modifiers):
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

    def _create_control(self, kind):
        """ Creates and connects the underlying text widget.
        """
        if kind == 'plain':
            control = QtGui.QPlainTextEdit()
        elif kind == 'rich':
            control = QtGui.QTextEdit()
            control.setAcceptRichText(False)
        else:
            raise ValueError("Kind %s unknown." % repr(kind))
        control.installEventFilter(self)
        control.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        control.customContextMenuRequested.connect(self._show_context_menu)
        control.copyAvailable.connect(self.copy_available)
        control.redoAvailable.connect(self.redo_available)
        control.undoAvailable.connect(self.undo_available)
        control.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        return control

    def _create_page_control(self):
        """ Creates and connects the underlying paging widget.
        """
        control = QtGui.QPlainTextEdit()
        control.installEventFilter(self)
        control.setReadOnly(True)
        control.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        return control

    def _event_filter_console_keypress(self, event):
        """ Filter key events for the underlying text widget to create a
            console-like interface.
        """
        intercepted = False
        cursor = self._control.textCursor()
        position = cursor.position()
        key = event.key()
        ctrl_down = self._control_key_down(event.modifiers())
        alt_down = event.modifiers() & QtCore.Qt.AltModifier
        shift_down = event.modifiers() & QtCore.Qt.ShiftModifier

        if event.matches(QtGui.QKeySequence.Paste):
            # Call our paste instead of the underlying text widget's.
            self.paste()
            intercepted = True

        elif ctrl_down:
            if key == QtCore.Qt.Key_C:
                intercepted = self._executing and self._execute_interrupt()

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
                self._set_cursor(self._get_word_start_cursor(position))
                intercepted = True
                
            elif key == QtCore.Qt.Key_F:
                self._set_cursor(self._get_word_end_cursor(position))
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

        else:
            if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                if self._reading:
                    self._append_plain_text('\n')
                    self._reading = False
                    if self._reading_callback:
                        self._reading_callback()
                elif not self._executing:
                    self.execute(interactive=True)
                intercepted = True

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
                cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
                start_line = cursor.blockNumber()
                if start_line == self._get_prompt_cursor().blockNumber():
                    start_pos = self._prompt_pos
                else:
                    start_pos = cursor.position()
                    start_pos += len(self._continuation_prompt)
                if shift_down and self._in_buffer(position):
                    self._set_selection(position, start_pos)
                else:
                    self._set_position(start_pos)
                intercepted = True

            elif key == QtCore.Qt.Key_Backspace:

                # Line deletion (remove continuation prompt)
                len_prompt = len(self._continuation_prompt)
                if not self._reading and \
                        cursor.columnNumber() == len_prompt and \
                        position != self._prompt_pos:
                    cursor.movePosition(QtGui.QTextCursor.StartOfBlock,
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

        # Don't move the cursor if control is down to allow copy-paste using
        # the keyboard in any part of the buffer.
        if not ctrl_down:
            self._keep_cursor_in_buffer()

        return intercepted

    def _event_filter_page_keypress(self, event):
        """ Filter key events for the paging widget to create console-like 
            interface.
        """
        key = event.key()

        if key in (QtCore.Qt.Key_Q, QtCore.Qt.Key_Escape):
            if self._splitter:
                self._page_control.hide()
            else:
                self.layout().setCurrentWidget(self._control)
            return True

        elif key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            new_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, 
                                        QtCore.Qt.Key_Down, 
                                        QtCore.Qt.NoModifier)
            QtGui.qApp.sendEvent(self._page_control, new_event)
            return True

        return False

    def _format_as_columns(self, items, separator='  '):
        """ Transform a list of strings into a single string with columns.

        Parameters
        ----------
        items : sequence of strings
            The strings to process.

        separator : str, optional [default is two spaces]
            The string that separates columns.

        Returns
        -------
        The formatted string.
        """
        # Note: this code is adapted from columnize 0.3.2.
        # See http://code.google.com/p/pycolumnize/

        width = self._control.viewport().width()
        char_width = QtGui.QFontMetrics(self.font).width(' ')
        displaywidth = max(5, width / char_width)

        # Some degenerate cases.
        size = len(items)
        if size == 0: 
            return '\n'
        elif size == 1:
            return '%s\n' % str(items[0])

        # Try every row count from 1 upwards
        array_index = lambda nrows, row, col: nrows*col + row
        for nrows in range(1, size):
            ncols = (size + nrows - 1) // nrows
            colwidths = []
            totwidth = -len(separator)
            for col in range(ncols):
                # Get max column width for this column
                colwidth = 0
                for row in range(nrows):
                    i = array_index(nrows, row, col)
                    if i >= size: break
                    x = items[i]
                    colwidth = max(colwidth, len(x))
                colwidths.append(colwidth)
                totwidth += colwidth + len(separator)
                if totwidth > displaywidth: 
                    break
            if totwidth <= displaywidth: 
                break

        # The smallest number of rows computed and the max widths for each
        # column has been obtained. Now we just have to format each of the rows.
        string = ''
        for row in range(nrows):
            texts = []
            for col in range(ncols):
                i = row + nrows*col
                if i >= size:
                    texts.append('')
                else:
                    texts.append(items[i])
            while texts and not texts[-1]:
                del texts[-1]
            for col in range(len(texts)):
                texts[col] = texts[col].ljust(colwidths[col])
            string += '%s\n' % str(separator.join(texts))
        return string

    def _get_block_plain_text(self, block):
        """ Given a QTextBlock, return its unformatted text.
        """
        cursor = QtGui.QTextCursor(block)
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, 
                            QtGui.QTextCursor.KeepAnchor)
        return str(cursor.selection().toPlainText())

    def _get_cursor(self):
        """ Convenience method that returns a cursor for the current position.
        """
        return self._control.textCursor()
                
    def _get_end_cursor(self):
        """ Convenience method that returns a cursor for the last character.
        """
        cursor = self._control.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        return cursor

    def _get_input_buffer_cursor_line(self):
        """ The text in the line of the input buffer in which the user's cursor
            rests. Returns a string if there is such a line; otherwise, None.
        """
        if self._executing:
            return None
        cursor = self._control.textCursor()
        if cursor.position() >= self._prompt_pos:
            text = self._get_block_plain_text(cursor.block())
            if cursor.blockNumber() == self._get_prompt_cursor().blockNumber():
                return text[len(self._prompt):]
            else:
                return text[len(self._continuation_prompt):]
        else:
            return None

    def _get_prompt_cursor(self):
        """ Convenience method that returns a cursor for the prompt position.
        """
        cursor = self._control.textCursor()
        cursor.setPosition(self._prompt_pos)
        return cursor

    def _get_selection_cursor(self, start, end):
        """ Convenience method that returns a cursor with text selected between
            the positions 'start' and 'end'.
        """
        cursor = self._control.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
        return cursor

    def _get_word_start_cursor(self, position):
        """ Find the start of the word to the left the given position. If a
            sequence of non-word characters precedes the first word, skip over
            them. (This emulates the behavior of bash, emacs, etc.)
        """
        document = self._control.document()
        position -= 1
        while position >= self._prompt_pos and \
                not document.characterAt(position).isLetterOrNumber():
            position -= 1
        while position >= self._prompt_pos and \
                document.characterAt(position).isLetterOrNumber():
            position -= 1
        cursor = self._control.textCursor()
        cursor.setPosition(position + 1)
        return cursor

    def _get_word_end_cursor(self, position):
        """ Find the end of the word to the right the given position. If a
            sequence of non-word characters precedes the first word, skip over
            them. (This emulates the behavior of bash, emacs, etc.)
        """
        document = self._control.document()
        end = self._get_end_cursor().position()
        while position < end and \
                not document.characterAt(position).isLetterOrNumber():
            position += 1
        while position < end and \
                document.characterAt(position).isLetterOrNumber():
            position += 1
        cursor = self._control.textCursor()
        cursor.setPosition(position)
        return cursor

    def _insert_html(self, cursor, html):
        """ Insert HTML using the specified cursor in such a way that future
            formatting is unaffected.
        """
        cursor.beginEditBlock()
        cursor.insertHtml(html)

        # After inserting HTML, the text document "remembers" it's in "html
        # mode", which means that subsequent calls adding plain text will result
        # in unwanted formatting, lost tab characters, etc. The following code
        # hacks around this behavior, which I consider to be a bug in Qt.
        cursor.movePosition(QtGui.QTextCursor.Left, 
                            QtGui.QTextCursor.KeepAnchor)
        if cursor.selection().toPlainText() == ' ':
            cursor.removeSelectedText()
        cursor.movePosition(QtGui.QTextCursor.Right)
        cursor.insertText(' ', QtGui.QTextCharFormat())
        cursor.endEditBlock()

    def _insert_plain_text(self, cursor, text):
        """ Inserts plain text using the specified cursor, processing ANSI codes
            if enabled.
        """
        cursor.beginEditBlock()
        if self.ansi_codes:
            for substring in self._ansi_processor.split_string(text):
                format = self._ansi_processor.get_format()
                cursor.insertText(substring, format)
        else:
            cursor.insertText(text)
        cursor.endEditBlock()

    def _insert_into_buffer(self, text):
        """ Inserts text into the input buffer at the current cursor position,
            ensuring that continuation prompts are inserted as necessary.
        """
        lines = str(text).splitlines(True)
        if lines:
            self._keep_cursor_in_buffer()
            cursor = self._control.textCursor()
            cursor.beginEditBlock()
            cursor.insertText(lines[0])
            for line in lines[1:]:
                if self._continuation_prompt_html is None:
                    cursor.insertText(self._continuation_prompt)
                else:
                    self._insert_html(cursor, self._continuation_prompt_html)
                cursor.insertText(line)
            cursor.endEditBlock()
            self._control.setTextCursor(cursor)

    def _in_buffer(self, position):
        """ Returns whether the given position is inside the editing region.
        """
        cursor = self._control.textCursor()
        cursor.setPosition(position)
        line = cursor.blockNumber()
        prompt_line = self._get_prompt_cursor().blockNumber()
        if line == prompt_line:
            return position >= self._prompt_pos
        elif line > prompt_line:
            cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
            prompt_pos = cursor.position() + len(self._continuation_prompt)
            return position >= prompt_pos
        return False

    def _keep_cursor_in_buffer(self):
        """ Ensures that the cursor is inside the editing region. Returns
            whether the cursor was moved.
        """
        cursor = self._control.textCursor()
        if self._in_buffer(cursor.position()):
            return False
        else:
            cursor.movePosition(QtGui.QTextCursor.End)
            self._control.setTextCursor(cursor)
            return True
        
    def _page(self, text):
        """ Displays text using the pager.
        """
        if self._page_style == 'custom':
            self.custom_page_requested.emit(text)
        elif self._page_style == 'none':
            self._append_plain_text(text)
        else:
            self._page_control.clear()
            cursor = self._page_control.textCursor()
            self._insert_plain_text(cursor, text)
            self._page_control.moveCursor(QtGui.QTextCursor.Start)

            self._page_control.viewport().resize(self._control.size())
            if self._splitter:
                self._page_control.show()
                self._page_control.setFocus()
            else:
                self.layout().setCurrentWidget(self._page_control)

    def _prompt_started(self):
        """ Called immediately after a new prompt is displayed.
        """
        # Temporarily disable the maximum block count to permit undo/redo and 
        # to ensure that the prompt position does not change due to truncation.
        self._control.document().setMaximumBlockCount(0)
        self._control.setUndoRedoEnabled(True)

        self._control.setReadOnly(False)
        self._control.moveCursor(QtGui.QTextCursor.End)

        self._executing = False
        self._prompt_started_hook()

    def _prompt_finished(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        self._control.setUndoRedoEnabled(False)
        self._control.setReadOnly(True)
        self._prompt_finished_hook()

    def _readline(self, prompt='', callback=None):
        """ Reads one line of input from the user. 

        Parameters
        ----------
        prompt : str, optional
            The prompt to print before reading the line.

        callback : callable, optional
            A callback to execute with the read line. If not specified, input is
            read *synchronously* and this method does not return until it has
            been read.

        Returns
        -------
        If a callback is specified, returns nothing. Otherwise, returns the
        input string with the trailing newline stripped.
        """
        if self._reading:
            raise RuntimeError('Cannot read a line. Widget is already reading.')

        if not callback and not self.isVisible():
            # If the user cannot see the widget, this function cannot return.
            raise RuntimeError('Cannot synchronously read a line if the widget'
                               'is not visible!')

        self._reading = True
        self._show_prompt(prompt, newline=False)

        if callback is None:
            self._reading_callback = None
            while self._reading:
                QtCore.QCoreApplication.processEvents()
            return self.input_buffer.rstrip('\n')

        else:
            self._reading_callback = lambda: \
                callback(self.input_buffer.rstrip('\n'))

    def _reset(self):
        """ Clears the console and resets internal state variables.
        """
        self._control.clear()
        self._executing = self._reading = False

    def _set_continuation_prompt(self, prompt, html=False):
        """ Sets the continuation prompt.

        Parameters
        ----------
        prompt : str
            The prompt to show when more input is needed.

        html : bool, optional (default False)
            If set, the prompt will be inserted as formatted HTML. Otherwise,
            the prompt will be treated as plain text, though ANSI color codes
            will be handled.
        """
        if html:
            self._continuation_prompt_html = prompt
        else:
            self._continuation_prompt = prompt
            self._continuation_prompt_html = None
            
    def _set_cursor(self, cursor):
        """ Convenience method to set the current cursor.
        """
        self._control.setTextCursor(cursor)

    def _set_position(self, position):
        """ Convenience method to set the position of the cursor.
        """
        cursor = self._control.textCursor()
        cursor.setPosition(position)
        self._control.setTextCursor(cursor)

    def _set_selection(self, start, end):
        """ Convenience method to set the current selected text.
        """
        self._control.setTextCursor(self._get_selection_cursor(start, end))

    def _show_context_menu(self, pos):
        """ Shows a context menu at the given QPoint (in widget coordinates).
        """
        menu = QtGui.QMenu()

        copy_action = menu.addAction('Copy', self.copy)
        copy_action.setEnabled(self._get_cursor().hasSelection())
        copy_action.setShortcut(QtGui.QKeySequence.Copy)

        paste_action = menu.addAction('Paste', self.paste)
        paste_action.setEnabled(self.can_paste())
        paste_action.setShortcut(QtGui.QKeySequence.Paste)

        menu.addSeparator()
        menu.addAction('Select All', self.select_all)

        menu.exec_(self._control.mapToGlobal(pos))

    def _show_prompt(self, prompt=None, html=False, newline=True):
        """ Writes a new prompt at the end of the buffer.

        Parameters
        ----------
        prompt : str, optional
            The prompt to show. If not specified, the previous prompt is used.

        html : bool, optional (default False)
            Only relevant when a prompt is specified. If set, the prompt will
            be inserted as formatted HTML. Otherwise, the prompt will be treated
            as plain text, though ANSI color codes will be handled.

        newline : bool, optional (default True)
            If set, a new line will be written before showing the prompt if 
            there is not already a newline at the end of the buffer.
        """
        # Insert a preliminary newline, if necessary.
        if newline:
            cursor = self._get_end_cursor()
            if cursor.position() > 0:
                cursor.movePosition(QtGui.QTextCursor.Left, 
                                    QtGui.QTextCursor.KeepAnchor)
                if str(cursor.selection().toPlainText()) != '\n':
                    self._append_plain_text('\n')

        # Write the prompt.
        if prompt is None:
            if self._prompt_html is None:
                self._append_plain_text(self._prompt)
            else:
                self._append_html(self._prompt_html)
        else:
            if html:
                self._prompt = self._append_html_fetching_plain_text(prompt)
                self._prompt_html = prompt
            else:
                self._append_plain_text(prompt)
                self._prompt = prompt
                self._prompt_html = None

        self._prompt_pos = self._get_end_cursor().position()
        self._prompt_started()

    def _show_continuation_prompt(self):
        """ Writes a new continuation prompt at the end of the buffer.
        """
        if self._continuation_prompt_html is None:
            self._append_plain_text(self._continuation_prompt)
        else:
            self._continuation_prompt = self._append_html_fetching_plain_text(
                self._continuation_prompt_html)

        self._prompt_started()


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

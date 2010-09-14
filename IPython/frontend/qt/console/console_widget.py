"""A base class for console-type widgets.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
from os.path import commonprefix
import re
import sys
from textwrap import dedent

# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.config.configurable import Configurable
from IPython.frontend.qt.util import MetaQObjectHasTraits, get_font
from IPython.utils.traitlets import Bool, Enum, Int
from ansi_code_processor import QtAnsiCodeProcessor
from completion_widget import CompletionWidget

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ConsoleWidget(Configurable, QtGui.QWidget):
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
    __metaclass__ = MetaQObjectHasTraits

    # Whether to process ANSI escape codes.
    ansi_codes = Bool(True, config=True)

    # The maximum number of lines of text before truncation. Specifying a
    # non-positive number disables text truncation (not recommended).
    buffer_size = Int(500, config=True)

    # Whether to use a list widget or plain text output for tab completion.
    gui_completion = Bool(False, config=True)

    # The type of underlying text widget to use. Valid values are 'plain', which
    # specifies a QPlainTextEdit, and 'rich', which specifies a QTextEdit.
    # NOTE: this value can only be specified during initialization.
    kind = Enum(['plain', 'rich'], default_value='plain', config=True)

    # The type of paging to use. Valid values are:
    #     'inside' : The widget pages like a traditional terminal pager.
    #     'hsplit' : When paging is requested, the widget is split
    #                horizontally. The top pane contains the console, and the
    #                bottom pane contains the paged text.
    #     'vsplit' : Similar to 'hsplit', except that a vertical splitter used.
    #     'custom' : No action is taken by the widget beyond emitting a
    #                'custom_page_requested(str)' signal.
    #     'none'   : The text is written directly to the console.
    # NOTE: this value can only be specified during initialization.
    paging = Enum(['inside', 'hsplit', 'vsplit', 'custom', 'none'], 
                  default_value='inside', config=True)

    # Whether to override ShortcutEvents for the keybindings defined by this
    # widget (Ctrl+n, Ctrl+a, etc). Enable this if you want this widget to take
    # priority (when it has focus) over, e.g., window-level menu shortcuts.
    override_shortcuts = Bool(False)

    # Signals that indicate ConsoleWidget state.
    copy_available = QtCore.pyqtSignal(bool)
    redo_available = QtCore.pyqtSignal(bool)
    undo_available = QtCore.pyqtSignal(bool)

    # Signal emitted when paging is needed and the paging style has been
    # specified as 'custom'.
    custom_page_requested = QtCore.pyqtSignal(object)

    # Protected class variables.
    _ctrl_down_remap = { QtCore.Qt.Key_B : QtCore.Qt.Key_Left,
                         QtCore.Qt.Key_F : QtCore.Qt.Key_Right,
                         QtCore.Qt.Key_A : QtCore.Qt.Key_Home,
                         QtCore.Qt.Key_E : QtCore.Qt.Key_End,
                         QtCore.Qt.Key_P : QtCore.Qt.Key_Up,
                         QtCore.Qt.Key_N : QtCore.Qt.Key_Down,
                         QtCore.Qt.Key_D : QtCore.Qt.Key_Delete, }
    _shortcuts = set(_ctrl_down_remap.keys() +
                     [ QtCore.Qt.Key_C, QtCore.Qt.Key_G, QtCore.Qt.Key_O,
                       QtCore.Qt.Key_V ])

    #---------------------------------------------------------------------------
    # 'QObject' interface
    #---------------------------------------------------------------------------

    def __init__(self, parent=None, **kw):
        """ Create a ConsoleWidget.

        Parameters:
        -----------
        parent : QWidget, optional [default None]
            The parent for this widget.
        """
        QtGui.QWidget.__init__(self, parent)
        Configurable.__init__(self, **kw)

        # Create the layout and underlying text widget.
        layout = QtGui.QStackedLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._control = self._create_control()
        self._page_control = None
        self._splitter = None
        if self.paging in ('hsplit', 'vsplit'):
            self._splitter = QtGui.QSplitter()
            if self.paging == 'hsplit':
                self._splitter.setOrientation(QtCore.Qt.Horizontal)
            else:
                self._splitter.setOrientation(QtCore.Qt.Vertical)
            self._splitter.addWidget(self._control)
            layout.addWidget(self._splitter)
        else:
            layout.addWidget(self._control)

        # Create the paging widget, if necessary.
        if self.paging in ('inside', 'hsplit', 'vsplit'):
            self._page_control = self._create_page_control()
            if self._splitter:
                self._page_control.hide()
                self._splitter.addWidget(self._page_control)
            else:
                layout.addWidget(self._page_control)

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
        self._prompt_sep = ''
        self._reading = False
        self._reading_callback = None
        self._tab_width = 8
        self._text_completing_pos = 0

        # Set a monospaced font.
        self.reset_font()

    def eventFilter(self, obj, event):
        """ Reimplemented to ensure a console-like behavior in the underlying
            text widgets.
        """
        etype = event.type()
        if etype == QtCore.QEvent.KeyPress:

            # Re-map keys for all filtered widgets.
            key = event.key()
            if self._control_key_down(event.modifiers()) and \
                    key in self._ctrl_down_remap:
                new_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, 
                                            self._ctrl_down_remap[key],
                                            QtCore.Qt.NoModifier)
                QtGui.qApp.sendEvent(obj, new_event)
                return True

            elif obj == self._control:
                return self._event_filter_console_keypress(event)

            elif obj == self._page_control:
                return self._event_filter_page_keypress(event)

        # Make middle-click paste safe.
        elif etype == QtCore.QEvent.MouseButtonRelease and \
                event.button() == QtCore.Qt.MidButton and \
                obj == self._control.viewport():
            cursor = self._control.cursorForPosition(event.pos())
            self._control.setTextCursor(cursor)
            self.paste(QtGui.QClipboard.Selection)
            return True

        # Manually adjust the scrollbars *after* a resize event is dispatched.
        elif etype == QtCore.QEvent.Resize:
            QtCore.QTimer.singleShot(0, self._adjust_scrollbars)

        # Override shortcuts for all filtered widgets.
        elif etype == QtCore.QEvent.ShortcutOverride and \
                self.override_shortcuts and \
                self._control_key_down(event.modifiers()) and \
                event.key() in self._shortcuts:
            event.accept()
            return False

        # Prevent text from being moved by drag and drop.
        elif etype in (QtCore.QEvent.DragEnter, QtCore.QEvent.DragLeave, 
                       QtCore.QEvent.DragMove, QtCore.QEvent.Drop):
            return True

        return super(ConsoleWidget, self).eventFilter(obj, event)

    #---------------------------------------------------------------------------
    # 'QWidget' interface
    #---------------------------------------------------------------------------

    def sizeHint(self):
        """ Reimplemented to suggest a size that is 80 characters wide and
            25 lines high.
        """
        font_metrics = QtGui.QFontMetrics(self.font)
        margin = (self._control.frameWidth() +
                  self._control.document().documentMargin()) * 2
        style = self.style()
        splitwidth = style.pixelMetric(QtGui.QStyle.PM_SplitterWidth)

        # Note 1: Despite my best efforts to take the various margins into
        # account, the width is still coming out a bit too small, so we include
        # a fudge factor of one character here.
        # Note 2: QFontMetrics.maxWidth is not used here or anywhere else due
        # to a Qt bug on certain Mac OS systems where it returns 0.
        width = font_metrics.width(' ') * 81 + margin
        width += style.pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        if self.paging == 'hsplit':
            width = width * 2 + splitwidth

        height = font_metrics.height() * 25 + margin
        if self.paging == 'vsplit':
            height = height * 2 + splitwidth

        return QtCore.QSize(width, height)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def can_copy(self):
        """ Returns whether text can be copied to the clipboard.
        """
        return self._control.textCursor().hasSelection()

    def can_cut(self):
        """ Returns whether text can be cut to the clipboard.
        """
        cursor = self._control.textCursor()
        return (cursor.hasSelection() and 
                self._in_buffer(cursor.anchor()) and 
                self._in_buffer(cursor.position()))
        
    def can_paste(self):
        """ Returns whether text can be pasted from the clipboard.
        """
        # Only accept text that can be ASCII encoded.
        if self._control.textInteractionFlags() & QtCore.Qt.TextEditable:
            text = QtGui.QApplication.clipboard().text()
            if not text.isEmpty():
                try:
                    str(text)
                    return True
                except UnicodeEncodeError:
                    pass
        return False

    def clear(self, keep_input=True):
        """ Clear the console, then write a new prompt. If 'keep_input' is set,
            restores the old input buffer when the new prompt is written.
        """
        if keep_input:
            input_buffer = self.input_buffer
        self._control.clear()
        self._show_prompt()
        if keep_input:
            self.input_buffer = input_buffer

    def copy(self):
        """ Copy the currently selected text to the clipboard.
        """
        self._control.copy()

    def cut(self):
        """ Copy the currently selected text to the clipboard and delete it
            if it's inside the input buffer.
        """
        self.copy()
        if self.can_cut():
            self._control.textCursor().removeSelectedText()

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
        # WARNING: The order in which things happen here is very particular, in
        # large part because our syntax highlighting is fragile. If you change
        # something, test carefully!

        # Decide what to execute.
        if source is None:
            source = self.input_buffer
            if not hidden:
                # A newline is appended later, but it should be considered part
                # of the input buffer.
                source += '\n'
        elif not hidden:
            self.input_buffer = source
            
        # Execute the source or show a continuation prompt if it is incomplete.
        complete = self._is_complete(source, interactive)
        if hidden:
            if complete:
                self._execute(source, hidden)
            else:
                error = 'Incomplete noninteractive input: "%s"'
                raise RuntimeError(error % source)                
        else:
            if complete:
                self._append_plain_text('\n')
                self._executing_input_buffer = self.input_buffer
                self._executing = True
                self._prompt_finished()

                # The maximum block count is only in effect during execution.
                # This ensures that _prompt_pos does not become invalid due to
                # text truncation.
                self._control.document().setMaximumBlockCount(self.buffer_size)

                # Setting a positive maximum block count will automatically
                # disable the undo/redo history, but just to be safe:
                self._control.setUndoRedoEnabled(False)

                # Perform actual execution.
                self._execute(source, hidden)
            
            else:
                # Do this inside an edit block so continuation prompts are
                # removed seamlessly via undo/redo.
                cursor = self._get_end_cursor()
                cursor.beginEditBlock()
                cursor.insertText('\n')
                self._insert_continuation_prompt(cursor)
                cursor.endEditBlock()

                # Do not do this inside the edit block. It works as expected
                # when using a QPlainTextEdit control, but does not have an 
                # effect when using a QTextEdit. I believe this is a Qt bug.
                self._control.moveCursor(QtGui.QTextCursor.End)

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
        if self._page_control:
            self._page_control.document().setDefaultFont(font)

    font = property(_get_font, _set_font)

    def paste(self, mode=QtGui.QClipboard.Clipboard):
        """ Paste the contents of the clipboard into the input region.

        Parameters:
        -----------
        mode : QClipboard::Mode, optional [default QClipboard::Clipboard]

            Controls which part of the system clipboard is used. This can be
            used to access the selection clipboard in X11 and the Find buffer
            in Mac OS. By default, the regular clipboard is used.
        """
        if self._control.textInteractionFlags() & QtCore.Qt.TextEditable:
            try:
                # Remove any trailing newline, which confuses the GUI and
                # forces the user to backspace.
                text = str(QtGui.QApplication.clipboard().text(mode)).rstrip()
            except UnicodeEncodeError:
                pass
            else:
                self._insert_plain_text_into_buffer(dedent(text))

    def print_(self, printer):
        """ Print the contents of the ConsoleWidget to the specified QPrinter.
        """
        self._control.print_(printer)

    def prompt_to_top(self):
        """ Moves the prompt to the top of the viewport.
        """
        if not self._executing:
            prompt_cursor = self._get_prompt_cursor()
            if self._get_cursor().blockNumber() < prompt_cursor.blockNumber():
                self._set_cursor(prompt_cursor)
            self._set_top_cursor(prompt_cursor)
            
    def redo(self):
        """ Redo the last operation. If there is no operation to redo, nothing
            happens.
        """
        self._control.redo()

    def reset_font(self):
        """ Sets the font to the default fixed-width font for this platform.
        """
        if sys.platform == 'win32':
            # Consolas ships with Vista/Win7, fallback to Courier if needed
            family, fallback = 'Consolas', 'Courier'
        elif sys.platform == 'darwin':
            # OSX always has Monaco, no need for a fallback
            family, fallback = 'Monaco', None
        else:
            # FIXME: remove Consolas as a default on Linux once our font
            # selections are configurable by the user.
            family, fallback = 'Consolas', 'Monospace'
        font = get_font(family, fallback)
        font.setPointSize(QtGui.qApp.font().pointSize())
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
        cursor = self._get_end_cursor()
        return self._insert_html_fetching_plain_text(cursor, html)

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

    def _cancel_text_completion(self):
        """ If text completion is progress, cancel it.
        """
        if self._text_completing_pos:
            self._clear_temporary_buffer()
            self._text_completing_pos = 0

    def _clear_temporary_buffer(self):
        """ Clears the "temporary text" buffer, i.e. all the text following
            the prompt region.
        """
        # Select and remove all text below the input buffer.
        cursor = self._get_prompt_cursor()
        prompt = self._continuation_prompt.lstrip()
        while cursor.movePosition(QtGui.QTextCursor.NextBlock):
            temp_cursor = QtGui.QTextCursor(cursor)
            temp_cursor.select(QtGui.QTextCursor.BlockUnderCursor)
            text = str(temp_cursor.selection().toPlainText()).lstrip()
            if not text.startswith(prompt):
                break
        else:
            # We've reached the end of the input buffer and no text follows.
            return
        cursor.movePosition(QtGui.QTextCursor.Left) # Grab the newline.
        cursor.movePosition(QtGui.QTextCursor.End,
                            QtGui.QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

        # After doing this, we have no choice but to clear the undo/redo
        # history. Otherwise, the text is not "temporary" at all, because it
        # can be recalled with undo/redo. Unfortunately, Qt does not expose
        # fine-grained control to the undo/redo system.
        if self._control.isUndoRedoEnabled():
            self._control.setUndoRedoEnabled(False)
            self._control.setUndoRedoEnabled(True)

    def _complete_with_items(self, cursor, items):
        """ Performs completion with 'items' at the specified cursor location.
        """
        self._cancel_text_completion()

        if len(items) == 1:
            cursor.setPosition(self._control.textCursor().position(), 
                               QtGui.QTextCursor.KeepAnchor)
            cursor.insertText(items[0])

        elif len(items) > 1:
            current_pos = self._control.textCursor().position()
            prefix = commonprefix(items)
            if prefix:
                cursor.setPosition(current_pos, QtGui.QTextCursor.KeepAnchor)
                cursor.insertText(prefix)
                current_pos = cursor.position()

            if self.gui_completion:
                cursor.movePosition(QtGui.QTextCursor.Left, n=len(prefix))
                self._completion_widget.show_items(cursor, items) 
            else:
                cursor.beginEditBlock()
                self._append_plain_text('\n')
                self._page(self._format_as_columns(items))
                cursor.endEditBlock()

                cursor.setPosition(current_pos)
                self._control.moveCursor(QtGui.QTextCursor.End)
                self._control.setTextCursor(cursor)
                self._text_completing_pos = current_pos

    def _context_menu_make(self, pos):
        """ Creates a context menu for the given QPoint (in widget coordinates).
        """
        menu = QtGui.QMenu()

        cut_action = menu.addAction('Cut', self.cut)
        cut_action.setEnabled(self.can_cut())
        cut_action.setShortcut(QtGui.QKeySequence.Cut)

        copy_action = menu.addAction('Copy', self.copy)
        copy_action.setEnabled(self.can_copy())
        copy_action.setShortcut(QtGui.QKeySequence.Copy)

        paste_action = menu.addAction('Paste', self.paste)
        paste_action.setEnabled(self.can_paste())
        paste_action.setShortcut(QtGui.QKeySequence.Paste)

        menu.addSeparator()
        menu.addAction('Select All', self.select_all)
        
        return menu

    def _control_key_down(self, modifiers, include_command=True):
        """ Given a KeyboardModifiers flags object, return whether the Control
        key is down.

        Parameters:
        -----------
        include_command : bool, optional (default True)
            Whether to treat the Command key as a (mutually exclusive) synonym
            for Control when in Mac OS.
        """
        # Note that on Mac OS, ControlModifier corresponds to the Command key
        # while MetaModifier corresponds to the Control key.
        if sys.platform == 'darwin':
            down = include_command and (modifiers & QtCore.Qt.ControlModifier)
            return bool(down) ^ bool(modifiers & QtCore.Qt.MetaModifier)
        else:
            return bool(modifiers & QtCore.Qt.ControlModifier)

    def _create_control(self):
        """ Creates and connects the underlying text widget.
        """
        # Create the underlying control.
        if self.kind == 'plain':
            control = QtGui.QPlainTextEdit()
        elif self.kind == 'rich':
            control = QtGui.QTextEdit()
            control.setAcceptRichText(False)

        # Install event filters. The filter on the viewport is needed for
        # mouse events and drag events.
        control.installEventFilter(self)
        control.viewport().installEventFilter(self)

        # Connect signals.
        control.cursorPositionChanged.connect(self._cursor_position_changed)
        control.customContextMenuRequested.connect(
            self._custom_context_menu_requested)
        control.copyAvailable.connect(self.copy_available)
        control.redoAvailable.connect(self.redo_available)
        control.undoAvailable.connect(self.undo_available)

        # Hijack the document size change signal to prevent Qt from adjusting
        # the viewport's scrollbar. We are relying on an implementation detail
        # of Q(Plain)TextEdit here, which is potentially dangerous, but without
        # this functionality we cannot create a nice terminal interface.
        layout = control.document().documentLayout()
        layout.documentSizeChanged.disconnect()
        layout.documentSizeChanged.connect(self._adjust_scrollbars)

        # Configure the control.
        control.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        control.setReadOnly(True)
        control.setUndoRedoEnabled(False)
        control.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        return control

    def _create_page_control(self):
        """ Creates and connects the underlying paging widget.
        """
        if self.kind == 'plain':
            control = QtGui.QPlainTextEdit()
        elif self.kind == 'rich':
            control = QtGui.QTextEdit()
        control.installEventFilter(self)
        control.setReadOnly(True)
        control.setUndoRedoEnabled(False)
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

        #------ Special sequences ----------------------------------------------

        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
            intercepted = True

        elif event.matches(QtGui.QKeySequence.Cut):
            self.cut()
            intercepted = True

        elif event.matches(QtGui.QKeySequence.Paste):
            self.paste()
            intercepted = True

        #------ Special modifier logic -----------------------------------------

        elif key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            intercepted = True
                
            # Special handling when tab completing in text mode.
            self._cancel_text_completion()

            if self._in_buffer(position):
                if self._reading:
                    self._append_plain_text('\n')
                    self._reading = False
                    if self._reading_callback:
                        self._reading_callback()

                # If the input buffer is a single line or there is only
                # whitespace after the cursor, execute. Otherwise, split the
                # line with a continuation prompt.
                elif not self._executing:
                    cursor.movePosition(QtGui.QTextCursor.End,
                                        QtGui.QTextCursor.KeepAnchor)
                    at_end = cursor.selectedText().trimmed().isEmpty() 
                    single_line = (self._get_end_cursor().blockNumber() ==
                                   self._get_prompt_cursor().blockNumber())
                    if (at_end or shift_down or single_line) and not ctrl_down:
                        self.execute(interactive = not shift_down)
                    else:
                        # Do this inside an edit block for clean undo/redo.
                        cursor.beginEditBlock()
                        cursor.setPosition(position)
                        cursor.insertText('\n')
                        self._insert_continuation_prompt(cursor)
                        cursor.endEditBlock()

                        # Ensure that the whole input buffer is visible.
                        # FIXME: This will not be usable if the input buffer is
                        # taller than the console widget.
                        self._control.moveCursor(QtGui.QTextCursor.End)
                        self._control.setTextCursor(cursor)

        #------ Control/Cmd modifier -------------------------------------------

        elif ctrl_down:
            if key == QtCore.Qt.Key_G:
                self._keyboard_quit()
                intercepted = True

            elif key == QtCore.Qt.Key_K:
                if self._in_buffer(position):
                    cursor.movePosition(QtGui.QTextCursor.EndOfLine,
                                        QtGui.QTextCursor.KeepAnchor)
                    if not cursor.hasSelection():
                        # Line deletion (remove continuation prompt)
                        cursor.movePosition(QtGui.QTextCursor.NextBlock,
                                            QtGui.QTextCursor.KeepAnchor)
                        cursor.movePosition(QtGui.QTextCursor.Right,
                                            QtGui.QTextCursor.KeepAnchor,
                                            len(self._continuation_prompt))
                    cursor.removeSelectedText()
                intercepted = True

            elif key == QtCore.Qt.Key_L:
                self.prompt_to_top()
                intercepted = True

            elif key == QtCore.Qt.Key_O:
                if self._page_control and self._page_control.isVisible():
                    self._page_control.setFocus()
                intercept = True

            elif key == QtCore.Qt.Key_Y:
                self.paste()
                intercepted = True

            elif key in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete):
                intercepted = True

        #------ Alt modifier ---------------------------------------------------

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

            elif key == QtCore.Qt.Key_Delete:
                intercepted = True

            elif key == QtCore.Qt.Key_Greater:
                self._control.moveCursor(QtGui.QTextCursor.End)
                intercepted = True
                
            elif key == QtCore.Qt.Key_Less:
                self._control.setTextCursor(self._get_prompt_cursor())
                intercepted = True

        #------ No modifiers ---------------------------------------------------

        else:
            if key == QtCore.Qt.Key_Escape:
                self._keyboard_quit()
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
                if not self._reading:
                    intercepted = not self._tab_pressed()

            elif key == QtCore.Qt.Key_Left:

                # Move to the previous line
                line, col = cursor.blockNumber(), cursor.columnNumber()
                if line > self._get_prompt_cursor().blockNumber() and \
                        col == len(self._continuation_prompt):
                    self._control.moveCursor(QtGui.QTextCursor.PreviousBlock)
                    self._control.moveCursor(QtGui.QTextCursor.EndOfBlock)
                    intercepted = True

                # Regular left movement
                else:
                    intercepted = not self._in_buffer(position - 1)
                    
            elif key == QtCore.Qt.Key_Right:
                original_block_number = cursor.blockNumber()
                cursor.movePosition(QtGui.QTextCursor.Right)
                if cursor.blockNumber() != original_block_number:
                    cursor.movePosition(QtGui.QTextCursor.Right,
                                        n=len(self._continuation_prompt))
                self._set_cursor(cursor)
                intercepted = True

            elif key == QtCore.Qt.Key_Home:
                start_line = cursor.blockNumber()
                if start_line == self._get_prompt_cursor().blockNumber():
                    start_pos = self._prompt_pos
                else:
                    cursor.movePosition(QtGui.QTextCursor.StartOfBlock,
                                        QtGui.QTextCursor.KeepAnchor)
                    start_pos = cursor.position()
                    start_pos += len(self._continuation_prompt)
                    cursor.setPosition(position)
                if shift_down and self._in_buffer(position):
                    cursor.setPosition(start_pos, QtGui.QTextCursor.KeepAnchor)
                else:
                    cursor.setPosition(start_pos)
                self._set_cursor(cursor)
                intercepted = True

            elif key == QtCore.Qt.Key_Backspace:

                # Line deletion (remove continuation prompt)
                line, col = cursor.blockNumber(), cursor.columnNumber()
                if not self._reading and \
                        col == len(self._continuation_prompt) and \
                        line > self._get_prompt_cursor().blockNumber():
                    cursor.beginEditBlock()
                    cursor.movePosition(QtGui.QTextCursor.StartOfBlock,
                                        QtGui.QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                    cursor.deletePreviousChar()
                    cursor.endEditBlock()
                    intercepted = True

                # Regular backwards deletion
                else:
                    anchor = cursor.anchor()
                    if anchor == position:
                        intercepted = not self._in_buffer(position - 1)
                    else:
                        intercepted = not self._in_buffer(min(anchor, position))

            elif key == QtCore.Qt.Key_Delete:

                # Line deletion (remove continuation prompt)
                if not self._reading and self._in_buffer(position) and \
                        cursor.atBlockEnd() and not cursor.hasSelection():
                    cursor.movePosition(QtGui.QTextCursor.NextBlock,
                                        QtGui.QTextCursor.KeepAnchor)
                    cursor.movePosition(QtGui.QTextCursor.Right,
                                        QtGui.QTextCursor.KeepAnchor,
                                        len(self._continuation_prompt))
                    cursor.removeSelectedText()
                    intercepted = True

                # Regular forwards deletion:
                else:
                    anchor = cursor.anchor()
                    intercepted = (not self._in_buffer(anchor) or
                                   not self._in_buffer(position))

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
        ctrl_down = self._control_key_down(event.modifiers())
        alt_down = event.modifiers() & QtCore.Qt.AltModifier

        if ctrl_down:
            if key == QtCore.Qt.Key_O:
                self._control.setFocus()
                intercept = True

        elif alt_down:
            if key == QtCore.Qt.Key_Greater:
                self._page_control.moveCursor(QtGui.QTextCursor.End)
                intercepted = True
                
            elif key == QtCore.Qt.Key_Less:
                self._page_control.moveCursor(QtGui.QTextCursor.Start)
                intercepted = True

        elif key in (QtCore.Qt.Key_Q, QtCore.Qt.Key_Escape):
            if self._splitter:
                self._page_control.hide()
            else:
                self.layout().setCurrentWidget(self._control)
            return True

        elif key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            new_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, 
                                        QtCore.Qt.Key_PageDown, 
                                        QtCore.Qt.NoModifier)
            QtGui.qApp.sendEvent(self._page_control, new_event)
            return True

        elif key == QtCore.Qt.Key_Backspace:
            new_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress,
                                        QtCore.Qt.Key_PageUp, 
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

        # Calculate the number of characters available.
        width = self._control.viewport().width()
        char_width = QtGui.QFontMetrics(self.font).width(' ')
        displaywidth = max(10, (width / char_width) - 1)

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

    def _get_input_buffer_cursor_column(self):
        """ Returns the column of the cursor in the input buffer, excluding the
            contribution by the prompt, or -1 if there is no such column.
        """
        prompt = self._get_input_buffer_cursor_prompt()
        if prompt is None:
            return -1
        else:
            cursor = self._control.textCursor()
            return cursor.columnNumber() - len(prompt)

    def _get_input_buffer_cursor_line(self):
        """ Returns line of the input buffer that contains the cursor, or None
            if there is no such line.
        """
        prompt = self._get_input_buffer_cursor_prompt()
        if prompt is None:
            return None
        else:
            cursor = self._control.textCursor()
            text = self._get_block_plain_text(cursor.block())
            return text[len(prompt):]

    def _get_input_buffer_cursor_prompt(self):
        """ Returns the (plain text) prompt for line of the input buffer that
            contains the cursor, or None if there is no such line.
        """
        if self._executing:
            return None
        cursor = self._control.textCursor()
        if cursor.position() >= self._prompt_pos:
            if cursor.blockNumber() == self._get_prompt_cursor().blockNumber():
                return self._prompt
            else:
                return self._continuation_prompt
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

    def _insert_continuation_prompt(self, cursor):
        """ Inserts new continuation prompt using the specified cursor.
        """
        if self._continuation_prompt_html is None:
            self._insert_plain_text(cursor, self._continuation_prompt)
        else:
            self._continuation_prompt = self._insert_html_fetching_plain_text(
                cursor, self._continuation_prompt_html)

    def _insert_html(self, cursor, html):
        """ Inserts HTML using the specified cursor in such a way that future
            formatting is unaffected.
        """
        cursor.beginEditBlock()
        cursor.insertHtml(html)

        # After inserting HTML, the text document "remembers" it's in "html
        # mode", which means that subsequent calls adding plain text will result
        # in unwanted formatting, lost tab characters, etc. The following code
        # hacks around this behavior, which I consider to be a bug in Qt, by
        # (crudely) resetting the document's style state.
        cursor.movePosition(QtGui.QTextCursor.Left,
                            QtGui.QTextCursor.KeepAnchor)
        if cursor.selection().toPlainText() == ' ':
            cursor.removeSelectedText()
        else:
            cursor.movePosition(QtGui.QTextCursor.Right)
        cursor.insertText(' ', QtGui.QTextCharFormat())
        cursor.endEditBlock()

    def _insert_html_fetching_plain_text(self, cursor, html):
        """ Inserts HTML using the specified cursor, then returns its plain text
            version.
        """
        cursor.beginEditBlock()
        cursor.removeSelectedText()

        start = cursor.position()
        self._insert_html(cursor, html)
        end = cursor.position()
        cursor.setPosition(start, QtGui.QTextCursor.KeepAnchor)
        text = str(cursor.selection().toPlainText())

        cursor.setPosition(end)
        cursor.endEditBlock()
        return text

    def _insert_plain_text(self, cursor, text):
        """ Inserts plain text using the specified cursor, processing ANSI codes
            if enabled.
        """
        cursor.beginEditBlock()
        if self.ansi_codes:
            for substring in self._ansi_processor.split_string(text):
                for act in self._ansi_processor.actions:

                    # Unlike real terminal emulators, we don't distinguish
                    # between the screen and the scrollback buffer. A screen
                    # erase request clears everything.
                    if act.action == 'erase' and act.area == 'screen':
                        cursor.select(QtGui.QTextCursor.Document)
                        cursor.removeSelectedText()

                    # Simulate a form feed by scrolling just past the last line.
                    elif act.action == 'scroll' and act.unit == 'page':
                        cursor.insertText('\n')
                        cursor.endEditBlock()
                        self._set_top_cursor(cursor)
                        cursor.joinPreviousEditBlock()
                        cursor.deletePreviousChar()
                        
                format = self._ansi_processor.get_format()
                cursor.insertText(substring, format)
        else:
            cursor.insertText(text)
        cursor.endEditBlock()

    def _insert_plain_text_into_buffer(self, text):
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
                    self._continuation_prompt = \
                        self._insert_html_fetching_plain_text(
                            cursor, self._continuation_prompt_html)
                cursor.insertText(line)
            cursor.endEditBlock()
            self._control.setTextCursor(cursor)

    def _in_buffer(self, position=None):
        """ Returns whether the current cursor (or, if specified, a position) is
            inside the editing region.
        """
        cursor = self._control.textCursor()
        if position is None:
            position = cursor.position()
        else:
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
        moved = not self._in_buffer()
        if moved:
            cursor = self._control.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self._control.setTextCursor(cursor)
        return moved

    def _keyboard_quit(self):
        """ Cancels the current editing task ala Ctrl-G in Emacs.
        """
        if self._text_completing_pos:
            self._cancel_text_completion()
        else:
            self.input_buffer = ''
        
    def _page(self, text, html=False):
        """ Displays text using the pager if it exceeds the height of the
        viewport.

        Parameters:
        -----------
        html : bool, optional (default False)
            If set, the text will be interpreted as HTML instead of plain text.
        """
        line_height = QtGui.QFontMetrics(self.font).height()
        minlines = self._control.viewport().height() / line_height
        if self.paging != 'none' and \
                re.match("(?:[^\n]*\n){%i}" % minlines, text):
            if self.paging == 'custom':
                self.custom_page_requested.emit(text)
            else:
                self._page_control.clear()
                cursor = self._page_control.textCursor()
                if html:
                    self._insert_html(cursor, text)
                else:
                    self._insert_plain_text(cursor, text)
                self._page_control.moveCursor(QtGui.QTextCursor.Start)

                self._page_control.viewport().resize(self._control.size())
                if self._splitter:
                    self._page_control.show()
                    self._page_control.setFocus()
                else:
                    self.layout().setCurrentWidget(self._page_control)
        elif html:
            self._append_plain_html(text)
        else:
            self._append_plain_text(text)

    def _prompt_finished(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        # Flush all state from the input splitter so the next round of
        # reading input starts with a clean buffer.
        self._input_splitter.reset()

        self._control.setReadOnly(True)
        self._prompt_finished_hook()

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
            raise RuntimeError('Cannot synchronously read a line if the widget '
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

    def _set_top_cursor(self, cursor):
        """ Scrolls the viewport so that the specified cursor is at the top.
        """
        scrollbar = self._control.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        original_cursor = self._control.textCursor()
        self._control.setTextCursor(cursor)
        self._control.ensureCursorVisible()
        self._control.setTextCursor(original_cursor)

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
        self._append_plain_text(self._prompt_sep)
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

    #------ Signal handlers ----------------------------------------------------

    def _adjust_scrollbars(self):
        """ Expands the vertical scrollbar beyond the range set by Qt.
        """
        # This code is adapted from _q_adjustScrollbars in qplaintextedit.cpp
        # and qtextedit.cpp.
        document = self._control.document()
        scrollbar = self._control.verticalScrollBar()
        viewport_height = self._control.viewport().height()
        if isinstance(self._control, QtGui.QPlainTextEdit):
            maximum = max(0, document.lineCount() - 1)
            step = viewport_height / self._control.fontMetrics().lineSpacing()
        else:
            # QTextEdit does not do line-based layout and blocks will not in
            # general have the same height. Therefore it does not make sense to
            # attempt to scroll in line height increments.
            maximum = document.size().height()
            step = viewport_height
        diff = maximum - scrollbar.maximum()
        scrollbar.setRange(0, maximum)
        scrollbar.setPageStep(step)
        # Compensate for undesirable scrolling that occurs automatically due to
        # maximumBlockCount() text truncation.
        if diff < 0 and document.blockCount() == document.maximumBlockCount():
            scrollbar.setValue(scrollbar.value() + diff)

    def _cursor_position_changed(self):
        """ Clears the temporary buffer based on the cursor position.
        """
        if self._text_completing_pos:
            document = self._control.document()
            if self._text_completing_pos < document.characterCount():
                cursor = self._control.textCursor()
                pos = cursor.position()
                text_cursor = self._control.textCursor()
                text_cursor.setPosition(self._text_completing_pos)
                if pos < self._text_completing_pos or \
                        cursor.blockNumber() > text_cursor.blockNumber():
                    self._clear_temporary_buffer()
                    self._text_completing_pos = 0
            else:
                self._clear_temporary_buffer()
                self._text_completing_pos = 0

    def _custom_context_menu_requested(self, pos):
        """ Shows a context menu at the given QPoint (in widget coordinates).
        """
        menu = self._context_menu_make(pos)
        menu.exec_(self._control.mapToGlobal(pos))

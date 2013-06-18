""" An abstract base class for console-type widgets.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
import os.path
import re
import sys
from textwrap import dedent
from unicodedata import category
import webbrowser

# System library imports
from IPython.external.qt import QtCore, QtGui

# Local imports
from IPython.config.configurable import LoggingConfigurable
from IPython.core.inputsplitter import ESC_SEQUENCES
from IPython.qt.rich_text import HtmlExporter
from IPython.qt.util import MetaQObjectHasTraits, get_font
from IPython.utils.text import columnize
from IPython.utils.traitlets import Bool, Enum, Integer, Unicode
from ansi_code_processor import QtAnsiCodeProcessor
from completion_widget import CompletionWidget
from completion_html import CompletionHtml
from completion_plain import CompletionPlain
from kill_ring import QtKillRing


#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

ESCAPE_CHARS = ''.join(ESC_SEQUENCES)
ESCAPE_RE = re.compile("^["+ESCAPE_CHARS+"]+")

def commonprefix(items):
    """Get common prefix for completions

    Return the longest common prefix of a list of strings, but with special
    treatment of escape characters that might precede commands in IPython,
    such as %magic functions. Used in tab completion.

    For a more general function, see os.path.commonprefix
    """
    # the last item will always have the least leading % symbol
    # min / max are first/last in alphabetical order
    first_match  = ESCAPE_RE.match(min(items))
    last_match  = ESCAPE_RE.match(max(items))
    # common suffix is (common prefix of reversed items) reversed
    if first_match and last_match:
        prefix = os.path.commonprefix((first_match.group(0)[::-1], last_match.group(0)[::-1]))[::-1]
    else:
        prefix = ''

    items = [s.lstrip(ESCAPE_CHARS) for s in items]
    return prefix+os.path.commonprefix(items)

def is_letter_or_number(char):
    """ Returns whether the specified unicode character is a letter or a number.
    """
    cat = category(char)
    return cat.startswith('L') or cat.startswith('N')

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ConsoleWidget(LoggingConfigurable, QtGui.QWidget):
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

    #------ Configuration ------------------------------------------------------

    ansi_codes = Bool(True, config=True,
        help="Whether to process ANSI escape codes."
    )
    buffer_size = Integer(500, config=True,
        help="""
        The maximum number of lines of text before truncation. Specifying a
        non-positive number disables text truncation (not recommended).
        """
    )
    gui_completion = Enum(['plain', 'droplist', 'ncurses'], config=True,
                    default_value = 'ncurses',
                    help="""
                    The type of completer to use. Valid values are:

                    'plain'   : Show the availlable completion as a text list
                                Below the editting area.
                    'droplist': Show the completion in a drop down list navigable
                                by the arrow keys, and from which you can select
                                completion by pressing Return.
                    'ncurses' : Show the completion as a text list which is navigable by
                                `tab` and arrow keys.
                    """
    )
    # NOTE: this value can only be specified during initialization.
    kind = Enum(['plain', 'rich'], default_value='plain', config=True,
        help="""
        The type of underlying text widget to use. Valid values are 'plain',
        which specifies a QPlainTextEdit, and 'rich', which specifies a
        QTextEdit.
        """
    )
    # NOTE: this value can only be specified during initialization.
    paging = Enum(['inside', 'hsplit', 'vsplit', 'custom', 'none'],
                  default_value='inside', config=True,
        help="""
        The type of paging to use. Valid values are:

            'inside' : The widget pages like a traditional terminal.
            'hsplit' : When paging is requested, the widget is split
                       horizontally. The top pane contains the console, and the
                       bottom pane contains the paged text.
            'vsplit' : Similar to 'hsplit', except that a vertical splitter
                       used.
            'custom' : No action is taken by the widget beyond emitting a
                       'custom_page_requested(str)' signal.
            'none'   : The text is written directly to the console.
        """)

    font_family = Unicode(config=True,
        help="""The font family to use for the console.
        On OSX this defaults to Monaco, on Windows the default is
        Consolas with fallback of Courier, and on other platforms
        the default is Monospace.
        """)
    def _font_family_default(self):
        if sys.platform == 'win32':
            # Consolas ships with Vista/Win7, fallback to Courier if needed
            return 'Consolas'
        elif sys.platform == 'darwin':
            # OSX always has Monaco, no need for a fallback
            return 'Monaco'
        else:
            # Monospace should always exist, no need for a fallback
            return 'Monospace'

    font_size = Integer(config=True,
        help="""The font size. If unconfigured, Qt will be entrusted
        with the size of the font.
        """)

    width = Integer(81, config=True,
        help="""The width of the console at start time in number
        of characters (will double with `hsplit` paging)
        """)

    height = Integer(25, config=True,
        help="""The height of the console at start time in number
        of characters (will double with `vsplit` paging)
        """)

    # Whether to override ShortcutEvents for the keybindings defined by this
    # widget (Ctrl+n, Ctrl+a, etc). Enable this if you want this widget to take
    # priority (when it has focus) over, e.g., window-level menu shortcuts.
    override_shortcuts = Bool(False)
    
    # ------ Custom Qt Widgets -------------------------------------------------
    
    # For other projects to easily override the Qt widgets used by the console
    # (e.g. Spyder)
    custom_control = None
    custom_page_control = None

    #------ Signals ------------------------------------------------------------

    # Signals that indicate ConsoleWidget state.
    copy_available = QtCore.Signal(bool)
    redo_available = QtCore.Signal(bool)
    undo_available = QtCore.Signal(bool)

    # Signal emitted when paging is needed and the paging style has been
    # specified as 'custom'.
    custom_page_requested = QtCore.Signal(object)

    # Signal emitted when the font is changed.
    font_changed = QtCore.Signal(QtGui.QFont)

    #------ Protected class variables ------------------------------------------

    # control handles
    _control = None
    _page_control = None
    _splitter = None

    # When the control key is down, these keys are mapped.
    _ctrl_down_remap = { QtCore.Qt.Key_B : QtCore.Qt.Key_Left,
                         QtCore.Qt.Key_F : QtCore.Qt.Key_Right,
                         QtCore.Qt.Key_A : QtCore.Qt.Key_Home,
                         QtCore.Qt.Key_P : QtCore.Qt.Key_Up,
                         QtCore.Qt.Key_N : QtCore.Qt.Key_Down,
                         QtCore.Qt.Key_H : QtCore.Qt.Key_Backspace, }
    if not sys.platform == 'darwin':
        # On OS X, Ctrl-E already does the right thing, whereas End moves the
        # cursor to the bottom of the buffer.
        _ctrl_down_remap[QtCore.Qt.Key_E] = QtCore.Qt.Key_End

    # The shortcuts defined by this widget. We need to keep track of these to
    # support 'override_shortcuts' above.
    _shortcuts = set(_ctrl_down_remap.keys() +
                     [ QtCore.Qt.Key_C, QtCore.Qt.Key_G, QtCore.Qt.Key_O,
                       QtCore.Qt.Key_V ])

    _temp_buffer_filled = False

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
        LoggingConfigurable.__init__(self, **kw)

        # While scrolling the pager on Mac OS X, it tears badly.  The
        # NativeGesture is platform and perhaps build-specific hence
        # we take adequate precautions here.
        self._pager_scroll_events = [QtCore.QEvent.Wheel]
        if hasattr(QtCore.QEvent, 'NativeGesture'):
            self._pager_scroll_events.append(QtCore.QEvent.NativeGesture)

        # Create the layout and underlying text widget.
        layout = QtGui.QStackedLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._control = self._create_control()
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
        self._append_before_prompt_pos = 0
        self._ansi_processor = QtAnsiCodeProcessor()
        if self.gui_completion == 'ncurses':
            self._completion_widget = CompletionHtml(self)
        elif self.gui_completion == 'droplist':
            self._completion_widget = CompletionWidget(self)
        elif self.gui_completion == 'plain':
            self._completion_widget = CompletionPlain(self)

        self._continuation_prompt = '> '
        self._continuation_prompt_html = None
        self._executing = False
        self._filter_resize = False
        self._html_exporter = HtmlExporter(self._control)
        self._input_buffer_executing = ''
        self._input_buffer_pending = ''
        self._kill_ring = QtKillRing(self._control)
        self._prompt = ''
        self._prompt_html = None
        self._prompt_pos = 0
        self._prompt_sep = ''
        self._reading = False
        self._reading_callback = None
        self._tab_width = 8

        # Set a monospaced font.
        self.reset_font()

        # Configure actions.
        action = QtGui.QAction('Print', None)
        action.setEnabled(True)
        printkey = QtGui.QKeySequence(QtGui.QKeySequence.Print)
        if printkey.matches("Ctrl+P") and sys.platform != 'darwin':
            # Only override the default if there is a collision.
            # Qt ctrl = cmd on OSX, so the match gets a false positive on OSX.
            printkey = "Ctrl+Shift+P"
        action.setShortcut(printkey)
        action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        action.triggered.connect(self.print_)
        self.addAction(action)
        self.print_action = action

        action = QtGui.QAction('Save as HTML/XML', None)
        action.setShortcut(QtGui.QKeySequence.Save)
        action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        action.triggered.connect(self.export_html)
        self.addAction(action)
        self.export_action = action

        action = QtGui.QAction('Select All', None)
        action.setEnabled(True)
        selectall = QtGui.QKeySequence(QtGui.QKeySequence.SelectAll)
        if selectall.matches("Ctrl+A") and sys.platform != 'darwin':
            # Only override the default if there is a collision.
            # Qt ctrl = cmd on OSX, so the match gets a false positive on OSX.
            selectall = "Ctrl+Shift+A"
        action.setShortcut(selectall)
        action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        action.triggered.connect(self.select_all)
        self.addAction(action)
        self.select_all_action = action

        self.increase_font_size = QtGui.QAction("Bigger Font",
                self,
                shortcut=QtGui.QKeySequence.ZoomIn,
                shortcutContext=QtCore.Qt.WidgetWithChildrenShortcut,
                statusTip="Increase the font size by one point",
                triggered=self._increase_font_size)
        self.addAction(self.increase_font_size)

        self.decrease_font_size = QtGui.QAction("Smaller Font",
                self,
                shortcut=QtGui.QKeySequence.ZoomOut,
                shortcutContext=QtCore.Qt.WidgetWithChildrenShortcut,
                statusTip="Decrease the font size by one point",
                triggered=self._decrease_font_size)
        self.addAction(self.decrease_font_size)

        self.reset_font_size = QtGui.QAction("Normal Font",
                self,
                shortcut="Ctrl+0",
                shortcutContext=QtCore.Qt.WidgetWithChildrenShortcut,
                statusTip="Restore the Normal font size",
                triggered=self.reset_font)
        self.addAction(self.reset_font_size)

        # Accept drag and drop events here. Drops were already turned off
        # in self._control when that widget was created.
        self.setAcceptDrops(True)

    #---------------------------------------------------------------------------
    # Drag and drop support
    #---------------------------------------------------------------------------

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            # The link action should indicate to that the drop will insert
            # the file anme.
            e.setDropAction(QtCore.Qt.LinkAction)
            e.accept()
        elif e.mimeData().hasText():
            # By changing the action to copy we don't need to worry about
            # the user accidentally moving text around in the widget.
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            pass
        elif e.mimeData().hasText():
            cursor = self._control.cursorForPosition(e.pos())
            if self._in_buffer(cursor.position()):
                e.setDropAction(QtCore.Qt.CopyAction)
                self._control.setTextCursor(cursor)
            else:
                e.setDropAction(QtCore.Qt.IgnoreAction)
            e.accept()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            self._keep_cursor_in_buffer()
            cursor = self._control.textCursor()
            filenames = [url.toLocalFile() for url in e.mimeData().urls()]
            text = ', '.join("'" + f.replace("'", "'\"'\"'") + "'"
                             for f in filenames)
            self._insert_plain_text_into_buffer(cursor, text)
        elif e.mimeData().hasText():
            cursor = self._control.cursorForPosition(e.pos())
            if self._in_buffer(cursor.position()):
                text = e.mimeData().text()
                self._insert_plain_text_into_buffer(cursor, text)

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
        elif etype == QtCore.QEvent.Resize and not self._filter_resize:
            self._filter_resize = True
            QtGui.qApp.sendEvent(obj, event)
            self._adjust_scrollbars()
            self._filter_resize = False
            return True

        # Override shortcuts for all filtered widgets.
        elif etype == QtCore.QEvent.ShortcutOverride and \
                self.override_shortcuts and \
                self._control_key_down(event.modifiers()) and \
                event.key() in self._shortcuts:
            event.accept()

        # Handle scrolling of the vsplit pager. This hack attempts to solve
        # problems with tearing of the help text inside the pager window.  This
        # happens only on Mac OS X with both PySide and PyQt. This fix isn't
        # perfect but makes the pager more usable.
        elif etype in self._pager_scroll_events and \
                obj == self._page_control:
            self._page_control.repaint()
            return True

        elif etype == QtCore.QEvent.MouseMove:
            anchor = self._control.anchorAt(event.pos())
            QtGui.QToolTip.showText(event.globalPos(), anchor)

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
        width = font_metrics.width(' ') * self.width + margin
        width += style.pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
        if self.paging == 'hsplit':
            width = width * 2 + splitwidth

        height = font_metrics.height() * self.height + margin
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
        if self._control.textInteractionFlags() & QtCore.Qt.TextEditable:
            return bool(QtGui.QApplication.clipboard().text())
        return False

    def clear(self, keep_input=True):
        """ Clear the console.

        Parameters:
        -----------
        keep_input : bool, optional (default True)
            If set, restores the old input buffer if a new prompt is written.
        """
        if self._executing:
            self._control.clear()
        else:
            if keep_input:
                input_buffer = self.input_buffer
            self._control.clear()
            self._show_prompt()
            if keep_input:
                self.input_buffer = input_buffer

    def copy(self):
        """ Copy the currently selected text to the clipboard.
        """
        self.layout().currentWidget().copy()

    def copy_anchor(self, anchor):
        """ Copy anchor text to the clipboard
        """
        QtGui.QApplication.clipboard().setText(anchor)

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
                self._input_buffer_executing = self.input_buffer
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

    def export_html(self):
        """ Shows a dialog to export HTML/XML in various formats.
        """
        self._html_exporter.export()

    def _get_input_buffer(self, force=False):
        """ The text that the user has entered entered at the current prompt.

        If the console is currently executing, the text that is executing will
        always be returned.
        """
        # If we're executing, the input buffer may not even exist anymore due to
        # the limit imposed by 'buffer_size'. Therefore, we store it.
        if self._executing and not force:
            return self._input_buffer_executing

        cursor = self._get_end_cursor()
        cursor.setPosition(self._prompt_pos, QtGui.QTextCursor.KeepAnchor)
        input_buffer = cursor.selection().toPlainText()

        # Strip out continuation prompts.
        return input_buffer.replace('\n' + self._continuation_prompt, '\n')

    def _set_input_buffer(self, string):
        """ Sets the text in the input buffer.

        If the console is currently executing, this call has no *immediate*
        effect. When the execution is finished, the input buffer will be updated
        appropriately.
        """
        # If we're executing, store the text for later.
        if self._executing:
            self._input_buffer_pending = string
            return

        # Remove old text.
        cursor = self._get_end_cursor()
        cursor.beginEditBlock()
        cursor.setPosition(self._prompt_pos, QtGui.QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

        # Insert new text with continuation prompts.
        self._insert_plain_text_into_buffer(self._get_prompt_cursor(), string)
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

        self.font_changed.emit(font)

    font = property(_get_font, _set_font)

    def open_anchor(self, anchor):
        """ Open selected anchor in the default webbrowser
        """
        webbrowser.open( anchor )

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
            # Make sure the paste is safe.
            self._keep_cursor_in_buffer()
            cursor = self._control.textCursor()

            # Remove any trailing newline, which confuses the GUI and forces the
            # user to backspace.
            text = QtGui.QApplication.clipboard().text(mode).rstrip()
            self._insert_plain_text_into_buffer(cursor, dedent(text))

    def print_(self, printer = None):
        """ Print the contents of the ConsoleWidget to the specified QPrinter.
        """
        if (not printer):
            printer = QtGui.QPrinter()
            if(QtGui.QPrintDialog(printer).exec_() != QtGui.QDialog.Accepted):
                return
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
            fallback = 'Courier'
        elif sys.platform == 'darwin':
            # OSX always has Monaco
            fallback = 'Monaco'
        else:
            # Monospace should always exist
            fallback = 'Monospace'
        font = get_font(self.font_family, fallback)
        if self.font_size:
            font.setPointSize(self.font_size)
        else:
            font.setPointSize(QtGui.qApp.font().pointSize())
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self._set_font(font)

    def change_font_size(self, delta):
        """Change the font size by the specified amount (in points).
        """
        font = self.font
        size = max(font.pointSize() + delta, 1) # minimum 1 point
        font.setPointSize(size)
        self._set_font(font)

    def _increase_font_size(self):
        self.change_font_size(1)

    def _decrease_font_size(self):
        self.change_font_size(-1)

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

    def _up_pressed(self, shift_modifier):
        """ Called when the up key is pressed. Returns whether to continue
            processing the event.
        """
        return True

    def _down_pressed(self, shift_modifier):
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

    def _append_custom(self, insert, input, before_prompt=False):
        """ A low-level method for appending content to the end of the buffer.

        If 'before_prompt' is enabled, the content will be inserted before the
        current prompt, if there is one.
        """
        # Determine where to insert the content.
        cursor = self._control.textCursor()
        if before_prompt and (self._reading or not self._executing):
            cursor.setPosition(self._append_before_prompt_pos)
        else:
            cursor.movePosition(QtGui.QTextCursor.End)
        start_pos = cursor.position()

        # Perform the insertion.
        result = insert(cursor, input)

        # Adjust the prompt position if we have inserted before it. This is safe
        # because buffer truncation is disabled when not executing.
        if before_prompt and not self._executing:
            diff = cursor.position() - start_pos
            self._append_before_prompt_pos += diff
            self._prompt_pos += diff

        return result

    def _append_block(self, block_format=None, before_prompt=False):
        """ Appends an new QTextBlock to the end of the console buffer.
        """
        self._append_custom(self._insert_block, block_format, before_prompt)

    def _append_html(self, html, before_prompt=False):
        """ Appends HTML at the end of the console buffer.
        """
        self._append_custom(self._insert_html, html, before_prompt)

    def _append_html_fetching_plain_text(self, html, before_prompt=False):
        """ Appends HTML, then returns the plain text version of it.
        """
        return self._append_custom(self._insert_html_fetching_plain_text,
                                   html, before_prompt)

    def _append_plain_text(self, text, before_prompt=False):
        """ Appends plain text, processing ANSI codes if enabled.
        """
        self._append_custom(self._insert_plain_text, text, before_prompt)

    def _cancel_completion(self):
        """ If text completion is progress, cancel it.
        """
        self._completion_widget.cancel_completion()

    def _clear_temporary_buffer(self):
        """ Clears the "temporary text" buffer, i.e. all the text following
            the prompt region.
        """
        # Select and remove all text below the input buffer.
        cursor = self._get_prompt_cursor()
        prompt = self._continuation_prompt.lstrip()
        if(self._temp_buffer_filled):
            self._temp_buffer_filled = False
            while cursor.movePosition(QtGui.QTextCursor.NextBlock):
                temp_cursor = QtGui.QTextCursor(cursor)
                temp_cursor.select(QtGui.QTextCursor.BlockUnderCursor)
                text = temp_cursor.selection().toPlainText().lstrip()
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
        self._cancel_completion()

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

            cursor.movePosition(QtGui.QTextCursor.Left, n=len(prefix))
            self._completion_widget.show_items(cursor, items)


    def _fill_temporary_buffer(self, cursor, text, html=False):
        """fill the area below the active editting zone with text"""

        current_pos = self._control.textCursor().position()

        cursor.beginEditBlock()
        self._append_plain_text('\n')
        self._page(text, html=html)
        cursor.endEditBlock()

        cursor.setPosition(current_pos)
        self._control.moveCursor(QtGui.QTextCursor.End)
        self._control.setTextCursor(cursor)

        self._temp_buffer_filled = True


    def _context_menu_make(self, pos):
        """ Creates a context menu for the given QPoint (in widget coordinates).
        """
        menu = QtGui.QMenu(self)

        self.cut_action = menu.addAction('Cut', self.cut)
        self.cut_action.setEnabled(self.can_cut())
        self.cut_action.setShortcut(QtGui.QKeySequence.Cut)

        self.copy_action = menu.addAction('Copy', self.copy)
        self.copy_action.setEnabled(self.can_copy())
        self.copy_action.setShortcut(QtGui.QKeySequence.Copy)

        self.paste_action = menu.addAction('Paste', self.paste)
        self.paste_action.setEnabled(self.can_paste())
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)

        anchor = self._control.anchorAt(pos)
        if anchor:
            menu.addSeparator()
            self.copy_link_action = menu.addAction(
                'Copy Link Address', lambda: self.copy_anchor(anchor=anchor))
            self.open_link_action = menu.addAction(
                'Open Link', lambda: self.open_anchor(anchor=anchor))

        menu.addSeparator()
        menu.addAction(self.select_all_action)

        menu.addSeparator()
        menu.addAction(self.export_action)
        menu.addAction(self.print_action)

        return menu

    def _control_key_down(self, modifiers, include_command=False):
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
        if self.custom_control:
            control = self.custom_control()
        elif self.kind == 'plain':
            control = QtGui.QPlainTextEdit()
        elif self.kind == 'rich':
            control = QtGui.QTextEdit()
            control.setAcceptRichText(False)
            control.setMouseTracking(True)

        # Prevent the widget from handling drops, as we already provide
        # the logic in this class.
        control.setAcceptDrops(False)

        # Install event filters. The filter on the viewport is needed for
        # mouse events.
        control.installEventFilter(self)
        control.viewport().installEventFilter(self)

        # Connect signals.
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
        control.setAttribute(QtCore.Qt.WA_InputMethodEnabled, True)
        control.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        control.setReadOnly(True)
        control.setUndoRedoEnabled(False)
        control.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        return control

    def _create_page_control(self):
        """ Creates and connects the underlying paging widget.
        """
        if self.custom_page_control:
            control = self.custom_page_control()
        elif self.kind == 'plain':
            control = QtGui.QPlainTextEdit()
        elif self.kind == 'rich':
            control = QtGui.QTextEdit()
        control.installEventFilter(self)
        viewport = control.viewport()
        viewport.installEventFilter(self)
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
            self._cancel_completion()

            if self._in_buffer(position):
                # Special handling when a reading a line of raw input.
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
                    at_end = len(cursor.selectedText().strip()) == 0
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
                    cursor.clearSelection()
                    cursor.movePosition(QtGui.QTextCursor.EndOfLine,
                                        QtGui.QTextCursor.KeepAnchor)
                    if not cursor.hasSelection():
                        # Line deletion (remove continuation prompt)
                        cursor.movePosition(QtGui.QTextCursor.NextBlock,
                                            QtGui.QTextCursor.KeepAnchor)
                        cursor.movePosition(QtGui.QTextCursor.Right,
                                            QtGui.QTextCursor.KeepAnchor,
                                            len(self._continuation_prompt))
                    self._kill_ring.kill_cursor(cursor)
                    self._set_cursor(cursor)
                intercepted = True

            elif key == QtCore.Qt.Key_L:
                self.prompt_to_top()
                intercepted = True

            elif key == QtCore.Qt.Key_O:
                if self._page_control and self._page_control.isVisible():
                    self._page_control.setFocus()
                intercepted = True

            elif key == QtCore.Qt.Key_U:
                if self._in_buffer(position):
                    cursor.clearSelection()
                    start_line = cursor.blockNumber()
                    if start_line == self._get_prompt_cursor().blockNumber():
                        offset = len(self._prompt)
                    else:
                        offset = len(self._continuation_prompt)
                    cursor.movePosition(QtGui.QTextCursor.StartOfBlock,
                                        QtGui.QTextCursor.KeepAnchor)
                    cursor.movePosition(QtGui.QTextCursor.Right,
                                        QtGui.QTextCursor.KeepAnchor, offset)
                    self._kill_ring.kill_cursor(cursor)
                    self._set_cursor(cursor)
                intercepted = True

            elif key == QtCore.Qt.Key_Y:
                self._keep_cursor_in_buffer()
                self._kill_ring.yank()
                intercepted = True

            elif key in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete):
                if key == QtCore.Qt.Key_Backspace:
                    cursor = self._get_word_start_cursor(position)
                else: # key == QtCore.Qt.Key_Delete
                    cursor = self._get_word_end_cursor(position)
                cursor.setPosition(position, QtGui.QTextCursor.KeepAnchor)
                self._kill_ring.kill_cursor(cursor)
                intercepted = True

            elif key == QtCore.Qt.Key_D:
                if len(self.input_buffer) == 0:
                    self.exit_requested.emit(self)
                else:
                    new_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress,
                                                QtCore.Qt.Key_Delete,
                                                QtCore.Qt.NoModifier)
                    QtGui.qApp.sendEvent(self._control, new_event)
                    intercepted = True

        #------ Alt modifier ---------------------------------------------------

        elif alt_down:
            if key == QtCore.Qt.Key_B:
                self._set_cursor(self._get_word_start_cursor(position))
                intercepted = True

            elif key == QtCore.Qt.Key_F:
                self._set_cursor(self._get_word_end_cursor(position))
                intercepted = True

            elif key == QtCore.Qt.Key_Y:
                self._kill_ring.rotate()
                intercepted = True

            elif key == QtCore.Qt.Key_Backspace:
                cursor = self._get_word_start_cursor(position)
                cursor.setPosition(position, QtGui.QTextCursor.KeepAnchor)
                self._kill_ring.kill_cursor(cursor)
                intercepted = True

            elif key == QtCore.Qt.Key_D:
                cursor = self._get_word_end_cursor(position)
                cursor.setPosition(position, QtGui.QTextCursor.KeepAnchor)
                self._kill_ring.kill_cursor(cursor)
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
            if shift_down:
                anchormode = QtGui.QTextCursor.KeepAnchor
            else:
                anchormode = QtGui.QTextCursor.MoveAnchor

            if key == QtCore.Qt.Key_Escape:
                self._keyboard_quit()
                intercepted = True

            elif key == QtCore.Qt.Key_Up:
                if self._reading or not self._up_pressed(shift_down):
                    intercepted = True
                else:
                    prompt_line = self._get_prompt_cursor().blockNumber()
                    intercepted = cursor.blockNumber() <= prompt_line

            elif key == QtCore.Qt.Key_Down:
                if self._reading or not self._down_pressed(shift_down):
                    intercepted = True
                else:
                    end_line = self._get_end_cursor().blockNumber()
                    intercepted = cursor.blockNumber() == end_line

            elif key == QtCore.Qt.Key_Tab:
                if not self._reading:
                    if self._tab_pressed():
                        # real tab-key, insert four spaces
                        cursor.insertText(' '*4)
                    intercepted = True

            elif key == QtCore.Qt.Key_Left:

                # Move to the previous line
                line, col = cursor.blockNumber(), cursor.columnNumber()
                if line > self._get_prompt_cursor().blockNumber() and \
                        col == len(self._continuation_prompt):
                    self._control.moveCursor(QtGui.QTextCursor.PreviousBlock,
                                             mode=anchormode)
                    self._control.moveCursor(QtGui.QTextCursor.EndOfBlock,
                                             mode=anchormode)
                    intercepted = True

                # Regular left movement
                else:
                    intercepted = not self._in_buffer(position - 1)

            elif key == QtCore.Qt.Key_Right:
                original_block_number = cursor.blockNumber()
                cursor.movePosition(QtGui.QTextCursor.Right,
                                mode=anchormode)
                if cursor.blockNumber() != original_block_number:
                    cursor.movePosition(QtGui.QTextCursor.Right,
                                        n=len(self._continuation_prompt),
                                        mode=anchormode)
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

        # Don't move the cursor if Control/Cmd is pressed to allow copy-paste
        # using the keyboard in any part of the buffer. Also, permit scrolling
        # with Page Up/Down keys. Finally, if we're executing, don't move the
        # cursor (if even this made sense, we can't guarantee that the prompt
        # position is still valid due to text truncation).
        if not (self._control_key_down(event.modifiers(), include_command=True)
                or key in (QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown)
                or (self._executing and not self._reading)):
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
                self._control.setFocus()
            else:
                self.layout().setCurrentWidget(self._control)
            return True

        elif key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return,
                     QtCore.Qt.Key_Tab):
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
        # Calculate the number of characters available.
        width = self._control.viewport().width()
        char_width = QtGui.QFontMetrics(self.font).width(' ')
        displaywidth = max(10, (width / char_width) - 1)

        return columnize(items, separator, displaywidth)

    def _get_block_plain_text(self, block):
        """ Given a QTextBlock, return its unformatted text.
        """
        cursor = QtGui.QTextCursor(block)
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock,
                            QtGui.QTextCursor.KeepAnchor)
        return cursor.selection().toPlainText()

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
        """ Returns the text of the line of the input buffer that contains the
            cursor, or None if there is no such line.
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
                  not is_letter_or_number(document.characterAt(position)):
            position -= 1
        while position >= self._prompt_pos and \
                  is_letter_or_number(document.characterAt(position)):
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
                  not is_letter_or_number(document.characterAt(position)):
            position += 1
        while position < end and \
                  is_letter_or_number(document.characterAt(position)):
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

    def _insert_block(self, cursor, block_format=None):
        """ Inserts an empty QTextBlock using the specified cursor.
        """
        if block_format is None:
            block_format = QtGui.QTextBlockFormat()
        cursor.insertBlock(block_format)

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
        text = cursor.selection().toPlainText()

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

                    elif act.action == 'carriage-return':
                        cursor.movePosition(
                            cursor.StartOfLine, cursor.KeepAnchor)

                    elif act.action == 'beep':
                        QtGui.qApp.beep()

                    elif act.action == 'backspace':
                        if not cursor.atBlockStart():
                            cursor.movePosition(
                                cursor.PreviousCharacter, cursor.KeepAnchor)

                    elif act.action == 'newline':
                        cursor.movePosition(cursor.EndOfLine)

                format = self._ansi_processor.get_format()

                selection = cursor.selectedText()
                if len(selection) == 0:
                    cursor.insertText(substring, format)
                elif substring is not None:
                    # BS and CR are treated as a change in print
                    # position, rather than a backwards character
                    # deletion for output equivalence with (I)Python
                    # terminal.
                    if len(substring) >= len(selection):
                        cursor.insertText(substring, format)
                    else:
                        old_text = selection[len(substring):]
                        cursor.insertText(substring + old_text, format)
                        cursor.movePosition(cursor.PreviousCharacter,
                               cursor.KeepAnchor, len(old_text))
        else:
            cursor.insertText(text)
        cursor.endEditBlock()

    def _insert_plain_text_into_buffer(self, cursor, text):
        """ Inserts text into the input buffer using the specified cursor (which
            must be in the input buffer), ensuring that continuation prompts are
            inserted as necessary.
        """
        lines = text.splitlines(True)
        if lines:
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
        if self._temp_buffer_filled :
            self._cancel_completion()
            self._clear_temporary_buffer()
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
            self._append_html(text)
        else:
            self._append_plain_text(text)

    def _set_paging(self, paging):
        """
        Change the pager to `paging` style.

        XXX: currently, this is limited to switching between 'hsplit' and
        'vsplit'.

        Parameters:
        -----------
        paging : string
            Either "hsplit", "vsplit", or "inside"
        """
        if self._splitter is None:
            raise NotImplementedError("""can only switch if --paging=hsplit or
                    --paging=vsplit is used.""")
        if paging == 'hsplit':
            self._splitter.setOrientation(QtCore.Qt.Horizontal)
        elif paging == 'vsplit':
            self._splitter.setOrientation(QtCore.Qt.Vertical)
        elif paging == 'inside':
            raise NotImplementedError("""switching to 'inside' paging not
                    supported yet.""")
        else:
            raise ValueError("unknown paging method '%s'" % paging)
        self.paging = paging

    def _prompt_finished(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        self._control.setReadOnly(True)
        self._prompt_finished_hook()

    def _prompt_started(self):
        """ Called immediately after a new prompt is displayed.
        """
        # Temporarily disable the maximum block count to permit undo/redo and
        # to ensure that the prompt position does not change due to truncation.
        self._control.document().setMaximumBlockCount(0)
        self._control.setUndoRedoEnabled(True)

        # Work around bug in QPlainTextEdit: input method is not re-enabled
        # when read-only is disabled.
        self._control.setReadOnly(False)
        self._control.setAttribute(QtCore.Qt.WA_InputMethodEnabled, True)

        if not self._reading:
            self._executing = False
        self._prompt_started_hook()

        # If the input buffer has changed while executing, load it.
        if self._input_buffer_pending:
            self.input_buffer = self._input_buffer_pending
            self._input_buffer_pending = ''

        self._control.moveCursor(QtGui.QTextCursor.End)

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
            return self._get_input_buffer(force=True).rstrip('\n')

        else:
            self._reading_callback = lambda: \
                callback(self._get_input_buffer(force=True).rstrip('\n'))

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
        # Save the current end position to support _append*(before_prompt=True).
        cursor = self._get_end_cursor()
        self._append_before_prompt_pos = cursor.position()

        # Insert a preliminary newline, if necessary.
        if newline and cursor.position() > 0:
            cursor.movePosition(QtGui.QTextCursor.Left,
                                QtGui.QTextCursor.KeepAnchor)
            if cursor.selection().toPlainText() != '\n':
                self._append_block()

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

    def _custom_context_menu_requested(self, pos):
        """ Shows a context menu at the given QPoint (in widget coordinates).
        """
        menu = self._context_menu_make(pos)
        menu.exec_(self._control.mapToGlobal(pos))

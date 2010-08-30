# Standard library imports
import signal
import sys

# System library imports
from pygments.lexers import PythonLexer
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.core.inputsplitter import InputSplitter
from IPython.frontend.qt.base_frontend_mixin import BaseFrontendMixin
from IPython.utils.traitlets import Bool
from bracket_matcher import BracketMatcher
from call_tip_widget import CallTipWidget
from completion_lexer import CompletionLexer
from console_widget import HistoryConsoleWidget
from pygments_highlighter import PygmentsHighlighter


class FrontendHighlighter(PygmentsHighlighter):
    """ A PygmentsHighlighter that can be turned on and off and that ignores
        prompts.
    """

    def __init__(self, frontend):
        super(FrontendHighlighter, self).__init__(frontend._control.document())
        self._current_offset = 0
        self._frontend = frontend
        self.highlighting_on = False

    def highlightBlock(self, qstring):
        """ Highlight a block of text. Reimplemented to highlight selectively.
        """
        if not self.highlighting_on:
            return

        # The input to this function is unicode string that may contain
        # paragraph break characters, non-breaking spaces, etc. Here we acquire
        # the string as plain text so we can compare it.
        current_block = self.currentBlock()
        string = self._frontend._get_block_plain_text(current_block)

        # Decide whether to check for the regular or continuation prompt.
        if current_block.contains(self._frontend._prompt_pos):
            prompt = self._frontend._prompt
        else:
            prompt = self._frontend._continuation_prompt

        # Don't highlight the part of the string that contains the prompt.
        if string.startswith(prompt):
            self._current_offset = len(prompt)
            qstring.remove(0, len(prompt))
        else:
            self._current_offset = 0

        PygmentsHighlighter.highlightBlock(self, qstring)

    def rehighlightBlock(self, block):
        """ Reimplemented to temporarily enable highlighting if disabled.
        """
        old = self.highlighting_on
        self.highlighting_on = True
        super(FrontendHighlighter, self).rehighlightBlock(block)
        self.highlighting_on = old

    def setFormat(self, start, count, format):
        """ Reimplemented to highlight selectively.
        """
        start += self._current_offset
        PygmentsHighlighter.setFormat(self, start, count, format)


class FrontendWidget(HistoryConsoleWidget, BaseFrontendMixin):
    """ A Qt frontend for a generic Python kernel.
    """

    # An option and corresponding signal for overriding the default kernel
    # interrupt behavior.
    custom_interrupt = Bool(False)
    custom_interrupt_requested = QtCore.pyqtSignal()

    # An option and corresponding signal for overriding the default kernel
    # restart behavior.
    custom_restart = Bool(False)
    custom_restart_requested = QtCore.pyqtSignal()
   
    # Emitted when an 'execute_reply' has been received from the kernel and
    # processed by the FrontendWidget.
    executed = QtCore.pyqtSignal(object)
    
    # Protected class variables.
    _input_splitter_class = InputSplitter

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, *args, **kw):
        super(FrontendWidget, self).__init__(*args, **kw)

        # FrontendWidget protected variables.
        self._bracket_matcher = BracketMatcher(self._control)
        self._call_tip_widget = CallTipWidget(self._control)
        self._completion_lexer = CompletionLexer(PythonLexer())
        self._hidden = False
        self._highlighter = FrontendHighlighter(self)
        self._input_splitter = self._input_splitter_class(input_mode='block')
        self._kernel_manager = None

        # Configure the ConsoleWidget.
        self.tab_width = 4
        self._set_continuation_prompt('... ')

        # Connect signal handlers.
        document = self._control.document()
        document.contentsChange.connect(self._document_contents_change)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _is_complete(self, source, interactive):
        """ Returns whether 'source' can be completely processed and a new
            prompt created. When triggered by an Enter/Return key press,
            'interactive' is True; otherwise, it is False.
        """
        complete = self._input_splitter.push(source.expandtabs(4))
        if interactive:
            complete = not self._input_splitter.push_accepts_more()
        return complete

    def _execute(self, source, hidden):
        """ Execute 'source'. If 'hidden', do not show any output.
        """
        self.kernel_manager.xreq_channel.execute(source, hidden)
        self._hidden = hidden
        
    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        """
        if not self._reading:
            self._highlighter.highlighting_on = True

    def _prompt_finished_hook(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        if not self._reading:
            self._highlighter.highlighting_on = False

    def _tab_pressed(self):
        """ Called when the tab key is pressed. Returns whether to continue
            processing the event.
        """
        # Perform tab completion if:
        # 1) The cursor is in the input buffer.
        # 2) There is a non-whitespace character before the cursor.
        text = self._get_input_buffer_cursor_line()
        if text is None:
            return False
        complete = bool(text[:self._get_input_buffer_cursor_column()].strip())
        if complete:
            self._complete()
        return not complete

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _event_filter_console_keypress(self, event):
        """ Reimplemented to allow execution interruption.
        """
        key = event.key()
        if self._executing and self._control_key_down(event.modifiers()):
            if key == QtCore.Qt.Key_C:
                self._kernel_interrupt()
                return True
            elif key == QtCore.Qt.Key_Period:
                self._kernel_restart()
                return True
        return super(FrontendWidget, self)._event_filter_console_keypress(event)

    def _insert_continuation_prompt(self, cursor):
        """ Reimplemented for auto-indentation.
        """
        super(FrontendWidget, self)._insert_continuation_prompt(cursor)
        spaces = self._input_splitter.indent_spaces
        cursor.insertText('\t' * (spaces / self.tab_width))
        cursor.insertText(' ' * (spaces % self.tab_width))

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_complete_reply(self, rep):
        """ Handle replies for tab completion.
        """
        cursor = self._get_cursor()
        if rep['parent_header']['msg_id'] == self._complete_id and \
                cursor.position() == self._complete_pos:
            text = '.'.join(self._get_context())
            cursor.movePosition(QtGui.QTextCursor.Left, n=len(text))
            self._complete_with_items(cursor, rep['content']['matches'])

    def _handle_execute_reply(self, msg):
        """ Handles replies for code execution.
        """
        if not self._hidden:
            # Make sure that all output from the SUB channel has been processed
            # before writing a new prompt.
            self.kernel_manager.sub_channel.flush()

            content = msg['content']
            status = content['status']
            if status == 'ok':
                self._process_execute_ok(msg)
            elif status == 'error':
                self._process_execute_error(msg)
            elif status == 'abort':
                self._process_execute_abort(msg)

            self._show_interpreter_prompt_for_reply(msg)
            self.executed.emit(msg)

    def _handle_input_request(self, msg):
        """ Handle requests for raw_input.
        """
        if self._hidden:
            raise RuntimeError('Request for raw input during hidden execution.')

        # Make sure that all output from the SUB channel has been processed
        # before entering readline mode.
        self.kernel_manager.sub_channel.flush()

        def callback(line):
            self.kernel_manager.rep_channel.input(line)
        self._readline(msg['content']['prompt'], callback=callback)

    def _handle_object_info_reply(self, rep):
        """ Handle replies for call tips.
        """
        cursor = self._get_cursor()
        if rep['parent_header']['msg_id'] == self._call_tip_id and \
                cursor.position() == self._call_tip_pos:
            doc = rep['content']['docstring']
            if doc:
                self._call_tip_widget.show_docstring(doc)

    def _handle_pyout(self, msg):
        """ Handle display hook output.
        """
        if not self._hidden and self._is_from_this_session(msg):
            self._append_plain_text(msg['content']['data'] + '\n')

    def _handle_stream(self, msg):
        """ Handle stdout, stderr, and stdin.
        """
        if not self._hidden and self._is_from_this_session(msg):
            self._append_plain_text(msg['content']['data'])
            self._control.moveCursor(QtGui.QTextCursor.End)
    
    def _started_channels(self):
        """ Called when the KernelManager channels have started listening or 
            when the frontend is assigned an already listening KernelManager.
        """
        self._control.clear()
        self._append_plain_text(self._get_banner())
        self._show_interpreter_prompt()

    def _stopped_channels(self):
        """ Called when the KernelManager channels have stopped listening or
            when a listening KernelManager is removed from the frontend.
        """
        self._executing = self._reading = False
        self._highlighter.highlighting_on = False

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------

    def execute_file(self, path, hidden=False):
        """ Attempts to execute file with 'path'. If 'hidden', no output is
            shown.
        """
        self.execute('execfile("%s")' % path, hidden=hidden)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _call_tip(self):
        """ Shows a call tip, if appropriate, at the current cursor location.
        """
        # Decide if it makes sense to show a call tip
        cursor = self._get_cursor()
        cursor.movePosition(QtGui.QTextCursor.Left)
        if cursor.document().characterAt(cursor.position()).toAscii() != '(':
            return False
        context = self._get_context(cursor)
        if not context:
            return False

        # Send the metadata request to the kernel
        name = '.'.join(context)
        self._call_tip_id = self.kernel_manager.xreq_channel.object_info(name)
        self._call_tip_pos = self._get_cursor().position()
        return True

    def _complete(self):
        """ Performs completion at the current cursor location.
        """
        context = self._get_context()
        if context:
            # Send the completion request to the kernel
            self._complete_id = self.kernel_manager.xreq_channel.complete(
                '.'.join(context),                       # text
                self._get_input_buffer_cursor_line(),    # line
                self._get_input_buffer_cursor_column(),  # cursor_pos
                self.input_buffer)                       # block 
            self._complete_pos = self._get_cursor().position()

    def _get_banner(self):
        """ Gets a banner to display at the beginning of a session.
        """
        banner = 'Python %s on %s\nType "help", "copyright", "credits" or ' \
            '"license" for more information.'
        return banner % (sys.version, sys.platform)

    def _get_context(self, cursor=None):
        """ Gets the context for the specified cursor (or the current cursor
            if none is specified).
        """
        if cursor is None:
            cursor = self._get_cursor()
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock, 
                            QtGui.QTextCursor.KeepAnchor)
        text = str(cursor.selection().toPlainText())
        return self._completion_lexer.get_context(text)

    def _kernel_interrupt(self):
        """ Attempts to interrupt the running kernel.
        """
        if self.custom_interrupt:
            self.custom_interrupt_requested.emit()
        elif self.kernel_manager.has_kernel:
            self.kernel_manager.signal_kernel(signal.SIGINT)
        else:
            self._append_plain_text('Kernel process is either remote or '
                                    'unspecified. Cannot interrupt.\n')

    def _kernel_restart(self):
        """ Attempts to restart the running kernel.
        """
        if self.custom_restart:
            self.custom_restart_requested.emit()
        elif self.kernel_manager.has_kernel:
            try:
                self.kernel_manager.restart_kernel()
            except RuntimeError:
                message = 'Kernel started externally. Cannot restart.\n'
                self._append_plain_text(message)
            else:
                self._stopped_channels()
                self._append_plain_text('Kernel restarting...\n')
                self._show_interpreter_prompt()
        else:
            self._append_plain_text('Kernel process is either remote or '
                                    'unspecified. Cannot restart.\n')

    def _process_execute_abort(self, msg):
        """ Process a reply for an aborted execution request.
        """
        self._append_plain_text("ERROR: execution aborted\n")

    def _process_execute_error(self, msg):
        """ Process a reply for an execution request that resulted in an error.
        """
        content = msg['content']
        traceback = ''.join(content['traceback'])
        self._append_plain_text(traceback)

    def _process_execute_ok(self, msg):
        """ Process a reply for a successful execution equest.
        """
        payload = msg['content']['payload']
        for item in payload:
            if not self._process_execute_payload(item):
                warning = 'Received unknown payload of type %s\n'
                self._append_plain_text(warning % repr(item['source']))

    def _process_execute_payload(self, item):
        """ Process a single payload item from the list of payload items in an
            execution reply. Returns whether the payload was handled.
        """
        # The basic FrontendWidget doesn't handle payloads, as they are a
        # mechanism for going beyond the standard Python interpreter model.
        return False

    def _show_interpreter_prompt(self):
        """ Shows a prompt for the interpreter.
        """
        self._show_prompt('>>> ')

    def _show_interpreter_prompt_for_reply(self, msg):
        """ Shows a prompt for the interpreter given an 'execute_reply' message.
        """
        self._show_interpreter_prompt()

    #------ Signal handlers ----------------------------------------------------

    def _document_contents_change(self, position, removed, added):
        """ Called whenever the document's content changes. Display a call tip
            if appropriate.
        """
        # Calculate where the cursor should be *after* the change:
        position += added

        document = self._control.document()
        if position == self._get_cursor().position():
            self._call_tip()

# Standard library imports
import signal
import sys

# System library imports
from pygments.lexers import PythonLexer
from PyQt4 import QtCore, QtGui
import zmq

# Local imports
from IPython.core.inputsplitter import InputSplitter
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

    def setFormat(self, start, count, format):
        """ Reimplemented to highlight selectively.
        """
        start += self._current_offset
        PygmentsHighlighter.setFormat(self, start, count, format)


class FrontendWidget(HistoryConsoleWidget):
    """ A Qt frontend for a generic Python kernel.
    """
   
    # Emitted when an 'execute_reply' is received from the kernel.
    executed = QtCore.pyqtSignal(object)

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, *args, **kw):
        super(FrontendWidget, self).__init__(*args, **kw)

        # FrontendWidget protected variables.
        self._call_tip_widget = CallTipWidget(self._control)
        self._completion_lexer = CompletionLexer(PythonLexer())
        self._hidden = True
        self._highlighter = FrontendHighlighter(self)
        self._input_splitter = InputSplitter(input_mode='replace')
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
        self.kernel_manager.xreq_channel.execute(source)
        self._hidden = hidden

    def _execute_interrupt(self):
        """ Attempts to stop execution. Returns whether this method has an
            implementation.
        """
        self._interrupt_kernel()
        return True
        
    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        """
        if not self._reading:
            self._highlighter.highlighting_on = True

            # Auto-indent if this is a continuation prompt.
            if self._get_prompt_cursor().blockNumber() != \
                    self._get_end_cursor().blockNumber():
                spaces = self._input_splitter.indent_spaces
                self._append_plain_text('\t' * (spaces / self.tab_width))
                self._append_plain_text(' ' * (spaces % self.tab_width))

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
        self._keep_cursor_in_buffer()
        cursor = self._get_cursor()
        return not self._complete()

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------

    def execute_file(self, path, hidden=False):
        """ Attempts to execute file with 'path'. If 'hidden', no output is
            shown.
        """
        self.execute('execfile("%s")' % path, hidden=hidden)

    def _get_kernel_manager(self):
        """ Returns the current kernel manager.
        """
        return self._kernel_manager

    def _set_kernel_manager(self, kernel_manager):
        """ Disconnect from the current kernel manager (if any) and set a new
            kernel manager.
        """
        # Disconnect the old kernel manager, if necessary.
        if self._kernel_manager is not None:
            self._kernel_manager.started_channels.disconnect(
                self._started_channels)
            self._kernel_manager.stopped_channels.disconnect(
                self._stopped_channels)

            # Disconnect the old kernel manager's channels.
            sub = self._kernel_manager.sub_channel
            xreq = self._kernel_manager.xreq_channel
            rep = self._kernel_manager.rep_channel
            sub.message_received.disconnect(self._handle_sub)
            xreq.execute_reply.disconnect(self._handle_execute_reply)
            xreq.complete_reply.disconnect(self._handle_complete_reply)
            xreq.object_info_reply.disconnect(self._handle_object_info_reply)
            rep.input_requested.disconnect(self._handle_req)

            # Handle the case where the old kernel manager is still listening.
            if self._kernel_manager.channels_running:
                self._stopped_channels()

        # Set the new kernel manager.
        self._kernel_manager = kernel_manager
        if kernel_manager is None:
            return

        # Connect the new kernel manager.
        kernel_manager.started_channels.connect(self._started_channels)
        kernel_manager.stopped_channels.connect(self._stopped_channels)

        # Connect the new kernel manager's channels.
        sub = kernel_manager.sub_channel
        xreq = kernel_manager.xreq_channel
        rep = kernel_manager.rep_channel
        sub.message_received.connect(self._handle_sub)
        xreq.execute_reply.connect(self._handle_execute_reply)
        xreq.complete_reply.connect(self._handle_complete_reply)
        xreq.object_info_reply.connect(self._handle_object_info_reply)
        rep.input_requested.connect(self._handle_req)
        
        # Handle the case where the kernel manager started channels before
        # we connected.
        if kernel_manager.channels_running:
            self._started_channels()

    kernel_manager = property(_get_kernel_manager, _set_kernel_manager)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _call_tip(self):
        """ Shows a call tip, if appropriate, at the current cursor location.
        """
        # Decide if it makes sense to show a call tip
        cursor = self._get_cursor()
        cursor.movePosition(QtGui.QTextCursor.Left)
        document = self._control.document()
        if document.characterAt(cursor.position()).toAscii() != '(':
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
        # Decide if it makes sense to do completion
        context = self._get_context()
        if not context:
            return False

        # Send the completion request to the kernel
        text = '.'.join(context)
        self._complete_id = self.kernel_manager.xreq_channel.complete(
            text, self._get_input_buffer_cursor_line(), self.input_buffer)
        self._complete_pos = self._get_cursor().position()
        return True

    def _get_banner(self):
        """ Gets a banner to display at the beginning of a session.
        """
        banner = 'Python %s on %s\nType "help", "copyright", "credits" or ' \
            '"license" for more information.'
        return banner % (sys.version, sys.platform)

    def _get_context(self, cursor=None):
        """ Gets the context at the current cursor location.
        """
        if cursor is None:
            cursor = self._get_cursor()
        cursor.movePosition(QtGui.QTextCursor.StartOfLine, 
                            QtGui.QTextCursor.KeepAnchor)
        text = str(cursor.selection().toPlainText())
        return self._completion_lexer.get_context(text)

    def _interrupt_kernel(self):
        """ Attempts to the interrupt the kernel.
        """
        if self.kernel_manager.has_kernel:
            self.kernel_manager.signal_kernel(signal.SIGINT)
        else:
            self._append_plain_text('Kernel process is either remote or '
                                    'unspecified. Cannot interrupt.\n')

    def _show_interpreter_prompt(self):
        """ Shows a prompt for the interpreter.
        """
        self._show_prompt('>>> ')

    #------ Signal handlers ----------------------------------------------------

    def _started_channels(self):
        """ Called when the kernel manager has started listening.
        """
        self._reset()
        self._append_plain_text(self._get_banner())
        self._show_interpreter_prompt()

    def _stopped_channels(self):
        """ Called when the kernel manager has stopped listening.
        """
        # FIXME: Print a message here?
        pass

    def _document_contents_change(self, position, removed, added):
        """ Called whenever the document's content changes. Display a call tip
            if appropriate.
        """
        # Calculate where the cursor should be *after* the change:
        position += added

        document = self._control.document()
        if position == self._get_cursor().position():
            self._call_tip()

    def _handle_req(self, req):
        # Make sure that all output from the SUB channel has been processed
        # before entering readline mode.
        self.kernel_manager.sub_channel.flush()

        def callback(line):
            self.kernel_manager.rep_channel.input(line)
        self._readline(req['content']['prompt'], callback=callback)

    def _handle_sub(self, omsg):
        if self._hidden:
            return
        handler = getattr(self, '_handle_%s' % omsg['msg_type'], None)
        if handler is not None:
            handler(omsg)

    def _handle_pyout(self, omsg):
        self._append_plain_text(omsg['content']['data'] + '\n')

    def _handle_stream(self, omsg):
        self._append_plain_text(omsg['content']['data'])
        self._control.moveCursor(QtGui.QTextCursor.End)
        
    def _handle_execute_reply(self, reply):
        if self._hidden:
            return

        # Make sure that all output from the SUB channel has been processed
        # before writing a new prompt.
        self.kernel_manager.sub_channel.flush()

        content = reply['content']
        status = content['status']
        if status == 'ok':
            self._handle_execute_payload(content['payload'])
        elif status == 'error':
            self._handle_execute_error(reply)
        elif status == 'aborted':
            text = "ERROR: ABORTED\n"
            self._append_plain_text(text)

        self._hidden = True
        self._show_interpreter_prompt()
        self.executed.emit(reply)

    def _handle_execute_error(self, reply):
        content = reply['content']
        traceback = ''.join(content['traceback'])
        self._append_plain_text(traceback)

    def _handle_execute_payload(self, payload):
        pass

    def _handle_complete_reply(self, rep):
        cursor = self._get_cursor()
        if rep['parent_header']['msg_id'] == self._complete_id and \
                cursor.position() == self._complete_pos:
            text = '.'.join(self._get_context())
            cursor.movePosition(QtGui.QTextCursor.Left, n=len(text))
            self._complete_with_items(cursor, rep['content']['matches'])

    def _handle_object_info_reply(self, rep):
        cursor = self._get_cursor()
        if rep['parent_header']['msg_id'] == self._call_tip_id and \
                cursor.position() == self._call_tip_pos:
            doc = rep['content']['docstring']
            if doc:
                self._call_tip_widget.show_docstring(doc)

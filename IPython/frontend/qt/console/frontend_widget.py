from __future__ import print_function

# Standard library imports
from collections import namedtuple
import sys
import time
import uuid

# System library imports
from pygments.lexers import PythonLexer
from IPython.external import qt
from IPython.external.qt import QtCore, QtGui

# Local imports
from IPython.core.inputsplitter import InputSplitter, IPythonInputSplitter
from IPython.core.inputtransformer import classic_prompt
from IPython.core.oinspect import call_tip
from IPython.frontend.qt.base_frontend_mixin import BaseFrontendMixin
from IPython.utils.traitlets import Bool, Instance, Unicode
from bracket_matcher import BracketMatcher
from call_tip_widget import CallTipWidget
from completion_lexer import CompletionLexer
from history_console_widget import HistoryConsoleWidget
from pygments_highlighter import PygmentsHighlighter


class FrontendHighlighter(PygmentsHighlighter):
    """ A PygmentsHighlighter that understands and ignores prompts.
    """

    def __init__(self, frontend):
        super(FrontendHighlighter, self).__init__(frontend._control.document())
        self._current_offset = 0
        self._frontend = frontend
        self.highlighting_on = False

    def highlightBlock(self, string):
        """ Highlight a block of text. Reimplemented to highlight selectively.
        """
        if not self.highlighting_on:
            return

        # The input to this function is a unicode string that may contain
        # paragraph break characters, non-breaking spaces, etc. Here we acquire
        # the string as plain text so we can compare it.
        current_block = self.currentBlock()
        string = self._frontend._get_block_plain_text(current_block)

        # Decide whether to check for the regular or continuation prompt.
        if current_block.contains(self._frontend._prompt_pos):
            prompt = self._frontend._prompt
        else:
            prompt = self._frontend._continuation_prompt

        # Only highlight if we can identify a prompt, but make sure not to
        # highlight the prompt.
        if string.startswith(prompt):
            self._current_offset = len(prompt)
            string = string[len(prompt):]
            super(FrontendHighlighter, self).highlightBlock(string)

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
        super(FrontendHighlighter, self).setFormat(start, count, format)


class FrontendWidget(HistoryConsoleWidget, BaseFrontendMixin):
    """ A Qt frontend for a generic Python kernel.
    """

    # The text to show when the kernel is (re)started.
    banner = Unicode()

    # An option and corresponding signal for overriding the default kernel
    # interrupt behavior.
    custom_interrupt = Bool(False)
    custom_interrupt_requested = QtCore.Signal()

    # An option and corresponding signals for overriding the default kernel
    # restart behavior.
    custom_restart = Bool(False)
    custom_restart_kernel_died = QtCore.Signal(float)
    custom_restart_requested = QtCore.Signal()

    # Whether to automatically show calltips on open-parentheses.
    enable_calltips = Bool(True, config=True,
        help="Whether to draw information calltips on open-parentheses.")

    clear_on_kernel_restart = Bool(True, config=True,
        help="Whether to clear the console when the kernel is restarted")

    confirm_restart = Bool(True, config=True,
        help="Whether to ask for user confirmation when restarting kernel")

    # Emitted when a user visible 'execute_request' has been submitted to the
    # kernel from the FrontendWidget. Contains the code to be executed.
    executing = QtCore.Signal(object)

    # Emitted when a user-visible 'execute_reply' has been received from the
    # kernel and processed by the FrontendWidget. Contains the response message.
    executed = QtCore.Signal(object)

    # Emitted when an exit request has been received from the kernel.
    exit_requested = QtCore.Signal(object)

    # Protected class variables.
    _prompt_transformer = IPythonInputSplitter(physical_line_transforms=[classic_prompt()],
                                               logical_line_transforms=[],
                                               python_line_transforms=[],
                                              )
    _CallTipRequest = namedtuple('_CallTipRequest', ['id', 'pos'])
    _CompletionRequest = namedtuple('_CompletionRequest', ['id', 'pos'])
    _ExecutionRequest = namedtuple('_ExecutionRequest', ['id', 'kind'])
    _input_splitter_class = InputSplitter
    _local_kernel = False
    _highlighter = Instance(FrontendHighlighter)

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        super(FrontendWidget, self).__init__(*args, **kw)
        # FIXME: remove this when PySide min version is updated past 1.0.7
        # forcefully disable calltips if PySide is < 1.0.7, because they crash
        if qt.QT_API == qt.QT_API_PYSIDE:
            import PySide
            if PySide.__version_info__ < (1,0,7):
                self.log.warn("PySide %s < 1.0.7 detected, disabling calltips" % PySide.__version__)
                self.enable_calltips = False

        # FrontendWidget protected variables.
        self._bracket_matcher = BracketMatcher(self._control)
        self._call_tip_widget = CallTipWidget(self._control)
        self._completion_lexer = CompletionLexer(PythonLexer())
        self._copy_raw_action = QtGui.QAction('Copy (Raw Text)', None)
        self._hidden = False
        self._highlighter = FrontendHighlighter(self)
        self._input_splitter = self._input_splitter_class()
        self._kernel_manager = None
        self._request_info = {}
        self._request_info['execute'] = {};
        self._callback_dict = {}

        # Configure the ConsoleWidget.
        self.tab_width = 4
        self._set_continuation_prompt('... ')

        # Configure the CallTipWidget.
        self._call_tip_widget.setFont(self.font)
        self.font_changed.connect(self._call_tip_widget.setFont)

        # Configure actions.
        action = self._copy_raw_action
        key = QtCore.Qt.CTRL | QtCore.Qt.SHIFT | QtCore.Qt.Key_C
        action.setEnabled(False)
        action.setShortcut(QtGui.QKeySequence(key))
        action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        action.triggered.connect(self.copy_raw)
        self.copy_available.connect(action.setEnabled)
        self.addAction(action)

        # Connect signal handlers.
        document = self._control.document()
        document.contentsChange.connect(self._document_contents_change)

        # Set flag for whether we are connected via localhost.
        self._local_kernel = kw.get('local_kernel',
                                    FrontendWidget._local_kernel)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def copy(self):
        """ Copy the currently selected text to the clipboard, removing prompts.
        """
        if self._page_control is not None and self._page_control.hasFocus():
            self._page_control.copy()
        elif self._control.hasFocus():
            text = self._control.textCursor().selection().toPlainText()
            if text:
                text = self._prompt_transformer.transform_cell(text)
                QtGui.QApplication.clipboard().setText(text)
        else:
            self.log.debug("frontend widget : unknown copy target")

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _is_complete(self, source, interactive):
        """ Returns whether 'source' can be completely processed and a new
            prompt created. When triggered by an Enter/Return key press,
            'interactive' is True; otherwise, it is False.
        """
        self._input_splitter.reset()
        complete = self._input_splitter.push(source)
        if interactive:
            complete = not self._input_splitter.push_accepts_more()
        return complete

    def _execute(self, source, hidden):
        """ Execute 'source'. If 'hidden', do not show any output.

        See parent class :meth:`execute` docstring for full details.
        """
        msg_id = self.kernel_manager.shell_channel.execute(source, hidden)
        self._request_info['execute'][msg_id] = self._ExecutionRequest(msg_id, 'user')
        self._hidden = hidden
        if not hidden:
            self.executing.emit(source)

    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        """
        if not self._reading:
            self._highlighter.highlighting_on = True

    def _prompt_finished_hook(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        # Flush all state from the input splitter so the next round of
        # reading input starts with a clean buffer.
        self._input_splitter.reset()

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

    def _context_menu_make(self, pos):
        """ Reimplemented to add an action for raw copy.
        """
        menu = super(FrontendWidget, self)._context_menu_make(pos)
        for before_action in menu.actions():
            if before_action.shortcut().matches(QtGui.QKeySequence.Paste) == \
                    QtGui.QKeySequence.ExactMatch:
                menu.insertAction(before_action, self._copy_raw_action)
                break
        return menu

    def request_interrupt_kernel(self):
        if self._executing:
            self.interrupt_kernel()

    def request_restart_kernel(self):
        message = 'Are you sure you want to restart the kernel?'
        self.restart_kernel(message, now=False)

    def _event_filter_console_keypress(self, event):
        """ Reimplemented for execution interruption and smart backspace.
        """
        key = event.key()
        if self._control_key_down(event.modifiers(), include_command=False):

            if key == QtCore.Qt.Key_C and self._executing:
                self.request_interrupt_kernel()
                return True

            elif key == QtCore.Qt.Key_Period:
                self.request_restart_kernel()
                return True

        elif not event.modifiers() & QtCore.Qt.AltModifier:

            # Smart backspace: remove four characters in one backspace if:
            # 1) everything left of the cursor is whitespace
            # 2) the four characters immediately left of the cursor are spaces
            if key == QtCore.Qt.Key_Backspace:
                col = self._get_input_buffer_cursor_column()
                cursor = self._control.textCursor()
                if col > 3 and not cursor.hasSelection():
                    text = self._get_input_buffer_cursor_line()[:col]
                    if text.endswith('    ') and not text.strip():
                        cursor.movePosition(QtGui.QTextCursor.Left,
                                            QtGui.QTextCursor.KeepAnchor, 4)
                        cursor.removeSelectedText()
                        return True

        return super(FrontendWidget, self)._event_filter_console_keypress(event)

    def _insert_continuation_prompt(self, cursor):
        """ Reimplemented for auto-indentation.
        """
        super(FrontendWidget, self)._insert_continuation_prompt(cursor)
        cursor.insertText(' ' * self._input_splitter.indent_spaces)

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_complete_reply(self, rep):
        """ Handle replies for tab completion.
        """
        self.log.debug("complete: %s", rep.get('content', ''))
        cursor = self._get_cursor()
        info = self._request_info.get('complete')
        if info and info.id == rep['parent_header']['msg_id'] and \
                info.pos == cursor.position():
            text = '.'.join(self._get_context())
            cursor.movePosition(QtGui.QTextCursor.Left, n=len(text))
            self._complete_with_items(cursor, rep['content']['matches'])

    def _silent_exec_callback(self, expr, callback):
        """Silently execute `expr` in the kernel and call `callback` with reply

        the `expr` is evaluated silently in the kernel (without) output in
        the frontend. Call `callback` with the
        `repr <http://docs.python.org/library/functions.html#repr> `_ as first argument

        Parameters
        ----------
        expr : string
            valid string to be executed by the kernel.
        callback : function
            function accepting one argument, as a string. The string will be
            the `repr` of the result of evaluating `expr`

        The `callback` is called with the `repr()` of the result of `expr` as
        first argument. To get the object, do `eval()` on the passed value.

        See Also
        --------
        _handle_exec_callback : private method, deal with calling callback with reply

        """

        # generate uuid, which would be used as an indication of whether or
        # not the unique request originated from here (can use msg id ?)
        local_uuid = str(uuid.uuid1())
        msg_id = self.kernel_manager.shell_channel.execute('',
            silent=True, user_expressions={ local_uuid:expr })
        self._callback_dict[local_uuid] = callback
        self._request_info['execute'][msg_id] = self._ExecutionRequest(msg_id, 'silent_exec_callback')

    def _handle_exec_callback(self, msg):
        """Execute `callback` corresponding to `msg` reply, after ``_silent_exec_callback``

        Parameters
        ----------
        msg : raw message send by the kernel containing an `user_expressions`
                and having a 'silent_exec_callback' kind.

        Notes
        -----
        This function will look for a `callback` associated with the
        corresponding message id. Association has been made by
        `_silent_exec_callback`. `callback` is then called with the `repr()`
        of the value of corresponding `user_expressions` as argument.
        `callback` is then removed from the known list so that any message
        coming again with the same id won't trigger it.

        """

        user_exp = msg['content'].get('user_expressions')
        if not user_exp:
            return
        for expression in user_exp:
            if expression in self._callback_dict:
                self._callback_dict.pop(expression)(user_exp[expression])

    def _handle_execute_reply(self, msg):
        """ Handles replies for code execution.
        """
        self.log.debug("execute: %s", msg.get('content', ''))
        msg_id = msg['parent_header']['msg_id']
        info = self._request_info['execute'].get(msg_id)
        # unset reading flag, because if execute finished, raw_input can't
        # still be pending.
        self._reading = False
        if info and info.kind == 'user' and not self._hidden:
            # Make sure that all output from the SUB channel has been processed
            # before writing a new prompt.
            self.kernel_manager.iopub_channel.flush()

            # Reset the ANSI style information to prevent bad text in stdout
            # from messing up our colors. We're not a true terminal so we're
            # allowed to do this.
            if self.ansi_codes:
                self._ansi_processor.reset_sgr()

            content = msg['content']
            status = content['status']
            if status == 'ok':
                self._process_execute_ok(msg)
            elif status == 'error':
                self._process_execute_error(msg)
            elif status == 'aborted':
                self._process_execute_abort(msg)

            self._show_interpreter_prompt_for_reply(msg)
            self.executed.emit(msg)
            self._request_info['execute'].pop(msg_id)
        elif info and info.kind == 'silent_exec_callback' and not self._hidden:
            self._handle_exec_callback(msg)
            self._request_info['execute'].pop(msg_id)
        else:
            super(FrontendWidget, self)._handle_execute_reply(msg)

    def _handle_input_request(self, msg):
        """ Handle requests for raw_input.
        """
        self.log.debug("input: %s", msg.get('content', ''))
        if self._hidden:
            raise RuntimeError('Request for raw input during hidden execution.')

        # Make sure that all output from the SUB channel has been processed
        # before entering readline mode.
        self.kernel_manager.iopub_channel.flush()

        def callback(line):
            self.kernel_manager.stdin_channel.input(line)
        if self._reading:
            self.log.debug("Got second input request, assuming first was interrupted.")
            self._reading = False
        self._readline(msg['content']['prompt'], callback=callback)

    def _handle_kernel_died(self, since_last_heartbeat):
        """ Handle the kernel's death by asking if the user wants to restart.
        """
        self.log.debug("kernel died: %s", since_last_heartbeat)
        if self.custom_restart:
            self.custom_restart_kernel_died.emit(since_last_heartbeat)
        else:
            message = 'The kernel heartbeat has been inactive for %.2f ' \
                'seconds. Do you want to restart the kernel? You may ' \
                'first want to check the network connection.' % \
                since_last_heartbeat
            self.restart_kernel(message, now=True)

    def _handle_object_info_reply(self, rep):
        """ Handle replies for call tips.
        """
        self.log.debug("oinfo: %s", rep.get('content', ''))
        cursor = self._get_cursor()
        info = self._request_info.get('call_tip')
        if info and info.id == rep['parent_header']['msg_id'] and \
                info.pos == cursor.position():
            # Get the information for a call tip.  For now we format the call
            # line as string, later we can pass False to format_call and
            # syntax-highlight it ourselves for nicer formatting in the
            # calltip.
            content = rep['content']
            # if this is from pykernel, 'docstring' will be the only key
            if content.get('ismagic', False):
                # Don't generate a call-tip for magics. Ideally, we should
                # generate a tooltip, but not on ( like we do for actual
                # callables.
                call_info, doc = None, None
            else:
                call_info, doc = call_tip(content, format_call=True)
            if call_info or doc:
                self._call_tip_widget.show_call_info(call_info, doc)

    def _handle_pyout(self, msg):
        """ Handle display hook output.
        """
        self.log.debug("pyout: %s", msg.get('content', ''))
        if not self._hidden and self._is_from_this_session(msg):
            text = msg['content']['data']
            self._append_plain_text(text + '\n', before_prompt=True)

    def _handle_stream(self, msg):
        """ Handle stdout, stderr, and stdin.
        """
        self.log.debug("stream: %s", msg.get('content', ''))
        if not self._hidden and self._is_from_this_session(msg):
            # Most consoles treat tabs as being 8 space characters. Convert tabs
            # to spaces so that output looks as expected regardless of this
            # widget's tab width.
            text = msg['content']['data'].expandtabs(8)

            self._append_plain_text(text, before_prompt=True)
            self._control.moveCursor(QtGui.QTextCursor.End)

    def _handle_shutdown_reply(self, msg):
        """ Handle shutdown signal, only if from other console.
        """
        self.log.debug("shutdown: %s", msg.get('content', ''))
        if not self._hidden and not self._is_from_this_session(msg):
            if self._local_kernel:
                if not msg['content']['restart']:
                    self.exit_requested.emit(self)
                else:
                    # we just got notified of a restart!
                    time.sleep(0.25) # wait 1/4 sec to reset
                                     # lest the request for a new prompt
                                     # goes to the old kernel
                    self.reset()
            else: # remote kernel, prompt on Kernel shutdown/reset
                title = self.window().windowTitle()
                if not msg['content']['restart']:
                    reply = QtGui.QMessageBox.question(self, title,
                        "Kernel has been shutdown permanently. "
                        "Close the Console?",
                        QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
                    if reply == QtGui.QMessageBox.Yes:
                        self.exit_requested.emit(self)
                else:
                    # XXX: remove message box in favor of using the
                    # clear_on_kernel_restart setting?
                    reply = QtGui.QMessageBox.question(self, title,
                        "Kernel has been reset. Clear the Console?",
                        QtGui.QMessageBox.Yes,QtGui.QMessageBox.No)
                    if reply == QtGui.QMessageBox.Yes:
                        time.sleep(0.25) # wait 1/4 sec to reset
                                         # lest the request for a new prompt
                                         # goes to the old kernel
                        self.reset()

    def _started_channels(self):
        """ Called when the KernelManager channels have started listening or
            when the frontend is assigned an already listening KernelManager.
        """
        self.reset(clear=True)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' public interface
    #---------------------------------------------------------------------------

    def copy_raw(self):
        """ Copy the currently selected text to the clipboard without attempting
            to remove prompts or otherwise alter the text.
        """
        self._control.copy()

    def execute_file(self, path, hidden=False):
        """ Attempts to execute file with 'path'. If 'hidden', no output is
            shown.
        """
        self.execute('execfile(%r)' % path, hidden=hidden)

    def interrupt_kernel(self):
        """ Attempts to interrupt the running kernel.
        
        Also unsets _reading flag, to avoid runtime errors
        if raw_input is called again.
        """
        if self.custom_interrupt:
            self._reading = False
            self.custom_interrupt_requested.emit()
        elif self.kernel_manager.has_kernel:
            self._reading = False
            self.kernel_manager.interrupt_kernel()
        else:
            self._append_plain_text('Kernel process is either remote or '
                                    'unspecified. Cannot interrupt.\n')

    def reset(self, clear=False):
        """ Resets the widget to its initial state if ``clear`` parameter or
        ``clear_on_kernel_restart`` configuration setting is True, otherwise
        prints a visual indication of the fact that the kernel restarted, but
        does not clear the traces from previous usage of the kernel before it
        was restarted.  With ``clear=True``, it is similar to ``%clear``, but
        also re-writes the banner and aborts execution if necessary.
        """
        if self._executing:
            self._executing = False
            self._request_info['execute'] = {}
        self._reading = False
        self._highlighter.highlighting_on = False

        if self.clear_on_kernel_restart or clear:
            self._control.clear()
            self._append_plain_text(self.banner)
        else:
            self._append_plain_text("# restarting kernel...")
            self._append_html("<hr><br>")
            # XXX: Reprinting the full banner may be too much, but once #1680 is
            # addressed, that will mitigate it.
            #self._append_plain_text(self.banner)
        # update output marker for stdout/stderr, so that startup
        # messages appear after banner:
        self._append_before_prompt_pos = self._get_cursor().position()
        self._show_interpreter_prompt()

    def restart_kernel(self, message, now=False):
        """ Attempts to restart the running kernel.
        """
        # FIXME: now should be configurable via a checkbox in the dialog.  Right
        # now at least the heartbeat path sets it to True and the manual restart
        # to False.  But those should just be the pre-selected states of a
        # checkbox that the user could override if so desired.  But I don't know
        # enough Qt to go implementing the checkbox now.

        if self.custom_restart:
            self.custom_restart_requested.emit()

        elif self.kernel_manager.has_kernel:
            # Pause the heart beat channel to prevent further warnings.
            self.kernel_manager.hb_channel.pause()

            # Prompt the user to restart the kernel. Un-pause the heartbeat if
            # they decline. (If they accept, the heartbeat will be un-paused
            # automatically when the kernel is restarted.)
            if self.confirm_restart:
                buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
                result = QtGui.QMessageBox.question(self, 'Restart kernel?',
                                                    message, buttons)
                do_restart = result == QtGui.QMessageBox.Yes
            else:
                # confirm_restart is False, so we don't need to ask user
                # anything, just do the restart
                do_restart = True
            if do_restart:
                try:
                    self.kernel_manager.restart_kernel(now=now)
                except RuntimeError:
                    self._append_plain_text('Kernel started externally. '
                                            'Cannot restart.\n',
                                            before_prompt=True
                                            )
                else:
                    self.reset()
            else:
                self.kernel_manager.hb_channel.unpause()

        else:
            self._append_plain_text('Kernel process is either remote or '
                                    'unspecified. Cannot restart.\n',
                                    before_prompt=True
                                    )

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _call_tip(self):
        """ Shows a call tip, if appropriate, at the current cursor location.
        """
        # Decide if it makes sense to show a call tip
        if not self.enable_calltips:
            return False
        cursor = self._get_cursor()
        cursor.movePosition(QtGui.QTextCursor.Left)
        if cursor.document().characterAt(cursor.position()) != '(':
            return False
        context = self._get_context(cursor)
        if not context:
            return False

        # Send the metadata request to the kernel
        name = '.'.join(context)
        msg_id = self.kernel_manager.shell_channel.object_info(name)
        pos = self._get_cursor().position()
        self._request_info['call_tip'] = self._CallTipRequest(msg_id, pos)
        return True

    def _complete(self):
        """ Performs completion at the current cursor location.
        """
        context = self._get_context()
        if context:
            # Send the completion request to the kernel
            msg_id = self.kernel_manager.shell_channel.complete(
                '.'.join(context),                       # text
                self._get_input_buffer_cursor_line(),    # line
                self._get_input_buffer_cursor_column(),  # cursor_pos
                self.input_buffer)                       # block
            pos = self._get_cursor().position()
            info = self._CompletionRequest(msg_id, pos)
            self._request_info['complete'] = info

    def _get_context(self, cursor=None):
        """ Gets the context for the specified cursor (or the current cursor
            if none is specified).
        """
        if cursor is None:
            cursor = self._get_cursor()
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock,
                            QtGui.QTextCursor.KeepAnchor)
        text = cursor.selection().toPlainText()
        return self._completion_lexer.get_context(text)

    def _process_execute_abort(self, msg):
        """ Process a reply for an aborted execution request.
        """
        self._append_plain_text("ERROR: execution aborted\n")

    def _process_execute_error(self, msg):
        """ Process a reply for an execution request that resulted in an error.
        """
        content = msg['content']
        # If a SystemExit is passed along, this means exit() was called - also
        # all the ipython %exit magic syntax of '-k' to be used to keep
        # the kernel running
        if content['ename']=='SystemExit':
            keepkernel = content['evalue']=='-k' or content['evalue']=='True'
            self._keep_kernel_on_exit = keepkernel
            self.exit_requested.emit(self)
        else:
            traceback = ''.join(content['traceback'])
            self._append_plain_text(traceback)

    def _process_execute_ok(self, msg):
        """ Process a reply for a successful execution request.
        """
        payload = msg['content']['payload']
        for item in payload:
            if not self._process_execute_payload(item):
                warning = 'Warning: received unknown payload of type %s'
                print(warning % repr(item['source']))

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

    #------ Trait default initializers -----------------------------------------

    def _banner_default(self):
        """ Returns the standard Python banner.
        """
        banner = 'Python %s on %s\nType "help", "copyright", "credits" or ' \
            '"license" for more information.'
        return banner % (sys.version, sys.platform)

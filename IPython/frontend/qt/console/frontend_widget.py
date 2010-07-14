# Standard library imports
from codeop import CommandCompiler
from threading import Thread
import time
import types

# System library imports
from pygments.lexers import PythonLexer
from PyQt4 import QtCore, QtGui
import zmq

# Local imports
from call_tip_widget import CallTipWidget
from completion_lexer import CompletionLexer
from console_widget import HistoryConsoleWidget
from pygments_highlighter import PygmentsHighlighter


class FrontendHighlighter(PygmentsHighlighter):
    """ A Python PygmentsHighlighter that can be turned on and off and which 
        knows about continuation prompts.
    """

    def __init__(self, frontend):
        PygmentsHighlighter.__init__(self, frontend.document(), PythonLexer())
        self._current_offset = 0
        self._frontend = frontend
        self.highlighting_on = False

    def highlightBlock(self, qstring):
        """ Highlight a block of text. Reimplemented to highlight selectively.
        """
        if self.highlighting_on:
            for prompt in (self._frontend._prompt, 
                           self._frontend.continuation_prompt):
                if qstring.startsWith(prompt):
                    qstring.remove(0, len(prompt))
                    self._current_offset = len(prompt)
                    break
            PygmentsHighlighter.highlightBlock(self, qstring)

    def setFormat(self, start, count, format):
        """ Reimplemented to avoid highlighting continuation prompts.
        """
        start += self._current_offset
        PygmentsHighlighter.setFormat(self, start, count, format)


class FrontendWidget(HistoryConsoleWidget):
    """ A Qt frontend for an IPython kernel.
    """

    # Emitted when an 'execute_reply' is received from the kernel.
    executed = QtCore.pyqtSignal(object)

    #---------------------------------------------------------------------------
    # 'QWidget' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, kernel_manager, parent=None):
        super(FrontendWidget, self).__init__(parent)

        self._call_tip_widget = CallTipWidget(self)
        self._compile = CommandCompiler()
        self._completion_lexer = CompletionLexer(PythonLexer())
        self._highlighter = FrontendHighlighter(self)
        self._kernel_manager = None

        self.continuation_prompt = '... '
        self.kernel_manager = kernel_manager

        self.document().contentsChange.connect(self._document_contents_change)

    def focusOutEvent(self, event):
        """ Reimplemented to hide calltips.
        """
        self._call_tip_widget.hide()
        return super(FrontendWidget, self).focusOutEvent(event)

    def keyPressEvent(self, event):
        """ Reimplemented to hide calltips.
        """
        if event.key() == QtCore.Qt.Key_Escape:
            self._call_tip_widget.hide()
        return super(FrontendWidget, self).keyPressEvent(event)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _execute(self, interactive):
        """ Called to execute the input buffer. When triggered by an the enter
            key press, 'interactive' is True; otherwise, it is False. Returns
            whether the input buffer was completely processed and a new prompt
            created.
        """
        return self.execute_source(self.input_buffer, interactive=interactive)
        
    def _prompt_started_hook(self):
        """ Called immediately after a new prompt is displayed.
        """
        self._highlighter.highlighting_on = True

    def _prompt_finished_hook(self):
        """ Called immediately after a prompt is finished, i.e. when some input
            will be processed and a new prompt displayed.
        """
        self._highlighter.highlighting_on = False

    def _tab_pressed(self):
        """ Called when the tab key is pressed. Returns whether to continue
            processing the event.
        """
        self._keep_cursor_in_buffer()
        cursor = self.textCursor()
        if not self._complete():
            cursor.insertText('    ')
        return False

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------

    def execute_source(self, source, hidden=False, interactive=False):
        """ Execute a string containing Python code. If 'hidden', no output is
            shown. Returns whether the source executed (i.e., returns True only
            if no more input is necessary).
        """
        try:
            code = self._compile(source, symbol='single')
        except (OverflowError, SyntaxError, ValueError):
            # Just let IPython deal with the syntax error.
            code = Exception
            
        # Only execute interactive multiline input if it ends with a blank line
        lines = source.splitlines()
        if interactive and len(lines) > 1 and lines[-1].strip() != '':
            code = None
            
        executed = code is not None
        if executed:
            self.kernel_manager.xreq_channel.execute(source)
        else:
            space = 0
            for char in lines[-1]:
                if char == '\t':
                    space += 4
                elif char == ' ':
                    space += 1
                else:
                    break
            if source.endswith(':') or source.endswith(':\n'):
                space += 4
            self._show_continuation_prompt()
            self.appendPlainText(' ' * space)

        return executed

    def execute_file(self, path, hidden=False):
        """ Attempts to execute file with 'path'. If 'hidden', no output is
            shown.
        """
        self.execute_source('run %s' % path, hidden=hidden)

    def _get_kernel_manager(self):
        """ Returns the current kernel manager.
        """
        return self._kernel_manager

    def _set_kernel_manager(self, kernel_manager):
        """ Sets a new kernel manager, configuring its channels as necessary.
        """
        # Disconnect the old kernel manager.
        if self._kernel_manager is not None:
            sub = self._kernel_manager.sub_channel
            xreq = self._kernel_manager.xreq_channel
            sub.message_received.disconnect(self._handle_sub)
            xreq.execute_reply.disconnect(self._handle_execute_reply)
            xreq.complete_reply.disconnect(self._handle_complete_reply)
            xreq.object_info_reply.disconnect(self._handle_object_info_reply)

        # Connect the new kernel manager.
        self._kernel_manager = kernel_manager
        sub = kernel_manager.sub_channel
        xreq = kernel_manager.xreq_channel
        sub.message_received.connect(self._handle_sub)
        xreq.execute_reply.connect(self._handle_execute_reply)
        xreq.complete_reply.connect(self._handle_complete_reply)
        xreq.object_info_reply.connect(self._handle_object_info_reply)
        
        self._show_prompt('>>> ')

    kernel_manager = property(_get_kernel_manager, _set_kernel_manager)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _call_tip(self):
        """ Shows a call tip, if appropriate, at the current cursor location.
        """
        # Decide if it makes sense to show a call tip
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Left)
        document = self.document()
        if document.characterAt(cursor.position()).toAscii() != '(':
            return False
        context = self._get_context(cursor)
        if not context:
            return False

        # Send the metadata request to the kernel
        name = '.'.join(context)
        self._calltip_id = self.kernel_manager.xreq_channel.object_info(name)
        self._calltip_pos = self.textCursor().position()
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
            text, self.input_buffer_cursor_line, self.input_buffer)
        self._complete_pos = self.textCursor().position()
        return True

    def _get_context(self, cursor=None):
        """ Gets the context at the current cursor location.
        """
        if cursor is None:
            cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.StartOfLine, 
                            QtGui.QTextCursor.KeepAnchor)
        text = unicode(cursor.selectedText())
        return self._completion_lexer.get_context(text)

    #------ Signal handlers ----------------------------------------------------

    def _document_contents_change(self, position, removed, added):
        """ Called whenever the document's content changes. Display a calltip
            if appropriate.
        """
        # Calculate where the cursor should be *after* the change:
        position += added

        document = self.document()
        if position == self.textCursor().position():
            self._call_tip()

    def _handle_sub(self, omsg):
        handler = getattr(self, '_handle_%s' % omsg['msg_type'], None)
        if handler is not None:
            handler(omsg)

    def _handle_pyout(self, omsg):
        session = omsg['parent_header']['session']
        if session == self.kernel_manager.session.session:
            self.appendPlainText(omsg['content']['data'] + '\n')

    def _handle_stream(self, omsg):
        self.appendPlainText(omsg['content']['data'])
        
    def _handle_execute_reply(self, rep):
        content = rep['content']
        status = content['status']
        if status == 'error':
            self.appendPlainText(content['traceback'][-1])
        elif status == 'aborted':
            text = "ERROR: ABORTED\n"
            self.appendPlainText(text)
        self._show_prompt('>>> ')
        self.executed.emit(rep)

    def _handle_complete_reply(self, rep):
        cursor = self.textCursor()
        if rep['parent_header']['msg_id'] == self._complete_id and \
                cursor.position() == self._complete_pos:
            text = '.'.join(self._get_context())
            cursor.movePosition(QtGui.QTextCursor.Left, n=len(text))
            self._complete_with_items(cursor, rep['content']['matches'])

    def _handle_object_info_reply(self, rep):
        cursor = self.textCursor()
        if rep['parent_header']['msg_id'] == self._calltip_id and \
                cursor.position() == self._calltip_pos:
            doc = rep['content']['docstring']
            if doc:
                self._call_tip_widget.show_tip(doc)


if __name__ == '__main__':
    import sys
    from IPython.frontend.qt.kernelmanager import QtKernelManager

    # Create KernelManager
    xreq_addr = ('127.0.0.1', 5575)
    sub_addr = ('127.0.0.1', 5576)
    rep_addr = ('127.0.0.1', 5577)
    kernel_manager = QtKernelManager(xreq_addr, sub_addr, rep_addr)
    kernel_manager.sub_channel.start()
    kernel_manager.xreq_channel.start()

    # Launch application
    app = QtGui.QApplication(sys.argv)
    widget = FrontendWidget(kernel_manager)
    widget.setWindowTitle('Python')
    widget.resize(640, 480)
    widget.show()
    sys.exit(app.exec_())
    

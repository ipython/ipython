# Standard library imports
from codeop import CommandCompiler
from threading import Thread
import time
import types

# System library imports
from pygments.lexers import PythonLexer
from PyQt4 import QtCore, QtGui
import zmq

# IPython imports.
from IPython.zmq.session import Message, Session

# Local imports
from call_tip_widget import CallTipWidget
from completion_lexer import CompletionLexer
from console_widget import HistoryConsoleWidget
from pygments_highlighter import PygmentsHighlighter


class FrontendReplyThread(Thread, QtCore.QObject):
    """ A Thread that receives a reply from the kernel for the frontend.
    """
    
    finished = QtCore.pyqtSignal()
    output_received = QtCore.pyqtSignal(Message)
    reply_received = QtCore.pyqtSignal(Message)

    def __init__(self, parent):
        """ Create a FrontendReplyThread for the specified frontend.
        """
        assert isinstance(parent, FrontendWidget)
        QtCore.QObject.__init__(self, parent)
        Thread.__init__(self)

        self.sleep_time = 0.05

    def run(self):
        """ The starting point for the thread.
        """
        frontend = self.parent()
        while True:
            rep = frontend._recv_reply()
            if rep is not None:
                self._recv_output()
                self.reply_received.emit(rep)
                break

            self._recv_output()
            time.sleep(self.sleep_time)
        
        self.finished.emit()

    def _recv_output(self):
        """ Send any output to the frontend.
        """
        frontend = self.parent()
        omsgs = frontend._recv_output()
        for omsg in omsgs:
            self.output_received.emit(omsg)


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
    executed = QtCore.pyqtSignal(Message)

    #---------------------------------------------------------------------------
    # 'QWidget' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, kernel_manager, parent=None):
        super(FrontendWidget, self).__init__(parent)

        self._call_tip_widget = CallTipWidget(self)
        self._compile = CommandCompiler()
        self._completion_lexer = CompletionLexer(PythonLexer())
        self._highlighter = FrontendHighlighter(self)

        self.document().contentsChange.connect(self._document_contents_change)

        self.continuation_prompt = '... '
        self.kernel_manager = kernel_manager

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
            msg = self.session.send(self.request_socket, 'execute_request',
                                    dict(code=source))
            thread = FrontendReplyThread(self)
            if not hidden:
                thread.output_received.connect(self._handle_output)
            thread.reply_received.connect(self._handle_reply)
            thread.finished.connect(thread.deleteLater)
            thread.start()
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
        self._kernel_manager = kernel_manager
        self._sub_channel = kernel_manager.get_sub_channel()
        self._xreq_channel = kernel_manager.get_xreq_channel()

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
        text = '.'.join(context)
        msg = self.session.send(self.request_socket, 'metadata_request',
                                dict(context=text))
        
        # Give the kernel some time to respond
        rep = self._recv_reply_now('metadata_reply')
        doc = rep.content.docstring if rep else ''

        # Show the call tip
        if doc:
            self._call_tip_widget.show_tip(doc)
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
        line = self.input_buffer_cursor_line
        msg = self.session.send(self.request_socket, 'complete_request',
                                dict(text=text, line=line))
        
        # Give the kernel some time to respond
        rep = self._recv_reply_now('complete_reply')
        matches = rep.content.matches if rep else []

        # Show the completion at the correct location
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Left, n=len(text))
        self._complete_with_items(cursor, matches)
        return True

    def _kernel_connected(self):
        """ Called when the frontend is connected to a kernel.
        """
        self._show_prompt('>>> ')

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

    def _handle_output(self, omsg):
        handler = getattr(self, '_handle_%s' % omsg.msg_type, None)
        if handler is not None:
            handler(omsg)

    def _handle_pyout(self, omsg):
        if omsg.parent_header.session == self.session.session:
            self.appendPlainText(omsg.content.data + '\n')

    def _handle_stream(self, omsg):
        self.appendPlainText(omsg.content.data)
        
    def _handle_reply(self, rep):
        if rep is not None:
            if rep.msg_type == 'execute_reply':
                if rep.content.status == 'error':
                    self.appendPlainText(rep.content.traceback[-1])
                elif rep.content.status == 'aborted':
                    text = "ERROR: ABORTED\n"
                    ab = self.messages[rep.parent_header.msg_id].content
                    if 'code' in ab:
                        text += ab.code
                    else:
                        text += ab
                    self.appendPlainText(text)
                self._show_prompt('>>> ')
                self.executed.emit(rep)

    #------ Communication methods ----------------------------------------------

    def _recv_output(self):
        omsgs = []
        while True:
            omsg = self.session.recv(self.sub_socket)
            if omsg is None:
                break
            else:
                omsgs.append(omsg)
        return omsgs

    def _recv_reply(self):
        return self.session.recv(self.request_socket)

    def _recv_reply_now(self, msg_type):
        for i in xrange(5):
            rep = self._recv_reply()
            if rep is not None and rep.msg_type == msg_type:
                return rep
            time.sleep(0.1)
        return None


if __name__ == '__main__':
    import sys

    # Defaults
    ip = '127.0.0.1'
    port_base = 5555
    connection = ('tcp://%s' % ip) + ':%i'
    req_conn = connection % port_base
    sub_conn = connection % (port_base+1)
    
    # Create initial sockets
    c = zmq.Context()
    request_socket = c.socket(zmq.XREQ)
    request_socket.connect(req_conn)
    sub_socket = c.socket(zmq.SUB)
    sub_socket.connect(sub_conn)
    sub_socket.setsockopt(zmq.SUBSCRIBE, '')

    # Launch application
    app = QtGui.QApplication(sys.argv)
    widget = FrontendWidget(request_socket=request_socket, 
                            sub_socket=sub_socket)
    widget.setWindowTitle('Python')
    widget.resize(640, 480)
    widget.show()
    sys.exit(app.exec_())
    

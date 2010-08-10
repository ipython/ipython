# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.core.usage import default_banner
from frontend_widget import FrontendWidget


class IPythonWidget(FrontendWidget):
    """ A FrontendWidget for an IPython kernel.
    """

    # The default stylesheet: black text on a white background.
    default_stylesheet = """
        .error { color: red; }
        .in-prompt { color: navy; }
        .in-prompt-number { font-weight: bold; }
        .out-prompt { color: darkred; }
        .out-prompt-number { font-weight: bold; }
    """

    # A dark stylesheet: white text on a black background.
    dark_stylesheet = """
        QPlainTextEdit { background-color: black; color: white }
        QFrame { border: 1px solid grey; }
        .error { color: red; }
        .in-prompt { color: lime; }
        .in-prompt-number { color: lime; font-weight: bold; }
        .out-prompt { color: red; }
        .out-prompt-number { color: red; font-weight: bold; }
    """

    #---------------------------------------------------------------------------
    # 'QObject' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, parent=None):
        super(IPythonWidget, self).__init__(parent)

        # Initialize protected variables.
        self._prompt_count = 0

        # Set a default stylesheet.
        self.reset_styling()

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------

    def execute_file(self, path, hidden=False):
        """ Reimplemented to use the 'run' magic.
        """
        self.execute('run %s' % path, hidden=hidden)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _get_banner(self):
        """ Reimplemented to return IPython's default banner.
        """
        return default_banner

    def _show_interpreter_prompt(self):
        """ Reimplemented for IPython-style prompts.
        """
        self._prompt_count += 1
        prompt_template = '<span class="in-prompt">%s</span>'
        prompt_body = '<br/>In [<span class="in-prompt-number">%i</span>]: '
        prompt = (prompt_template % prompt_body) % self._prompt_count
        self._show_prompt(prompt, html=True)

        # Update continuation prompt to reflect (possibly) new prompt length.
        cont_prompt_chars = '...: '
        space_count = len(self._prompt.lstrip()) - len(cont_prompt_chars)
        cont_prompt_body = '&nbsp;' * space_count + cont_prompt_chars
        self._continuation_prompt_html = prompt_template % cont_prompt_body

    #------ Signal handlers ----------------------------------------------------

    def _handle_execute_error(self, reply):
        """ Reimplemented for IPython-style traceback formatting.
        """
        content = reply['content']
        traceback_lines = content['traceback'][:]
        traceback = ''.join(traceback_lines)
        traceback = traceback.replace(' ', '&nbsp;')
        traceback = traceback.replace('\n', '<br/>')

        ename = content['ename']
        ename_styled = '<span class="error">%s</span>' % ename
        traceback = traceback.replace(ename, ename_styled)

        self.appendHtml(traceback)

    def _handle_pyout(self, omsg):
        """ Reimplemented for IPython-style "display hook".
        """
        prompt_template = '<span class="out-prompt">%s</span>'
        prompt_body = 'Out[<span class="out-prompt-number">%i</span>]: '
        prompt = (prompt_template % prompt_body) % self._prompt_count
        self.appendHtml(prompt)
        self.appendPlainText(omsg['content']['data'] + '\n')

    #---------------------------------------------------------------------------
    # 'IPythonWidget' interface
    #---------------------------------------------------------------------------

    def reset_styling(self):
        """ Restores the default IPythonWidget styling.
        """
        self.set_styling(self.default_stylesheet, syntax_style='default')
        #self.set_styling(self.dark_stylesheet, syntax_style='monokai')

    def set_styling(self, stylesheet, syntax_style=None):
        """ Sets the IPythonWidget styling.

        Parameters:
        -----------
        stylesheet : str
            A CSS stylesheet. The stylesheet can contain classes for:
                1. Qt: QPlainTextEdit, QFrame, QWidget, etc
                2. Pygments: .c, .k, .o, etc (see PygmentsHighlighter)
                3. IPython: .error, .in-prompt, .out-prompt, etc.

        syntax_style : str or None [default None]
            If specified, use the Pygments style with given name. Otherwise, 
            the stylesheet is queried for Pygments style information.
        """
        self.setStyleSheet(stylesheet)
        self.document().setDefaultStyleSheet(stylesheet)

        if syntax_style is None:
            self._highlighter.set_style_sheet(stylesheet)
        else:
            self._highlighter.set_style(syntax_style)


if __name__ == '__main__':
    from IPython.frontend.qt.kernelmanager import QtKernelManager

    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager.
    kernel_manager = QtKernelManager()
    kernel_manager.start_kernel()
    kernel_manager.start_channels()

    # Launch the application.
    app = QtGui.QApplication([])
    widget = IPythonWidget()
    widget.kernel_manager = kernel_manager
    widget.setWindowTitle('Python')
    widget.resize(640, 480)
    widget.show()
    app.exec_()

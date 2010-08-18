# Standard library imports
from subprocess import Popen

# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.core.inputsplitter import IPythonInputSplitter
from IPython.core.usage import default_banner
from frontend_widget import FrontendWidget


class IPythonWidget(FrontendWidget):
    """ A FrontendWidget for an IPython kernel.
    """

    # Signal emitted when an editor is needed for a file and the editor has been
    # specified as 'custom'.
    custom_edit_requested = QtCore.pyqtSignal(object)

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

    # Default prompts.
    in_prompt = '<br/>In [<span class="in-prompt-number">%i</span>]: '
    out_prompt = 'Out[<span class="out-prompt-number">%i</span>]: '

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, *args, **kw):
        super(IPythonWidget, self).__init__(*args, **kw)

        # FrontendWidget protected variables.
        #self._input_splitter = IPythonInputSplitter(input_mode='replace')

        # IPythonWidget protected variables.
        self._previous_prompt_blocks = []
        self._prompt_count = 0

        # Set a default editor and stylesheet.
        self.set_editor('default')
        self.reset_styling()

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_pyout(self, msg):
        """ Reimplemented for IPython-style "display hook".
        """
        self._append_html(self._make_out_prompt(self._prompt_count))
        self._save_prompt_block()
        
        self._append_plain_text(msg['content']['data'] + '\n')

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

    def _process_execute_error(self, msg):
        """ Reimplemented for IPython-style traceback formatting.
        """
        content = msg['content']
        traceback_lines = content['traceback'][:]
        traceback = ''.join(traceback_lines)
        traceback = traceback.replace(' ', '&nbsp;')
        traceback = traceback.replace('\n', '<br/>')

        ename = content['ename']
        ename_styled = '<span class="error">%s</span>' % ename
        traceback = traceback.replace(ename, ename_styled)

        self._append_html(traceback)

    def _show_interpreter_prompt(self):
        """ Reimplemented for IPython-style prompts.
        """
        # Update old prompt numbers if necessary.
        previous_prompt_number = self._prompt_count
        if previous_prompt_number != self._prompt_count:
            for i, (block, length) in enumerate(self._previous_prompt_blocks):
                if block.isValid():
                    cursor = QtGui.QTextCursor(block)
                    cursor.movePosition(QtGui.QTextCursor.Right,
                                        QtGui.QTextCursor.KeepAnchor, length-1)
                    if i == 0:
                        prompt = self._make_in_prompt(previous_prompt_number)
                    else:
                        prompt = self._make_out_prompt(previous_prompt_number)
                    self._insert_html(cursor, prompt)
        self._previous_prompt_blocks = []

        # Show a new prompt.
        self._prompt_count += 1
        self._show_prompt(self._make_in_prompt(self._prompt_count), html=True)
        self._save_prompt_block()

        # Update continuation prompt to reflect (possibly) new prompt length.
        self._set_continuation_prompt(
            self._make_continuation_prompt(self._prompt), html=True)

    #---------------------------------------------------------------------------
    # 'IPythonWidget' interface
    #---------------------------------------------------------------------------

    def edit(self, filename):
        """ Opens a Python script for editing.

        Parameters:
        -----------
        filename : str
            A path to a local system file.
        
        Raises:
        -------
        OSError
            If the editor command cannot be executed.
        """
        if self._editor == 'default':
            url = QtCore.QUrl.fromLocalFile(filename)
            if not QtGui.QDesktopServices.openUrl(url):
                message = 'Failed to open %s with the default application'
                raise OSError(message % repr(filename))
        elif self._editor is None:
            self.custom_edit_requested.emit(filename)
        else:
            Popen(self._editor + [filename])

    def reset_styling(self):
        """ Restores the default IPythonWidget styling.
        """
        self.set_styling(self.default_stylesheet, syntax_style='default')
        #self.set_styling(self.dark_stylesheet, syntax_style='monokai')

    def set_editor(self, editor):
        """ Sets the editor to use with the %edit magic.

        Parameters:
        -----------
        editor : str or sequence of str
            A command suitable for use with Popen. This command will be executed
            with a single argument--a filename--when editing is requested.

            This parameter also takes two special values:
                'default' : Files will be edited with the system default 
                            application for Python files.
                'custom'  : Emit a 'custom_edit_requested(str)' signal instead
                            of opening an editor.
        """
        if editor == 'default':
            self._editor = 'default'
        elif editor == 'custom':
            self._editor = None
        elif isinstance(editor, basestring):
            self._editor = [ editor ]
        else:
            self._editor = list(editor)

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
        self._control.document().setDefaultStyleSheet(stylesheet)
        if self._page_control:
            self._page_control.document().setDefaultStyleSheet(stylesheet)

        if syntax_style is None:
            self._highlighter.set_style_sheet(stylesheet)
        else:
            self._highlighter.set_style(syntax_style)

    #---------------------------------------------------------------------------
    # 'IPythonWidget' protected interface
    #---------------------------------------------------------------------------

    def _make_in_prompt(self, number):
        """ Given a prompt number, returns an HTML In prompt.
        """
        body = self.in_prompt % number
        return '<span class="in-prompt">%s</span>' % body

    def _make_continuation_prompt(self, prompt):
        """ Given a plain text version of an In prompt, returns an HTML
            continuation prompt.
        """
        end_chars = '...: '
        space_count = len(prompt.lstrip('\n')) - len(end_chars)
        body = '&nbsp;' * space_count + end_chars
        return '<span class="in-prompt">%s</span>' % body
        
    def _make_out_prompt(self, number):
        """ Given a prompt number, returns an HTML Out prompt.
        """
        body = self.out_prompt % number
        return '<span class="out-prompt">%s</span>' % body

    def _save_prompt_block(self):
        """ Assuming a prompt has just been written at the end of the buffer,
            store the QTextBlock that contains it and its length.
        """
        block = self._control.document().lastBlock()
        self._previous_prompt_blocks.append((block, block.length()))

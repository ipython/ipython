""" A FrontendWidget that emulates the interface of the console IPython and
    supports the additional functionality provided by the IPython kernel.

    TODO: Add support for retrieving the system default editor. Requires code
          paths for Windows (use the registry), Mac OS (use LaunchServices), and
          Linux (use the xdg system).
"""

# Standard library imports
from subprocess import Popen

# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.core.inputsplitter import IPythonInputSplitter
from IPython.core.usage import default_banner
from frontend_widget import FrontendWidget


class IPythonPromptBlock(object):
    """ An internal storage object for IPythonWidget.
    """
    def __init__(self, block, length, number):
        self.block = block
        self.length = length
        self.number = number


class IPythonWidget(FrontendWidget):
    """ A FrontendWidget for an IPython kernel.
    """

    # Signal emitted when an editor is needed for a file and the editor has been
    # specified as 'custom'. See 'set_editor' for more information.
    custom_edit_requested = QtCore.pyqtSignal(object, object)

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
        QPlainTextEdit, QTextEdit { background-color: black; color: white }
        QFrame { border: 1px solid grey; }
        .error { color: red; }
        .in-prompt { color: lime; }
        .in-prompt-number { color: lime; font-weight: bold; }
        .out-prompt { color: red; }
        .out-prompt-number { color: red; font-weight: bold; }
    """

    # Default prompts.
    in_prompt = 'In [<span class="in-prompt-number">%i</span>]: '
    out_prompt = 'Out[<span class="out-prompt-number">%i</span>]: '

    # FrontendWidget protected class variables.
    #_input_splitter_class = IPythonInputSplitter

    # IPythonWidget protected class variables.
    _payload_source_edit = 'IPython.zmq.zmqshell.ZMQInteractiveShell.edit_magic'
    _payload_source_page = 'IPython.zmq.page.page'

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, *args, **kw):
        super(IPythonWidget, self).__init__(*args, **kw)

        # IPythonWidget protected variables.
        self._previous_prompt_obj = None

        # Set a default editor and stylesheet.
        self.set_editor('default')
        self.reset_styling()

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_history_reply(self, msg):
        """ Implemented to handle history replies, which are only supported by
            the IPython kernel.
        """
        history_dict = msg['content']['history']
        items = [ history_dict[key] for key in sorted(history_dict.keys()) ]
        self._set_history(items)

    def _handle_prompt_reply(self, msg):
        """ Implemented to handle prompt number replies, which are only
            supported by the IPython kernel.
        """
        content = msg['content']
        self._show_interpreter_prompt(content['prompt_number'], 
                                      content['input_sep'])

    def _handle_pyout(self, msg):
        """ Reimplemented for IPython-style "display hook".
        """
        if not self._hidden and self._is_from_this_session(msg):
            content = msg['content']
            prompt_number = content['prompt_number']
            self._append_plain_text(content['output_sep'])
            self._append_html(self._make_out_prompt(prompt_number))
            self._append_plain_text(content['data'] + '\n' + 
                                    content['output_sep2'])

    def _started_channels(self):
        """ Reimplemented to make a history request.
        """
        super(IPythonWidget, self)._started_channels()
        # FIXME: Disabled until history requests are properly implemented.
        #self.kernel_manager.xreq_channel.history(raw=True, output=False)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------

    def execute_file(self, path, hidden=False):
        """ Reimplemented to use the 'run' magic.
        """
        self.execute('%%run %s' % path, hidden=hidden)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _get_banner(self):
        """ Reimplemented to return IPython's default banner.
        """
        return default_banner + '\n'

    def _process_execute_error(self, msg):
        """ Reimplemented for IPython-style traceback formatting.
        """
        content = msg['content']
        traceback = '\n'.join(content['traceback']) + '\n'
        if False:
            # FIXME: For now, tracebacks come as plain text, so we can't use
            # the html renderer yet.  Once we refactor ultratb to produce
            # properly styled tracebacks, this branch should be the default
            traceback = traceback.replace(' ', '&nbsp;')
            traceback = traceback.replace('\n', '<br/>')

            ename = content['ename']
            ename_styled = '<span class="error">%s</span>' % ename
            traceback = traceback.replace(ename, ename_styled)

            self._append_html(traceback)
        else:
            # This is the fallback for now, using plain text with ansi escapes
            self._append_plain_text(traceback)

    def _process_execute_payload(self, item):
        """ Reimplemented to handle %edit and paging payloads.
        """
        if item['source'] == self._payload_source_edit:
            self._edit(item['filename'], item['line_number'])
            return True
        elif item['source'] == self._payload_source_page:
            self._page(item['data'])
            return True
        else:
            return False

    def _show_interpreter_prompt(self, number=None, input_sep='\n'):
        """ Reimplemented for IPython-style prompts.
        """
        # If a number was not specified, make a prompt number request.
        if number is None:
            self.kernel_manager.xreq_channel.prompt()
            return

        # Show a new prompt and save information about it so that it can be
        # updated later if the prompt number turns out to be wrong.
        self._append_plain_text(input_sep)
        self._show_prompt(self._make_in_prompt(number), html=True)
        block = self._control.document().lastBlock()
        length = len(self._prompt)
        self._previous_prompt_obj = IPythonPromptBlock(block, length, number)

        # Update continuation prompt to reflect (possibly) new prompt length.
        self._set_continuation_prompt(
            self._make_continuation_prompt(self._prompt), html=True)

    def _show_interpreter_prompt_for_reply(self, msg):
        """ Reimplemented for IPython-style prompts.
        """
        # Update the old prompt number if necessary.
        content = msg['content']
        previous_prompt_number = content['prompt_number']
        if self._previous_prompt_obj and \
                self._previous_prompt_obj.number != previous_prompt_number:
            block = self._previous_prompt_obj.block

            # Make sure the prompt block has not been erased.
            if block.isValid() and not block.text().isEmpty():

                # Remove the old prompt and insert a new prompt.
                cursor = QtGui.QTextCursor(block)
                cursor.movePosition(QtGui.QTextCursor.Right,
                                    QtGui.QTextCursor.KeepAnchor, 
                                    self._previous_prompt_obj.length)
                prompt = self._make_in_prompt(previous_prompt_number)
                self._prompt = self._insert_html_fetching_plain_text(
                    cursor, prompt)

                # When the HTML is inserted, Qt blows away the syntax
                # highlighting for the line, so we need to rehighlight it.
                self._highlighter.rehighlightBlock(cursor.block())

            self._previous_prompt_obj = None

        # Show a new prompt with the kernel's estimated prompt number.
        next_prompt = content['next_prompt']
        self._show_interpreter_prompt(next_prompt['prompt_number'], 
                                      next_prompt['input_sep'])

    #---------------------------------------------------------------------------
    # 'IPythonWidget' interface
    #---------------------------------------------------------------------------

    def reset_styling(self):
        """ Restores the default IPythonWidget styling.
        """
        self.set_styling(self.default_stylesheet, syntax_style='default')
        #self.set_styling(self.dark_stylesheet, syntax_style='monokai')

    def set_editor(self, editor, line_editor=None):
        """ Sets the editor to use with the %edit magic.

        Parameters:
        -----------
        editor : str
            A command for invoking a system text editor. If the string contains
            a {filename} format specifier, it will be used. Otherwise, the 
            filename will be appended to the end the command.

            This parameter also takes a special value:
                'custom'  : Emit a 'custom_edit_requested(str, int)' signal 
                            instead of opening an editor.

        line_editor : str, optional
            The editor command to use when a specific line number is
            requested. The string should contain two format specifiers: {line}
            and {filename}. If this parameter is not specified, the line number
            option to the %edit magic will be ignored.
        """
        self._editor = editor
        self._editor_line = line_editor

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

    def _edit(self, filename, line=None):
        """ Opens a Python script for editing.

        Parameters:
        -----------
        filename : str
            A path to a local system file.

        line : int, optional
            A line of interest in the file.
        """
        if self._editor == 'custom':
            self.custom_edit_requested.emit(filename, line)
        elif self._editor == 'default':
            self._append_plain_text('No default editor available.\n')
        else:
            try:
                filename = '"%s"' % filename
                if line and self._editor_line:
                    command = self._editor_line.format(filename=filename,
                                                       line=line)
                else:
                    try:
                        command = self._editor.format()
                    except KeyError:
                        command = self._editor.format(filename=filename)
                    else:
                        command += ' ' + filename
            except KeyError:
                self._append_plain_text('Invalid editor command.\n')
            else:
                try:
                    Popen(command, shell=True)
                except OSError:
                    msg = 'Opening editor with command "%s" failed.\n'
                    self._append_plain_text(msg % command)

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

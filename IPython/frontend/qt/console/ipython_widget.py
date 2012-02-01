""" A FrontendWidget that emulates the interface of the console IPython and
    supports the additional functionality provided by the IPython kernel.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
from collections import namedtuple
import os.path
import re
from subprocess import Popen
import sys
import time
from textwrap import dedent

# System library imports
from IPython.external.qt import QtCore, QtGui

# Local imports
from IPython.core.inputsplitter import IPythonInputSplitter, \
    transform_ipy_prompt
from IPython.utils.traitlets import Bool, Unicode
from frontend_widget import FrontendWidget
import styles

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# Default strings to build and display input and output prompts (and separators
# in between)
default_in_prompt = 'In [<span class="in-prompt-number">%i</span>]: '
default_out_prompt = 'Out[<span class="out-prompt-number">%i</span>]: '
default_input_sep = '\n'
default_output_sep = ''
default_output_sep2 = ''

# Base path for most payload sources.
zmq_shell_source = 'IPython.zmq.zmqshell.ZMQInteractiveShell'

if sys.platform.startswith('win'):
    default_editor = 'notepad'
else:
    default_editor = ''

#-----------------------------------------------------------------------------
# IPythonWidget class
#-----------------------------------------------------------------------------

class IPythonWidget(FrontendWidget):
    """ A FrontendWidget for an IPython kernel.
    """

    # If set, the 'custom_edit_requested(str, int)' signal will be emitted when
    # an editor is needed for a file. This overrides 'editor' and 'editor_line'
    # settings.
    custom_edit = Bool(False)
    custom_edit_requested = QtCore.Signal(object, object)

    editor = Unicode(default_editor, config=True,
        help="""
        A command for invoking a system text editor. If the string contains a
        {filename} format specifier, it will be used. Otherwise, the filename
        will be appended to the end the command.
        """)

    editor_line = Unicode(config=True,
        help="""
        The editor command to use when a specific line number is requested. The
        string should contain two format specifiers: {line} and {filename}. If
        this parameter is not specified, the line number option to the %edit
        magic will be ignored.
        """)

    style_sheet = Unicode(config=True,
        help="""
        A CSS stylesheet. The stylesheet can contain classes for:
            1. Qt: QPlainTextEdit, QFrame, QWidget, etc
            2. Pygments: .c, .k, .o, etc. (see PygmentsHighlighter)
            3. IPython: .error, .in-prompt, .out-prompt, etc
        """)

    syntax_style = Unicode(config=True,
        help="""
        If not empty, use this Pygments style for syntax highlighting.
        Otherwise, the style sheet is queried for Pygments style
        information.
        """)

    # Prompts.
    in_prompt = Unicode(default_in_prompt, config=True)
    out_prompt = Unicode(default_out_prompt, config=True)
    input_sep = Unicode(default_input_sep, config=True)
    output_sep = Unicode(default_output_sep, config=True)
    output_sep2 = Unicode(default_output_sep2, config=True)

    # FrontendWidget protected class variables.
    _input_splitter_class = IPythonInputSplitter
    _transform_prompt = staticmethod(transform_ipy_prompt)

    # IPythonWidget protected class variables.
    _PromptBlock = namedtuple('_PromptBlock', ['block', 'length', 'number'])
    _payload_source_edit = zmq_shell_source + '.edit_magic'
    _payload_source_exit = zmq_shell_source + '.ask_exit'
    _payload_source_next_input = zmq_shell_source + '.set_next_input'
    _payload_source_page = 'IPython.zmq.page.page'
    _retrying_history_request = False

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        super(IPythonWidget, self).__init__(*args, **kw)

        # IPythonWidget protected variables.
        self._payload_handlers = {
            self._payload_source_edit : self._handle_payload_edit,
            self._payload_source_exit : self._handle_payload_exit,
            self._payload_source_page : self._handle_payload_page,
            self._payload_source_next_input : self._handle_payload_next_input }
        self._previous_prompt_obj = None
        self._keep_kernel_on_exit = None

        # Initialize widget styling.
        if self.style_sheet:
            self._style_sheet_changed()
            self._syntax_style_changed()
        else:
            self.set_default_style()

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_complete_reply(self, rep):
        """ Reimplemented to support IPython's improved completion machinery.
        """
        self.log.debug("complete: %s", rep.get('content', ''))
        cursor = self._get_cursor()
        info = self._request_info.get('complete')
        if info and info.id == rep['parent_header']['msg_id'] and \
                info.pos == cursor.position():
            matches = rep['content']['matches']
            text = rep['content']['matched_text']
            offset = len(text)

            # Clean up matches with period and path separators if the matched
            # text has not been transformed. This is done by truncating all
            # but the last component and then suitably decreasing the offset
            # between the current cursor position and the start of completion.
            if len(matches) > 1 and matches[0][:offset] == text:
                parts = re.split(r'[./\\]', text)
                sep_count = len(parts) - 1
                if sep_count:
                    chop_length = sum(map(len, parts[:sep_count])) + sep_count
                    matches = [ match[chop_length:] for match in matches ]
                    offset -= chop_length

            # Move the cursor to the start of the match and complete.
            cursor.movePosition(QtGui.QTextCursor.Left, n=offset)
            self._complete_with_items(cursor, matches)

    def _handle_execute_reply(self, msg):
        """ Reimplemented to support prompt requests.
        """
        msg_id = msg['parent_header'].get('msg_id')
        info = self._request_info['execute'].get(msg_id)
        if info and info.kind == 'prompt':
           number = msg['content']['execution_count'] + 1
           self._show_interpreter_prompt(number)
           self._request_info['execute'].pop(msg_id)
        else:
           super(IPythonWidget, self)._handle_execute_reply(msg)

    def _handle_history_reply(self, msg):
        """ Implemented to handle history tail replies, which are only supported
            by the IPython kernel.
        """
        self.log.debug("history: %s", msg.get('content', ''))
        content = msg['content']
        if 'history' not in content:
            self.log.error("History request failed: %r"%content)
            if content.get('status', '') == 'aborted' and \
                                            not self._retrying_history_request:
                # a *different* action caused this request to be aborted, so
                # we should try again.
                self.log.error("Retrying aborted history request")
                # prevent multiple retries of aborted requests:
                self._retrying_history_request = True
                # wait out the kernel's queue flush, which is currently timed at 0.1s
                time.sleep(0.25)
                self.kernel_manager.shell_channel.history(hist_access_type='tail',n=1000)
            else:
                self._retrying_history_request = False
            return
        # reset retry flag
        self._retrying_history_request = False
        history_items = content['history']
        items = []
        last_cell = u""
        for _, _, cell in history_items:
            cell = cell.rstrip()
            if cell != last_cell:
                items.append(cell)
                last_cell = cell
        self._set_history(items)

    def _handle_pyout(self, msg):
        """ Reimplemented for IPython-style "display hook".
        """
        self.log.debug("pyout: %s", msg.get('content', ''))
        if not self._hidden and self._is_from_this_session(msg):
            content = msg['content']
            prompt_number = content['execution_count']
            data = content['data']
            if data.has_key('text/html'):
                self._append_plain_text(self.output_sep, True)
                self._append_html(self._make_out_prompt(prompt_number), True)
                html = data['text/html']
                self._append_plain_text('\n', True)
                self._append_html(html + self.output_sep2, True)
            elif data.has_key('text/plain'):
                self._append_plain_text(self.output_sep, True)
                self._append_html(self._make_out_prompt(prompt_number), True)
                text = data['text/plain']
                # If the repr is multiline, make sure we start on a new line,
                # so that its lines are aligned.
                if "\n" in text and not self.output_sep.endswith("\n"):
                    self._append_plain_text('\n', True)
                self._append_plain_text(text + self.output_sep2, True)

    def _handle_display_data(self, msg):
        """ The base handler for the ``display_data`` message.
        """
        self.log.debug("display: %s", msg.get('content', ''))
        # For now, we don't display data from other frontends, but we
        # eventually will as this allows all frontends to monitor the display
        # data. But we need to figure out how to handle this in the GUI.
        if not self._hidden and self._is_from_this_session(msg):
            source = msg['content']['source']
            data = msg['content']['data']
            metadata = msg['content']['metadata']
            # In the regular IPythonWidget, we simply print the plain text
            # representation.
            if data.has_key('text/html'):
                html = data['text/html']
                self._append_html(html, True)
            elif data.has_key('text/plain'):
                text = data['text/plain']
                self._append_plain_text(text, True)
            # This newline seems to be needed for text and html output.
            self._append_plain_text(u'\n', True)

    def _started_channels(self):
        """ Reimplemented to make a history request.
        """
        super(IPythonWidget, self)._started_channels()
        self.kernel_manager.shell_channel.history(hist_access_type='tail',
                                                  n=1000)
    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface
    #---------------------------------------------------------------------------

    #---------------------------------------------------------------------------
    # 'FrontendWidget' public interface
    #---------------------------------------------------------------------------

    def execute_file(self, path, hidden=False):
        """ Reimplemented to use the 'run' magic.
        """
        # Use forward slashes on Windows to avoid escaping each separator.
        if sys.platform == 'win32':
            path = os.path.normpath(path).replace('\\', '/')

        # Perhaps we should not be using %run directly, but while we
        # are, it is necessary to quote or escape filenames containing spaces 
        # or quotes. 
        
        # In earlier code here, to minimize escaping, we sometimes quoted the 
        # filename with single quotes. But to do this, this code must be
        # platform-aware, because run uses shlex rather than python string
        # parsing, so that:
        # * In Win: single quotes can be used in the filename without quoting,
        #   and we cannot use single quotes to quote the filename.
        # * In *nix: we can escape double quotes in a double quoted filename,
        #   but can't escape single quotes in a single quoted filename.
        
        # So to keep this code non-platform-specific and simple, we now only
        # use double quotes to quote filenames, and escape when needed:
        if ' ' in path or "'" in path or '"' in path:
            path = '"%s"' % path.replace('"', '\\"')
        self.execute('%%run %s' % path, hidden=hidden)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _complete(self):
        """ Reimplemented to support IPython's improved completion machinery.
        """
        # We let the kernel split the input line, so we *always* send an empty
        # text field. Readline-based frontends do get a real text field which
        # they can use.
        text = ''

        # Send the completion request to the kernel
        msg_id = self.kernel_manager.shell_channel.complete(
            text,                                    # text
            self._get_input_buffer_cursor_line(),    # line
            self._get_input_buffer_cursor_column(),  # cursor_pos
            self.input_buffer)                       # block
        pos = self._get_cursor().position()
        info = self._CompletionRequest(msg_id, pos)
        self._request_info['complete'] = info

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
        """ Reimplemented to dispatch payloads to handler methods.
        """
        handler = self._payload_handlers.get(item['source'])
        if handler is None:
            # We have no handler for this type of payload, simply ignore it
            return False
        else:
            handler(item)
            return True

    def _show_interpreter_prompt(self, number=None):
        """ Reimplemented for IPython-style prompts.
        """
        # If a number was not specified, make a prompt number request.
        if number is None:
            msg_id = self.kernel_manager.shell_channel.execute('', silent=True)
            info = self._ExecutionRequest(msg_id, 'prompt')
            self._request_info['execute'][msg_id] = info
            return

        # Show a new prompt and save information about it so that it can be
        # updated later if the prompt number turns out to be wrong.
        self._prompt_sep = self.input_sep
        self._show_prompt(self._make_in_prompt(number), html=True)
        block = self._control.document().lastBlock()
        length = len(self._prompt)
        self._previous_prompt_obj = self._PromptBlock(block, length, number)

        # Update continuation prompt to reflect (possibly) new prompt length.
        self._set_continuation_prompt(
            self._make_continuation_prompt(self._prompt), html=True)

    def _show_interpreter_prompt_for_reply(self, msg):
        """ Reimplemented for IPython-style prompts.
        """
        # Update the old prompt number if necessary.
        content = msg['content']
        # abort replies do not have any keys:
        if content['status'] == 'aborted':
            if self._previous_prompt_obj:
                previous_prompt_number = self._previous_prompt_obj.number
            else:
                previous_prompt_number = 0
        else:
            previous_prompt_number = content['execution_count']
        if self._previous_prompt_obj and \
                self._previous_prompt_obj.number != previous_prompt_number:
            block = self._previous_prompt_obj.block

            # Make sure the prompt block has not been erased.
            if block.isValid() and block.text():

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
        self._show_interpreter_prompt(previous_prompt_number + 1)

    #---------------------------------------------------------------------------
    # 'IPythonWidget' interface
    #---------------------------------------------------------------------------

    def set_default_style(self, colors='lightbg'):
        """ Sets the widget style to the class defaults.

        Parameters:
        -----------
        colors : str, optional (default lightbg)
            Whether to use the default IPython light background or dark
            background or B&W style.
        """
        colors = colors.lower()
        if colors=='lightbg':
            self.style_sheet = styles.default_light_style_sheet
            self.syntax_style = styles.default_light_syntax_style
        elif colors=='linux':
            self.style_sheet = styles.default_dark_style_sheet
            self.syntax_style = styles.default_dark_syntax_style
        elif colors=='nocolor':
            self.style_sheet = styles.default_bw_style_sheet
            self.syntax_style = styles.default_bw_syntax_style
        else:
            raise KeyError("No such color scheme: %s"%colors)

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
        if self.custom_edit:
            self.custom_edit_requested.emit(filename, line)
        elif not self.editor:
            self._append_plain_text('No default editor available.\n'
            'Specify a GUI text editor in the `IPythonWidget.editor` '
            'configurable to enable the %edit magic')
        else:
            try:
                filename = '"%s"' % filename
                if line and self.editor_line:
                    command = self.editor_line.format(filename=filename,
                                                      line=line)
                else:
                    try:
                        command = self.editor.format()
                    except KeyError:
                        command = self.editor.format(filename=filename)
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
        try:
            body = self.in_prompt % number
        except TypeError:
            # allow in_prompt to leave out number, e.g. '>>> '
            body = self.in_prompt
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

    #------ Payload handlers --------------------------------------------------

    # Payload handlers with a generic interface: each takes the opaque payload
    # dict, unpacks it and calls the underlying functions with the necessary
    # arguments.

    def _handle_payload_edit(self, item):
        self._edit(item['filename'], item['line_number'])

    def _handle_payload_exit(self, item):
        self._keep_kernel_on_exit = item['keepkernel']
        self.exit_requested.emit(self)

    def _handle_payload_next_input(self, item):
        self.input_buffer = dedent(item['text'].rstrip())

    def _handle_payload_page(self, item):
        # Since the plain text widget supports only a very small subset of HTML
        # and we have no control over the HTML source, we only page HTML
        # payloads in the rich text widget.
        if item['html'] and self.kind == 'rich':
            self._page(item['html'], html=True)
        else:
            self._page(item['text'], html=False)

    #------ Trait change handlers --------------------------------------------

    def _style_sheet_changed(self):
        """ Set the style sheets of the underlying widgets.
        """
        self.setStyleSheet(self.style_sheet)
        if self._control is not None:
            self._control.document().setDefaultStyleSheet(self.style_sheet)
            bg_color = self._control.palette().window().color()
            self._ansi_processor.set_background_color(bg_color)
        
        if self._page_control is not None:
            self._page_control.document().setDefaultStyleSheet(self.style_sheet)



    def _syntax_style_changed(self):
        """ Set the style for the syntax highlighter.
        """
        if self._highlighter is None:
            # ignore premature calls
            return
        if self.syntax_style:
            self._highlighter.set_style(self.syntax_style)
        else:
            self._highlighter.set_style_sheet(self.style_sheet)

    #------ Trait default initializers -----------------------------------------

    def _banner_default(self):
        from IPython.core.usage import default_gui_banner
        return default_gui_banner

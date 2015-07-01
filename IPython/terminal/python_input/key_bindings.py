from __future__ import unicode_literals

from prompt_toolkit.document import Document
from prompt_toolkit.filters import HasSelection, IsMultiline, Filter, HasFocus, Condition
from prompt_toolkit.key_binding.bindings.vi import ViStateFilter
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.keys import Keys

__all__ = (
    'load_python_bindings',
)


class TabShouldInsertWhitespaceFilter(Filter):
    """
    When the 'tab' key is pressed with only whitespace character before the
    cursor, do autocompletion. Otherwise, insert indentation.

    Except for the first character at the first line. Then always do a
    completion. It doesn't make sense to start the first line with
    indentation.
    """
    def __call__(self, cli):
        b = cli.current_buffer
        before_cursor = b.document.current_line_before_cursor

        return bool(b.text and (not before_cursor or before_cursor.isspace()))


def load_python_bindings(key_bindings_manager, python_input):
    """
    Custom key bindings.
    """
    handle = key_bindings_manager.registry.add_binding
    has_selection = HasSelection()
    vi_mode_enabled = Condition(lambda cli: python_input.vi_mode)

    @handle(Keys.ControlL)
    def _(event):
        """
        Clear whole screen and render again -- also when the sidebar is visible.
        """
        event.cli.renderer.clear()

    @handle(Keys.Tab, filter= ~has_selection & TabShouldInsertWhitespaceFilter())
    def _(event):
        """
        When tab should insert whitespace, do that instead of completion.
        """
        event.cli.current_buffer.insert_text('    ')

    @handle(Keys.ControlJ, filter= ~has_selection &
            ~(vi_mode_enabled &
              ViStateFilter(key_bindings_manager.vi_state, InputMode.NAVIGATION)) &
            HasFocus('default') & IsMultiline())
    def _(event):
        """
        Behaviour of the Enter key.

        Auto indent after newline/Enter.
        (When not in Vi navigaton mode, and when multiline is enabled.)
        """
        b = event.current_buffer
        empty_lines_required = 2

        def at_the_end(b):
            """ we consider the cursor at the end when there is no text after
            the cursor, or only whitespace. """
            text = b.document.text_after_cursor
            return text == '' or (text.isspace() and not '\n' in text)

        if python_input.paste_mode:
            # In paste mode, always insert text.
            b.insert_text('\n')

        elif at_the_end(b) and b.document.text.replace(' ', '').endswith(
                    '\n' * (empty_lines_required - 1)):
            if b.validate():
                # When the cursor is at the end, and we have an empty line:
                # drop the empty lines, but return the value.
                b.document = Document(
                    text=b.text.rstrip(),
                    cursor_position=len(b.text.rstrip()))

                b.accept_action.validate_and_handle(event.cli, b)
        else:
            auto_newline(b)


def auto_newline(buffer):
    r"""
    Insert \n at the cursor position. Also add necessary padding.
    """
    insert_text = buffer.insert_text

    if buffer.document.current_line_after_cursor:
        # When we are in the middle of a line. Always insert a newline.
        insert_text('\n')
    else:
        # Go to new line, but also add indentation.
        current_line = buffer.document.current_line_before_cursor.rstrip()
        insert_text('\n')

        # Copy whitespace from current line
        for c in current_line:
            if c.isspace():
                insert_text(c)
            else:
                break

        # If the last line ends with a colon, add four extra spaces.
        if current_line[-1:] == ':':
            for x in range(4):
                insert_text(' ')

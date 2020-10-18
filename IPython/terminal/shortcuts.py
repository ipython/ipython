"""
Module to define and register Terminal IPython shortcuts with
:mod:`prompt_toolkit`
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import warnings
import signal
import sys
from typing import Callable


from jedi import Interpreter
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.filters import (has_focus, has_selection, Condition,
    vi_insert_mode, emacs_insert_mode, has_completions, completion_is_selected,  vi_mode)
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings import named_commands as nc

from IPython.utils.decorators import undoc

@undoc
@Condition
def cursor_in_leading_ws():
    before = get_app().current_buffer.document.current_line_before_cursor
    return (not before) or before.isspace()


def create_ipython_shortcuts(shell):
    """Set up the prompt_toolkit keyboard shortcuts for IPython"""

    kb = KeyBindings()
    insert_mode = vi_insert_mode | emacs_insert_mode

    if getattr(shell, 'handle_return', None):
        return_handler = shell.handle_return(shell)
    else:
        return_handler = newline_or_execute_outer(shell)

    kb.add('enter', filter=(has_focus(DEFAULT_BUFFER)
                            & ~has_selection
                            & insert_mode
                        ))(return_handler)

    def reformat_and_execute(event):
        reformat_text_before_cursor(event.current_buffer, event.current_buffer.document, shell)
        event.current_buffer.validate_and_handle()

    kb.add('escape', 'enter', filter=(has_focus(DEFAULT_BUFFER)
                            & ~has_selection
                            & insert_mode
                                      ))(reformat_and_execute)

    kb.add('c-\\')(force_exit)

    kb.add('c-p', filter=(vi_insert_mode & has_focus(DEFAULT_BUFFER))
                )(previous_history_or_previous_completion)

    kb.add('c-n', filter=(vi_insert_mode & has_focus(DEFAULT_BUFFER))
                )(next_history_or_next_completion)

    kb.add('c-g', filter=(has_focus(DEFAULT_BUFFER) & has_completions)
                )(dismiss_completion)

    kb.add('c-c', filter=has_focus(DEFAULT_BUFFER))(reset_buffer)

    kb.add('c-c', filter=has_focus(SEARCH_BUFFER))(reset_search_buffer)

    supports_suspend = Condition(lambda: hasattr(signal, 'SIGTSTP'))
    kb.add('c-z', filter=supports_suspend)(suspend_to_bg)

    # Ctrl+I == Tab
    kb.add('tab', filter=(has_focus(DEFAULT_BUFFER)
                          & ~has_selection
                          & insert_mode
                          & cursor_in_leading_ws
                        ))(indent_buffer)
    kb.add('c-o', filter=(has_focus(DEFAULT_BUFFER) & emacs_insert_mode)
           )(newline_autoindent_outer(shell.input_transformer_manager))

    kb.add('f2', filter=has_focus(DEFAULT_BUFFER))(open_input_in_editor)

    if shell.display_completions == 'readlinelike':
        kb.add('c-i', filter=(has_focus(DEFAULT_BUFFER)
                              & ~has_selection
                              & insert_mode
                              & ~cursor_in_leading_ws
                        ))(display_completions_like_readline)

    if sys.platform == "win32":
        kb.add("c-v", filter=(has_focus(DEFAULT_BUFFER) & ~vi_mode))(win_paste)

    @Condition
    def ebivim():
        return shell.emacs_bindings_in_vi_insert_mode

    focused_insert = has_focus(DEFAULT_BUFFER) & vi_insert_mode

    # Needed for to accept autosuggestions in vi insert mode
    @kb.add("c-e", filter=focused_insert & ebivim)
    def _(event):
        b = event.current_buffer
        suggestion = b.suggestion
        if suggestion:
            b.insert_text(suggestion.text)
        else:
            nc.end_of_line(event)

    @kb.add("c-f", filter=focused_insert & ebivim)
    def _(event):
        b = event.current_buffer
        suggestion = b.suggestion
        if suggestion:
            b.insert_text(suggestion.text)
        else:
            nc.forward_char(event)

    @kb.add("escape", "f", filter=focused_insert & ebivim)
    def _(event):
        b = event.current_buffer
        suggestion = b.suggestion
        if suggestion:
            t = re.split(r"(\S+\s+)", suggestion.text)
            b.insert_text(next((x for x in t if x), ""))
        else:
            nc.forward_word(event)

    # Simple Control keybindings
    key_cmd_dict = {
        "c-a": nc.beginning_of_line,
        "c-b": nc.backward_char,
        "c-k": nc.kill_line,
        "c-w": nc.backward_kill_word,
        "c-y": nc.yank,
        "c-_": nc.undo,
    }

    for key, cmd in key_cmd_dict.items():
        kb.add(key, filter=focused_insert & ebivim)(cmd)

    # Alt and Combo Control keybindings
    keys_cmd_dict = {
        # Control Combos
        ("c-x", "c-e"): nc.edit_and_execute,
        ("c-x", "e"): nc.edit_and_execute,
        # Alt
        ("escape", "b"): nc.backward_word,
        ("escape", "c"): nc.capitalize_word,
        ("escape", "d"): nc.kill_word,
        ("escape", "h"): nc.backward_kill_word,
        ("escape", "l"): nc.downcase_word,
        ("escape", "u"): nc.uppercase_word,
        ("escape", "y"): nc.yank_pop,
        ("escape", "."): nc.yank_last_arg,
    }

    for keys, cmd in keys_cmd_dict.items():
        kb.add(*keys, filter=focused_insert & ebivim)(cmd)

    if sys.platform == 'win32':
        kb.add('c-v', filter=(has_focus(DEFAULT_BUFFER) & ~vi_mode))(win_paste)

    # if settings.tab_apply_completion:
    def is_callable(text=""):
        completions = Interpreter(text, [locals()]).complete()
        match = next((i for i in completions if i.name == text), None)
        return match.type in ("class", "function") if match else None

    @Condition
    def auto_complete_selected_option_on_tab():
        return shell.auto_complete_selected_option_on_tab

    @Condition
    def auto_complete_top_option_on_enter():
        return shell.auto_complete_top_option_on_enter

    @Condition
    def auto_complete_top_option_on_tab():
        return shell.auto_complete_top_option_on_tab

    @Condition
    def auto_complete_only_option_on_tab():
        return shell.auto_complete_only_option_on_tab

    @Condition
    def auto_complete_function_parentheses():
        return shell.auto_complete_function_parentheses

    insert_mode = vi_insert_mode | emacs_insert_mode
    focused_insert = insert_mode & has_focus(DEFAULT_BUFFER)
    shown_not_selected = has_completions & ~completion_is_selected

    # apply selected completion option with enter
    @kb.add('c-j', filter=focused_insert & completion_is_selected)
    @kb.add("enter", filter=focused_insert & completion_is_selected)
    def _(event):
        b = event.current_buffer
        completion = b.complete_state.current_completion
        b.apply_completion(completion)
        if shell.auto_complete_function_parentheses:
            if is_callable(completion.text) or is_callable(b.document.get_word_under_cursor()):
                b.insert_text("()")
                b.cursor_left()

    # apply selected completion option with tab
    @kb.add("tab", filter=focused_insert & completion_is_selected & auto_complete_selected_option_on_tab)
    @kb.add("c-space", filter=focused_insert & completion_is_selected & auto_complete_selected_option_on_tab)
    def _(event):
        b = event.current_buffer
        completion = b.complete_state.current_completion
        b.apply_completion(completion)
        if shell.auto_complete_function_parentheses:
            if is_callable(completion.text) or is_callable(b.document.get_word_under_cursor()):
                b.insert_text("()")
                b.cursor_left()

    # apply first completion option with enter when completion menu is showing
    @kb.add('c-j', filter=focused_insert & shown_not_selected & auto_complete_top_option_on_enter)
    @kb.add("enter", filter=focused_insert & shown_not_selected & auto_complete_top_option_on_enter)
    def _(event):
        b = event.current_buffer
        completion = b.complete_state.completions[0]
        b.apply_completion(completion)
        if shell.auto_complete_function_parentheses:
            if is_callable(completion.text) or is_callable(b.document.get_word_under_cursor()):
                b.insert_text("()")
                b.cursor_left()

    # apply first completion option with tab if completion menu is showing
    @kb.add("tab", filter=focused_insert & shown_not_selected & auto_complete_top_option_on_tab)
    @kb.add("c-space", filter=focused_insert & shown_not_selected & auto_complete_top_option_on_tab)
    def _(event):
        b = event.current_buffer
        completion = b.complete_state.completions[0]
        b.apply_completion(completion)
        if shell.auto_complete_function_parentheses:
            if is_callable(completion.text) or is_callable(b.document.get_word_under_cursor()):
                b.insert_text("()")
                b.cursor_left()

    # apply completion if there is only one option, otherwise start completion
    @kb.add("tab", filter=focused_insert & ~has_completions & auto_complete_only_option_on_tab)
    @kb.add("c-space", filter=focused_insert & ~has_completions & auto_complete_only_option_on_tab)
    def _(event):
        b = event.current_buffer
        complete_event = CompleteEvent(completion_requested=True)
        completions = list(b.completer.get_completions(b.document, complete_event))
        if len(completions) == 1:
            completion = completions[0]
            b.apply_completion(completion)
            if shell.auto_complete_function_parentheses:
                if is_callable(completion.text) or is_callable(b.document.get_word_under_cursor()):
                    b.insert_text("()")
                    b.cursor_left()
        else:
            b.start_completion(insert_common_part=True)

    return kb


def reformat_text_before_cursor(buffer, document, shell):
    text = buffer.delete_before_cursor(len(document.text[:document.cursor_position]))
    try:
        formatted_text = shell.reformat_handler(text)
        buffer.insert_text(formatted_text)
    except Exception as e:
        buffer.insert_text(text)


def newline_or_execute_outer(shell):

    def newline_or_execute(event):
        """When the user presses return, insert a newline or execute the code."""
        b = event.current_buffer
        d = b.document

        if b.complete_state:
            cc = b.complete_state.current_completion
            if cc:
                b.apply_completion(cc)
            else:
                b.cancel_completion()
            return

        # If there's only one line, treat it as if the cursor is at the end.
        # See https://github.com/ipython/ipython/issues/10425
        if d.line_count == 1:
            check_text = d.text
        else:
            check_text = d.text[:d.cursor_position]
        status, indent = shell.check_complete(check_text)
       
        # if all we have after the cursor is whitespace: reformat current text
        # before cursor
        after_cursor = d.text[d.cursor_position:]
        reformatted = False
        if not after_cursor.strip():
            reformat_text_before_cursor(b, d, shell)
            reformatted = True
        if not (d.on_last_line or
                d.cursor_position_row >= d.line_count - d.empty_line_count_at_the_end()
                ):
            if shell.autoindent:
                b.insert_text('\n' + indent)
            else:
                b.insert_text('\n')
            return

        if (status != 'incomplete') and b.accept_handler:
            if not reformatted:
                reformat_text_before_cursor(b, d, shell)
            b.validate_and_handle()
        else:
            if shell.autoindent:
                b.insert_text('\n' + indent)
            else:
                b.insert_text('\n')
    return newline_or_execute


def previous_history_or_previous_completion(event):
    """
    Control-P in vi edit mode on readline is history next, unlike default prompt toolkit.

    If completer is open this still select previous completion.
    """
    event.current_buffer.auto_up()


def next_history_or_next_completion(event):
    """
    Control-N in vi edit mode on readline is history previous, unlike default prompt toolkit.

    If completer is open this still select next completion.
    """
    event.current_buffer.auto_down()


def dismiss_completion(event):
    b = event.current_buffer
    if b.complete_state:
        b.cancel_completion()


def reset_buffer(event):
    b = event.current_buffer
    if b.complete_state:
        b.cancel_completion()
    else:
        b.reset()


def reset_search_buffer(event):
    if event.current_buffer.document.text:
        event.current_buffer.reset()
    else:
        event.app.layout.focus(DEFAULT_BUFFER)

def suspend_to_bg(event):
    event.app.suspend_to_background()

def force_exit(event):
    """
    Force exit (with a non-zero return value)
    """
    sys.exit("Quit")

def indent_buffer(event):
    event.current_buffer.insert_text(' ' * 4)

@undoc
def newline_with_copy_margin(event):
    """
    DEPRECATED since IPython 6.0

    See :any:`newline_autoindent_outer` for a replacement.

    Preserve margin and cursor position when using
    Control-O to insert a newline in EMACS mode
    """
    warnings.warn("`newline_with_copy_margin(event)` is deprecated since IPython 6.0. "
      "see `newline_autoindent_outer(shell)(event)` for a replacement.",
                  DeprecationWarning, stacklevel=2)

    b = event.current_buffer
    cursor_start_pos = b.document.cursor_position_col
    b.newline(copy_margin=True)
    b.cursor_up(count=1)
    cursor_end_pos = b.document.cursor_position_col
    if cursor_start_pos != cursor_end_pos:
        pos_diff = cursor_start_pos - cursor_end_pos
        b.cursor_right(count=pos_diff)

def newline_autoindent_outer(inputsplitter) -> Callable[..., None]:
    """
    Return a function suitable for inserting a indented newline after the cursor.

    Fancier version of deprecated ``newline_with_copy_margin`` which should
    compute the correct indentation of the inserted line. That is to say, indent
    by 4 extra space after a function definition, class definition, context
    manager... And dedent by 4 space after ``pass``, ``return``, ``raise ...``.
    """

    def newline_autoindent(event):
        """insert a newline after the cursor indented appropriately."""
        b = event.current_buffer
        d = b.document

        if b.complete_state:
            b.cancel_completion()
        text = d.text[:d.cursor_position] + '\n'
        _, indent = inputsplitter.check_complete(text)
        b.insert_text('\n' + (' ' * (indent or 0)), move_cursor=False)

    return newline_autoindent


def open_input_in_editor(event):
    event.app.current_buffer.open_in_editor()


if sys.platform == 'win32':
    from IPython.core.error import TryNext
    from IPython.lib.clipboard import (ClipboardEmpty,
                                       win32_clipboard_get,
                                       tkinter_clipboard_get)

    @undoc
    def win_paste(event):
        try:
            text = win32_clipboard_get()
        except TryNext:
            try:
                text = tkinter_clipboard_get()
            except (TryNext, ClipboardEmpty):
                return
        except ClipboardEmpty:
            return
        event.current_buffer.insert_text(text.replace('\t', ' ' * 4))

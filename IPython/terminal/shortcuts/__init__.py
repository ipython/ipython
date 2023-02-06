"""
Module to define and register Terminal IPython shortcuts with
:mod:`prompt_toolkit`
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import re
import signal
import sys
import warnings
from typing import Callable, Dict, Union

from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.filters import Condition, emacs_insert_mode, has_completions
from prompt_toolkit.filters import has_focus as has_focus_impl
from prompt_toolkit.filters import (
    has_selection,
    has_suggestion,
    vi_insert_mode,
    vi_mode,
)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings import named_commands as nc
from prompt_toolkit.key_binding.bindings.completion import (
    display_completions_like_readline,
)
from prompt_toolkit.key_binding.vi_state import InputMode, ViState
from prompt_toolkit.layout.layout import FocusableElement

from IPython.terminal.shortcuts import auto_match as match
from IPython.terminal.shortcuts import auto_suggest
from IPython.utils.decorators import undoc

__all__ = ["create_ipython_shortcuts"]


@undoc
@Condition
def cursor_in_leading_ws():
    before = get_app().current_buffer.document.current_line_before_cursor
    return (not before) or before.isspace()


def has_focus(value: FocusableElement):
    """Wrapper around has_focus adding a nice `__name__` to tester function"""
    tester = has_focus_impl(value).func
    tester.__name__ = f"is_focused({value})"
    return Condition(tester)


@undoc
@Condition
def has_line_below() -> bool:
    document = get_app().current_buffer.document
    return document.cursor_position_row < len(document.lines) - 1


@undoc
@Condition
def has_line_above() -> bool:
    document = get_app().current_buffer.document
    return document.cursor_position_row != 0


def create_ipython_shortcuts(shell, for_all_platforms: bool = False) -> KeyBindings:
    """Set up the prompt_toolkit keyboard shortcuts for IPython.

    Parameters
    ----------
    shell: InteractiveShell
        The current IPython shell Instance
    for_all_platforms: bool (default false)
        This parameter is mostly used in generating the documentation
        to create the shortcut binding for all the platforms, and export
        them.

    Returns
    -------
    KeyBindings
        the keybinding instance for prompt toolkit.

    """
    # Warning: if possible, do NOT define handler functions in the locals
    # scope of this function, instead define functions in the global
    # scope, or a separate module, and include a user-friendly docstring
    # describing the action.

    kb = KeyBindings()
    insert_mode = vi_insert_mode | emacs_insert_mode

    if getattr(shell, "handle_return", None):
        return_handler = shell.handle_return(shell)
    else:
        return_handler = newline_or_execute_outer(shell)

    kb.add("enter", filter=(has_focus(DEFAULT_BUFFER) & ~has_selection & insert_mode))(
        return_handler
    )

    @Condition
    def ebivim():
        return shell.emacs_bindings_in_vi_insert_mode

    @kb.add(
        "escape",
        "enter",
        filter=(has_focus(DEFAULT_BUFFER) & ~has_selection & insert_mode & ebivim),
    )
    def reformat_and_execute(event):
        """Reformat code and execute it"""
        reformat_text_before_cursor(
            event.current_buffer, event.current_buffer.document, shell
        )
        event.current_buffer.validate_and_handle()

    kb.add("c-\\")(quit)

    kb.add("c-p", filter=(vi_insert_mode & has_focus(DEFAULT_BUFFER)))(
        previous_history_or_previous_completion
    )

    kb.add("c-n", filter=(vi_insert_mode & has_focus(DEFAULT_BUFFER)))(
        next_history_or_next_completion
    )

    kb.add("c-g", filter=(has_focus(DEFAULT_BUFFER) & has_completions))(
        dismiss_completion
    )

    kb.add("c-c", filter=has_focus(DEFAULT_BUFFER))(reset_buffer)

    kb.add("c-c", filter=has_focus(SEARCH_BUFFER))(reset_search_buffer)

    supports_suspend = Condition(lambda: hasattr(signal, "SIGTSTP"))
    kb.add("c-z", filter=supports_suspend)(suspend_to_bg)

    # Ctrl+I == Tab
    kb.add(
        "tab",
        filter=(
            has_focus(DEFAULT_BUFFER)
            & ~has_selection
            & insert_mode
            & cursor_in_leading_ws
        ),
    )(indent_buffer)
    kb.add("c-o", filter=(has_focus(DEFAULT_BUFFER) & emacs_insert_mode))(
        newline_autoindent_outer(shell.input_transformer_manager)
    )

    kb.add("f2", filter=has_focus(DEFAULT_BUFFER))(open_input_in_editor)

    @Condition
    def auto_match():
        return shell.auto_match

    def all_quotes_paired(quote, buf):
        paired = True
        i = 0
        while i < len(buf):
            c = buf[i]
            if c == quote:
                paired = not paired
            elif c == "\\":
                i += 1
            i += 1
        return paired

    focused_insert = (vi_insert_mode | emacs_insert_mode) & has_focus(DEFAULT_BUFFER)
    _preceding_text_cache: Dict[Union[str, Callable], Condition] = {}
    _following_text_cache: Dict[Union[str, Callable], Condition] = {}

    def preceding_text(pattern: Union[str, Callable]):
        if pattern in _preceding_text_cache:
            return _preceding_text_cache[pattern]

        if callable(pattern):

            def _preceding_text():
                app = get_app()
                before_cursor = app.current_buffer.document.current_line_before_cursor
                # mypy can't infer if(callable): https://github.com/python/mypy/issues/3603
                return bool(pattern(before_cursor))  # type: ignore[operator]

        else:
            m = re.compile(pattern)

            def _preceding_text():
                app = get_app()
                before_cursor = app.current_buffer.document.current_line_before_cursor
                return bool(m.match(before_cursor))

            _preceding_text.__name__ = f"preceding_text({pattern!r})"

        condition = Condition(_preceding_text)
        _preceding_text_cache[pattern] = condition
        return condition

    def following_text(pattern):
        try:
            return _following_text_cache[pattern]
        except KeyError:
            pass
        m = re.compile(pattern)

        def _following_text():
            app = get_app()
            return bool(m.match(app.current_buffer.document.current_line_after_cursor))

        _following_text.__name__ = f"following_text({pattern!r})"

        condition = Condition(_following_text)
        _following_text_cache[pattern] = condition
        return condition

    @Condition
    def not_inside_unclosed_string():
        app = get_app()
        s = app.current_buffer.document.text_before_cursor
        # remove escaped quotes
        s = s.replace('\\"', "").replace("\\'", "")
        # remove triple-quoted string literals
        s = re.sub(r"(?:\"\"\"[\s\S]*\"\"\"|'''[\s\S]*''')", "", s)
        # remove single-quoted string literals
        s = re.sub(r"""(?:"[^"]*["\n]|'[^']*['\n])""", "", s)
        return not ('"' in s or "'" in s)

    # auto match
    for key, cmd in match.auto_match_parens.items():
        kb.add(key, filter=focused_insert & auto_match & following_text(r"[,)}\]]|$"))(
            cmd
        )

    # raw string
    for key, cmd in match.auto_match_parens_raw_string.items():
        kb.add(
            key,
            filter=focused_insert & auto_match & preceding_text(r".*(r|R)[\"'](-*)$"),
        )(cmd)

    kb.add(
        '"',
        filter=focused_insert
        & auto_match
        & not_inside_unclosed_string
        & preceding_text(lambda line: all_quotes_paired('"', line))
        & following_text(r"[,)}\]]|$"),
    )(match.double_quote)

    kb.add(
        "'",
        filter=focused_insert
        & auto_match
        & not_inside_unclosed_string
        & preceding_text(lambda line: all_quotes_paired("'", line))
        & following_text(r"[,)}\]]|$"),
    )(match.single_quote)

    kb.add(
        '"',
        filter=focused_insert
        & auto_match
        & not_inside_unclosed_string
        & preceding_text(r'^.*""$'),
    )(match.docstring_double_quotes)

    kb.add(
        "'",
        filter=focused_insert
        & auto_match
        & not_inside_unclosed_string
        & preceding_text(r"^.*''$"),
    )(match.docstring_single_quotes)

    # just move cursor
    kb.add(")", filter=focused_insert & auto_match & following_text(r"^\)"))(
        match.skip_over
    )
    kb.add("]", filter=focused_insert & auto_match & following_text(r"^\]"))(
        match.skip_over
    )
    kb.add("}", filter=focused_insert & auto_match & following_text(r"^\}"))(
        match.skip_over
    )
    kb.add('"', filter=focused_insert & auto_match & following_text('^"'))(
        match.skip_over
    )
    kb.add("'", filter=focused_insert & auto_match & following_text("^'"))(
        match.skip_over
    )

    kb.add(
        "backspace",
        filter=focused_insert
        & preceding_text(r".*\($")
        & auto_match
        & following_text(r"^\)"),
    )(match.delete_pair)
    kb.add(
        "backspace",
        filter=focused_insert
        & preceding_text(r".*\[$")
        & auto_match
        & following_text(r"^\]"),
    )(match.delete_pair)
    kb.add(
        "backspace",
        filter=focused_insert
        & preceding_text(r".*\{$")
        & auto_match
        & following_text(r"^\}"),
    )(match.delete_pair)
    kb.add(
        "backspace",
        filter=focused_insert
        & preceding_text('.*"$')
        & auto_match
        & following_text('^"'),
    )(match.delete_pair)
    kb.add(
        "backspace",
        filter=focused_insert
        & preceding_text(r".*'$")
        & auto_match
        & following_text(r"^'"),
    )(match.delete_pair)

    if shell.display_completions == "readlinelike":
        kb.add(
            "c-i",
            filter=(
                has_focus(DEFAULT_BUFFER)
                & ~has_selection
                & insert_mode
                & ~cursor_in_leading_ws
            ),
        )(display_completions_like_readline)

    if sys.platform == "win32" or for_all_platforms:
        kb.add("c-v", filter=(has_focus(DEFAULT_BUFFER) & ~vi_mode))(win_paste)

    focused_insert_vi = has_focus(DEFAULT_BUFFER) & vi_insert_mode

    # autosuggestions
    @Condition
    def navigable_suggestions():
        return isinstance(
            shell.auto_suggest, auto_suggest.NavigableAutoSuggestFromHistory
        )

    kb.add("end", filter=has_focus(DEFAULT_BUFFER) & (ebivim | ~vi_insert_mode))(
        auto_suggest.accept_in_vi_insert_mode
    )
    kb.add("c-e", filter=focused_insert_vi & ebivim)(
        auto_suggest.accept_in_vi_insert_mode
    )
    kb.add("c-f", filter=focused_insert_vi)(auto_suggest.accept)
    kb.add("escape", "f", filter=focused_insert_vi & ebivim)(auto_suggest.accept_word)
    kb.add("c-right", filter=has_suggestion & has_focus(DEFAULT_BUFFER))(
        auto_suggest.accept_token
    )
    kb.add(
        "escape", filter=has_suggestion & has_focus(DEFAULT_BUFFER) & emacs_insert_mode
    )(auto_suggest.discard)
    kb.add(
        "up",
        filter=navigable_suggestions
        & ~has_line_above
        & has_suggestion
        & has_focus(DEFAULT_BUFFER),
    )(auto_suggest.swap_autosuggestion_up(shell.auto_suggest))
    kb.add(
        "down",
        filter=navigable_suggestions
        & ~has_line_below
        & has_suggestion
        & has_focus(DEFAULT_BUFFER),
    )(auto_suggest.swap_autosuggestion_down(shell.auto_suggest))
    kb.add(
        "up", filter=has_line_above & navigable_suggestions & has_focus(DEFAULT_BUFFER)
    )(auto_suggest.up_and_update_hint)
    kb.add(
        "down",
        filter=has_line_below & navigable_suggestions & has_focus(DEFAULT_BUFFER),
    )(auto_suggest.down_and_update_hint)
    kb.add("right", filter=has_suggestion & has_focus(DEFAULT_BUFFER))(
        auto_suggest.accept_character
    )
    kb.add("c-left", filter=has_suggestion & has_focus(DEFAULT_BUFFER))(
        auto_suggest.accept_and_move_cursor_left
    )
    kb.add("c-down", filter=has_suggestion & has_focus(DEFAULT_BUFFER))(
        auto_suggest.accept_and_keep_cursor
    )
    kb.add("backspace", filter=has_suggestion & has_focus(DEFAULT_BUFFER))(
        auto_suggest.backspace_and_resume_hint
    )

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
        kb.add(key, filter=focused_insert_vi & ebivim)(cmd)

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
        kb.add(*keys, filter=focused_insert_vi & ebivim)(cmd)

    def get_input_mode(self):
        app = get_app()
        app.ttimeoutlen = shell.ttimeoutlen
        app.timeoutlen = shell.timeoutlen

        return self._input_mode

    def set_input_mode(self, mode):
        shape = {InputMode.NAVIGATION: 2, InputMode.REPLACE: 4}.get(mode, 6)
        cursor = "\x1b[{} q".format(shape)

        sys.stdout.write(cursor)
        sys.stdout.flush()

        self._input_mode = mode

    if shell.editing_mode == "vi" and shell.modal_cursor:
        ViState._input_mode = InputMode.INSERT  # type: ignore
        ViState.input_mode = property(get_input_mode, set_input_mode)  # type: ignore
    return kb


def reformat_text_before_cursor(buffer, document, shell):
    text = buffer.delete_before_cursor(len(document.text[: document.cursor_position]))
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
            check_text = d.text[: d.cursor_position]
        status, indent = shell.check_complete(check_text)

        # if all we have after the cursor is whitespace: reformat current text
        # before cursor
        after_cursor = d.text[d.cursor_position :]
        reformatted = False
        if not after_cursor.strip():
            reformat_text_before_cursor(b, d, shell)
            reformatted = True
        if not (
            d.on_last_line
            or d.cursor_position_row >= d.line_count - d.empty_line_count_at_the_end()
        ):
            if shell.autoindent:
                b.insert_text("\n" + indent)
            else:
                b.insert_text("\n")
            return

        if (status != "incomplete") and b.accept_handler:
            if not reformatted:
                reformat_text_before_cursor(b, d, shell)
            b.validate_and_handle()
        else:
            if shell.autoindent:
                b.insert_text("\n" + indent)
            else:
                b.insert_text("\n")

    newline_or_execute.__qualname__ = "newline_or_execute"

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
    """Dismiss completion"""
    b = event.current_buffer
    if b.complete_state:
        b.cancel_completion()


def reset_buffer(event):
    """Reset buffer"""
    b = event.current_buffer
    if b.complete_state:
        b.cancel_completion()
    else:
        b.reset()


def reset_search_buffer(event):
    """Reset search buffer"""
    if event.current_buffer.document.text:
        event.current_buffer.reset()
    else:
        event.app.layout.focus(DEFAULT_BUFFER)


def suspend_to_bg(event):
    """Suspend to background"""
    event.app.suspend_to_background()


def quit(event):
    """
    Quit application with ``SIGQUIT`` if supported or ``sys.exit`` otherwise.

    On platforms that support SIGQUIT, send SIGQUIT to the current process.
    On other platforms, just exit the process with a message.
    """
    sigquit = getattr(signal, "SIGQUIT", None)
    if sigquit is not None:
        os.kill(0, signal.SIGQUIT)
    else:
        sys.exit("Quit")


def indent_buffer(event):
    """Indent buffer"""
    event.current_buffer.insert_text(" " * 4)


@undoc
def newline_with_copy_margin(event):
    """
    DEPRECATED since IPython 6.0

    See :any:`newline_autoindent_outer` for a replacement.

    Preserve margin and cursor position when using
    Control-O to insert a newline in EMACS mode
    """
    warnings.warn(
        "`newline_with_copy_margin(event)` is deprecated since IPython 6.0. "
        "see `newline_autoindent_outer(shell)(event)` for a replacement.",
        DeprecationWarning,
        stacklevel=2,
    )

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
        """Insert a newline after the cursor indented appropriately."""
        b = event.current_buffer
        d = b.document

        if b.complete_state:
            b.cancel_completion()
        text = d.text[: d.cursor_position] + "\n"
        _, indent = inputsplitter.check_complete(text)
        b.insert_text("\n" + (" " * (indent or 0)), move_cursor=False)

    newline_autoindent.__qualname__ = "newline_autoindent"

    return newline_autoindent


def open_input_in_editor(event):
    """Open code from input in external editor"""
    event.app.current_buffer.open_in_editor()


if sys.platform == "win32":
    from IPython.core.error import TryNext
    from IPython.lib.clipboard import (
        ClipboardEmpty,
        tkinter_clipboard_get,
        win32_clipboard_get,
    )

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
        event.current_buffer.insert_text(text.replace("\t", " " * 4))

else:

    @undoc
    def win_paste(event):
        """Stub used when auto-generating shortcuts for documentation"""
        pass

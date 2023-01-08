import pytest
from IPython.terminal.shortcuts.autosuggestions import (
    accept_in_vi_insert_mode,
    accept_token,
)

from unittest.mock import patch, Mock


def make_event(text, cursor, suggestion):
    event = Mock()
    event.current_buffer = Mock()
    event.current_buffer.suggestion = Mock()
    event.current_buffer.text = text
    event.current_buffer.cursor_position = cursor
    event.current_buffer.suggestion.text = suggestion
    event.current_buffer.document = Mock()
    event.current_buffer.document.get_end_of_line_position = Mock(return_value=0)
    event.current_buffer.document.text = text
    event.current_buffer.document.cursor_position = cursor
    return event


@pytest.mark.parametrize(
    "text, cursor, suggestion, called",
    [
        ("123456", 6, "123456789", True),
        ("123456", 3, "123456789", False),
        ("123456   \n789", 6, "123456789", True),
    ],
)
def test_autosuggest_at_EOL(text, cursor, suggestion, called):
    """
    test that autosuggest is only applied at end of line.
    """

    event = make_event(text, cursor, suggestion)
    event.current_buffer.insert_text = Mock()
    accept_in_vi_insert_mode(event)
    if called:
        event.current_buffer.insert_text.assert_called()
    else:
        event.current_buffer.insert_text.assert_not_called()
        # event.current_buffer.document.get_end_of_line_position.assert_called()


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "def "),
        ("d", "ef out(tag: str, n=50):", "ef "),
        ("de ", "f out(tag: str, n=50):", "f "),
        ("def", " out(tag: str, n=50):", " "),
        ("def ", "out(tag: str, n=50):", "out("),
        ("def o", "ut(tag: str, n=50):", "ut("),
        ("def ou", "t(tag: str, n=50):", "t("),
        ("def out", "(tag: str, n=50):", "("),
        ("def out(", "tag: str, n=50):", "tag: "),
        ("def out(t", "ag: str, n=50):", "ag: "),
        ("def out(ta", "g: str, n=50):", "g: "),
        ("def out(tag", ": str, n=50):", ": "),
        ("def out(tag:", " str, n=50):", " "),
        ("def out(tag: ", "str, n=50):", "str, "),
        ("def out(tag: s", "tr, n=50):", "tr, "),
        ("def out(tag: st", "r, n=50):", "r, "),
        ("def out(tag: str", ", n=50):", ", n"),
        ("def out(tag: str,", " n=50):", " n"),
        ("def out(tag: str, ", "n=50):", "n="),
        ("def out(tag: str, n", "=50):", "="),
        ("def out(tag: str, n=", "50):", "50)"),
        ("def out(tag: str, n=5", "0):", "0)"),
        ("def out(tag: str, n=50", "):", "):"),
        ("def out(tag: str, n=50)", ":", ":"),
    ],
)
def test_autosuggest_token(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    event.current_buffer.insert_text = Mock()
    accept_token(event)
    assert event.current_buffer.insert_text.called
    assert event.current_buffer.insert_text.call_args[0] == (expected,)


def test_autosuggest_token_empty():
    full = "def out(tag: str, n=50):"
    event = make_event(full, len(full), "")
    event.current_buffer.insert_text = Mock()

    with patch(
        "prompt_toolkit.key_binding.bindings.named_commands.forward_word"
    ) as forward_word:
        accept_token(event)
        assert not event.current_buffer.insert_text.called
        assert forward_word.called

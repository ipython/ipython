import pytest
from IPython.terminal.shortcuts.auto_suggest import (
    accept,
    accept_in_vi_insert_mode,
    accept_token,
    accept_character,
    accept_word,
    accept_and_keep_cursor,
    discard,
    NavigableAutoSuggestFromHistory,
    swap_autosuggestion_up,
    swap_autosuggestion_down,
)

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from unittest.mock import patch, Mock


def make_event(text, cursor, suggestion):
    event = Mock()
    event.current_buffer = Mock()
    event.current_buffer.suggestion = Mock()
    event.current_buffer.text = text
    event.current_buffer.cursor_position = cursor
    event.current_buffer.suggestion.text = suggestion
    event.current_buffer.document = Document(text=text, cursor_position=cursor)
    return event


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "def out(tag: str, n=50):"),
        ("def ", "out(tag: str, n=50):", "out(tag: str, n=50):"),
    ],
)
def test_accept(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    buffer = event.current_buffer
    buffer.insert_text = Mock()
    accept(event)
    assert buffer.insert_text.called
    assert buffer.insert_text.call_args[0] == (expected,)


@pytest.mark.parametrize(
    "text, suggestion",
    [
        ("", "def out(tag: str, n=50):"),
        ("def ", "out(tag: str, n=50):"),
    ],
)
def test_discard(text, suggestion):
    event = make_event(text, len(text), suggestion)
    buffer = event.current_buffer
    buffer.insert_text = Mock()
    discard(event)
    assert not buffer.insert_text.called
    assert buffer.suggestion is None


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


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "d"),
        ("d", "ef out(tag: str, n=50):", "e"),
        ("de ", "f out(tag: str, n=50):", "f"),
        ("def", " out(tag: str, n=50):", " "),
    ],
)
def test_accept_character(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    event.current_buffer.insert_text = Mock()
    accept_character(event)
    assert event.current_buffer.insert_text.called
    assert event.current_buffer.insert_text.call_args[0] == (expected,)


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "def "),
        ("d", "ef out(tag: str, n=50):", "ef "),
        ("de", "f out(tag: str, n=50):", "f "),
        ("def", " out(tag: str, n=50):", " "),
        # (this is why we also have accept_token)
        ("def ", "out(tag: str, n=50):", "out(tag: "),
    ],
)
def test_accept_word(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    event.current_buffer.insert_text = Mock()
    accept_word(event)
    assert event.current_buffer.insert_text.called
    assert event.current_buffer.insert_text.call_args[0] == (expected,)


@pytest.mark.parametrize(
    "text, suggestion, expected, cursor",
    [
        ("", "def out(tag: str, n=50):", "def out(tag: str, n=50):", 0),
        ("def ", "out(tag: str, n=50):", "out(tag: str, n=50):", 4),
    ],
)
def test_accept_and_keep_cursor(text, suggestion, expected, cursor):
    event = make_event(text, cursor, suggestion)
    buffer = event.current_buffer
    buffer.insert_text = Mock()
    accept_and_keep_cursor(event)
    assert buffer.insert_text.called
    assert buffer.insert_text.call_args[0] == (expected,)
    assert buffer.cursor_position == cursor


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


def test_other_providers():
    """Ensure that swapping autosuggestions does not break with other providers"""
    provider = AutoSuggestFromHistory()
    up = swap_autosuggestion_up(provider)
    down = swap_autosuggestion_down(provider)
    event = Mock()
    event.current_buffer = Buffer()
    assert up(event) is None
    assert down(event) is None


async def test_navigable_provider():
    provider = NavigableAutoSuggestFromHistory()
    history = InMemoryHistory(history_strings=["very_a", "very", "very_b", "very_c"])
    buffer = Buffer(history=history)

    async for _ in history.load():
        pass

    buffer.cursor_position = 5
    buffer.text = "very"

    up = swap_autosuggestion_up(provider)
    down = swap_autosuggestion_down(provider)

    event = Mock()
    event.current_buffer = buffer

    def get_suggestion():
        suggestion = provider.get_suggestion(buffer, buffer.document)
        buffer.suggestion = suggestion
        return suggestion

    assert get_suggestion().text == "_c"

    # should go up
    up(event)
    assert get_suggestion().text == "_b"

    # should skip over 'very' which is identical to buffer content
    up(event)
    assert get_suggestion().text == "_a"

    # should cycle back to beginning
    up(event)
    assert get_suggestion().text == "_c"

    # should cycle back through end boundary
    down(event)
    assert get_suggestion().text == "_a"

    down(event)
    assert get_suggestion().text == "_b"

    down(event)
    assert get_suggestion().text == "_c"

    down(event)
    assert get_suggestion().text == "_a"


async def test_navigable_provider_multiline_entries():
    provider = NavigableAutoSuggestFromHistory()
    history = InMemoryHistory(history_strings=["very_a\nvery_b", "very_c"])
    buffer = Buffer(history=history)

    async for _ in history.load():
        pass

    buffer.cursor_position = 5
    buffer.text = "very"
    up = swap_autosuggestion_up(provider)
    down = swap_autosuggestion_down(provider)

    event = Mock()
    event.current_buffer = buffer

    def get_suggestion():
        suggestion = provider.get_suggestion(buffer, buffer.document)
        buffer.suggestion = suggestion
        return suggestion

    assert get_suggestion().text == "_c"

    up(event)
    assert get_suggestion().text == "_b"

    up(event)
    assert get_suggestion().text == "_a"

    down(event)
    assert get_suggestion().text == "_b"

    down(event)
    assert get_suggestion().text == "_c"


def create_session_mock():
    session = Mock()
    session.default_buffer = Buffer()
    return session


def test_navigable_provider_connection():
    provider = NavigableAutoSuggestFromHistory()
    provider.skip_lines = 1

    session_1 = create_session_mock()
    provider.connect(session_1)

    assert provider.skip_lines == 1
    session_1.default_buffer.on_text_insert.fire()
    assert provider.skip_lines == 0

    session_2 = create_session_mock()
    provider.connect(session_2)
    provider.skip_lines = 2

    assert provider.skip_lines == 2
    session_2.default_buffer.on_text_insert.fire()
    assert provider.skip_lines == 0

    provider.skip_lines = 3
    provider.disconnect()
    session_1.default_buffer.on_text_insert.fire()
    session_2.default_buffer.on_text_insert.fire()
    assert provider.skip_lines == 3

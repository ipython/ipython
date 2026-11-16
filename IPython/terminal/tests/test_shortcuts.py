"""Tests for IPython.terminal.shortcuts."""

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document

from IPython.terminal.shortcuts import reformat_text_before_cursor


class _Shell:
    def __init__(self, handler):
        self.reformat_handler = handler


def _buffer_with_text(text):
    buffer = Buffer()
    buffer.document = Document(text, len(text))
    return buffer


def test_reformat_text_before_cursor_does_not_touch_unchanged_buffer():
    """A no-op reformat must not emit text change events.

    The dumb prompt echoes the last character on every text change, so a
    delete-and-reinsert of identical text duplicates that character.
    """
    buffer = _buffer_with_text("exit")
    echoes = []
    buffer.on_text_changed += lambda _: echoes.append(
        buffer.document.text_before_cursor[-1:]
    )

    reformat_text_before_cursor(buffer, buffer.document, _Shell(lambda text: text))

    assert buffer.text == "exit"
    assert echoes == []


def test_reformat_text_before_cursor_still_updates_changed_text():
    buffer = _buffer_with_text("x=1")

    reformat_text_before_cursor(buffer, buffer.document, _Shell(lambda text: "x = 1"))

    assert buffer.text == "x = 1"

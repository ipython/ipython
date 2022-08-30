import pytest
from IPython.terminal.shortcuts import _apply_autosuggest

from unittest.mock import Mock


def make_event(text, cursor, suggestion):
    event = Mock()
    event.current_buffer = Mock()
    event.current_buffer.suggestion = Mock()
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
    _apply_autosuggest(event)
    if called:
        event.current_buffer.insert_text.assert_called()
    else:
        event.current_buffer.insert_text.assert_not_called()
        # event.current_buffer.document.get_end_of_line_position.assert_called()

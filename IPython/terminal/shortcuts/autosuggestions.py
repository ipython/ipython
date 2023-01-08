import re
from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.key_binding.bindings import named_commands as nc


# Needed for to accept autosuggestions in vi insert mode
def accept_in_vi_insert_mode(event: KeyPressEvent):
    """Apply autosuggestion if at end of line."""
    b = event.current_buffer
    d = b.document
    after_cursor = d.text[d.cursor_position :]
    lines = after_cursor.split("\n")
    end_of_current_line = lines[0].strip()
    suggestion = b.suggestion
    if (suggestion is not None) and (suggestion.text) and (end_of_current_line == ""):
        b.insert_text(suggestion.text)
    else:
        nc.end_of_line(event)


def accept(event):
    """Accept suggestion"""
    b = event.current_buffer
    suggestion = b.suggestion
    if suggestion:
        b.insert_text(suggestion.text)
    else:
        nc.forward_char(event)


def accept_word(event):
    """Fill partial suggestion by word"""
    b = event.current_buffer
    suggestion = b.suggestion
    if suggestion:
        t = re.split(r"(\S+\s+)", suggestion.text)
        b.insert_text(next((x for x in t if x), ""))
    else:
        nc.forward_word(event)

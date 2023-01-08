import re
import tokenize
from io import StringIO
from typing import List, Optional

from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.key_binding.bindings import named_commands as nc

from IPython.utils.tokenutil import generate_tokens


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


def accept(event: KeyPressEvent):
    """Accept suggestion"""
    b = event.current_buffer
    suggestion = b.suggestion
    if suggestion:
        b.insert_text(suggestion.text)
    else:
        nc.forward_char(event)


def accept_word(event: KeyPressEvent):
    """Fill partial suggestion by word"""
    b = event.current_buffer
    suggestion = b.suggestion
    if suggestion:
        t = re.split(r"(\S+\s+)", suggestion.text)
        b.insert_text(next((x for x in t if x), ""))
    else:
        nc.forward_word(event)


def accept_token(event: KeyPressEvent):
    """Fill partial suggestion by token"""
    b = event.current_buffer
    suggestion = b.suggestion

    if suggestion:
        prefix = b.text
        text = prefix + suggestion.text

        tokens: List[Optional[str]] = [None, None, None]
        substings = [""]
        i = 0

        for token in generate_tokens(StringIO(text).readline):
            if token.type == tokenize.NEWLINE:
                index = len(text)
            else:
                index = text.index(token[1], len(substings[-1]))
            substings.append(text[:index])
            tokenized_so_far = substings[-1]
            if tokenized_so_far.startswith(prefix):
                if i == 0 and len(tokenized_so_far) > len(prefix):
                    tokens[0] = tokenized_so_far[len(prefix) :]
                    substings.append(tokenized_so_far)
                    i += 1
                tokens[i] = token[1]
                if i == 2:
                    break
                i += 1

        if tokens[0]:
            to_insert: str
            insert_text = substings[-2]
            if tokens[1] and len(tokens[1]) == 1:
                insert_text = substings[-1]
            to_insert = insert_text[len(prefix) :]
            b.insert_text(to_insert)
            return

    nc.forward_word(event)

import re

__all__ = (
    'has_unclosed_brackets',
    'document_is_multiline_python',
)


def has_unclosed_brackets(text):
    """
    Starting at the end of the string. If we find an opening bracket
    for which we didn't had a closing one yet, return True.
    """
    stack = []

    # Ignore braces inside strings
    text = re.sub(r'''('[^']*'|"[^"]*")''', '', text)  # XXX: handle escaped quotes.!

    for c in reversed(text):
        if c in '])}':
            stack.append(c)

        elif c in '[({':
            if stack:
                if ((c == '[' and stack[-1] == ']') or
                        (c == '{' and stack[-1] == '}') or
                        (c == '(' and stack[-1] == ')')):
                    stack.pop()
            else:
                # Opening bracket for which we didn't had a closing one.
                return True

    return False


_multiline_string_delims = re.compile('''[']{3}|["]{3}''')


def document_is_multiline_python(document):
    """
    Determine whether this is a multiline Python document.
    """
    def ends_in_multiline_string():
        """
        ``True`` if we're inside a multiline string at the end of the text.
        """
        delims = _multiline_string_delims.findall(document.text)
        opening = None
        for delim in delims:
            if opening is None:
                opening = delim
            elif delim == opening:
                opening = None
        return bool(opening)

    if '\n' in document.text or ends_in_multiline_string():
        return True

    # If we just typed a colon, or still have open brackets, always insert a real newline.
    if document.text_before_cursor.rstrip()[-1:] == ':' or \
            (document.is_cursor_at_the_end and
             has_unclosed_brackets(document.text_before_cursor)) or \
            document.text.startswith('@'):
        return True

    # If the character before the cursor is a backslash (line continuation
    # char), insert a new line.
    elif document.text_before_cursor[-1:] == '\\':
        return True

    return False

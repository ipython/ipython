"""
Tools to open .py files as Unicode, using the encoding specified within the file,
as per PEP 263.

Much of the code is taken from the tokenize module in Python 3.2.
"""
from __future__ import annotations

import io
import warnings
from collections.abc import Iterator
from io import BytesIO, TextIOBase, TextIOWrapper
from pathlib import Path
import re
from tokenize import detect_encoding, open

cookie_re = re.compile(r"coding[:=]\s*([-\w.]+)", re.UNICODE)
cookie_comment_re = re.compile(r"^\s*#.*coding[:=]\s*([-\w.]+)", re.UNICODE)

def source_to_unicode(
    txt: bytes | BytesIO | str, errors: str = "replace", skip_encoding_cookie: bool = True
) -> str:
    """Converts bytes or a BytesIO buffer with python source code to unicode.

    Byte strings are checked for the python source file encoding cookie to
    determine encoding.

    Parameters
    ----------
    txt : bytes | BytesIO | str
        The source code as bytes or a BytesIO buffer. Passing a str is
        deprecated and will emit a warning.
    errors : str
        How to handle decoding errors. Default is "replace".
    skip_encoding_cookie : bool
        If True (default), skip the encoding declaration line if found.

    Returns
    -------
    str
        The decoded unicode string.

    .. deprecated:: 9.0
        Passing a str to this function is deprecated. If you already have
        a string, you don't need to call this function.
    """
    # Handle deprecated str input for backward compatibility
    if isinstance(txt, str):
        warnings.warn(
            "Passing a str to source_to_unicode is deprecated. "
            "If you already have a string, you don't need to call this function.",
            DeprecationWarning,
            stacklevel=2,
        )
        return txt
    
    if isinstance(txt, bytes):
        buffer = BytesIO(txt)
    else:
        buffer = txt
    try:
        encoding, _ = detect_encoding(buffer.readline)
    except SyntaxError:
        encoding = "ascii"
    buffer.seek(0)
    with TextIOWrapper(buffer, encoding, errors=errors, line_buffering=True) as text:
        if skip_encoding_cookie:
            return "".join(strip_encoding_cookie(text))
        else:
            return text.read()

def strip_encoding_cookie(filelike: Iterator[str] | io.TextIOBase) -> Iterator[str]:
    """Generator to pull lines from a text-mode file, skipping the encoding
    cookie if it is found in the first two lines.
    """
    it: Iterator[str] = iter(filelike)
    try:
        first = next(it)
        if not cookie_comment_re.match(first):
            yield first
        second = next(it)
        if not cookie_comment_re.match(second):
            yield second
    except StopIteration:
        return
    
    yield from it

def read_py_file(filename: str | Path, skip_encoding_cookie: bool = True) -> str:
    """Read a Python file, using the encoding declared inside the file.

    Parameters
    ----------
    filename : str
        The path to the file to read.
    skip_encoding_cookie : bool
        If True (the default), and the encoding declaration is found in the first
        two lines, that line will be excluded from the output.

    Returns
    -------
    A unicode string containing the contents of the file.
    """
    filepath = Path(filename)
    with open(filepath) as f:  # the open function defined in this module.
        if skip_encoding_cookie:
            return "".join(strip_encoding_cookie(f))
        else:
            return f.read()

def read_py_url(url: str, errors: str = "replace", skip_encoding_cookie: bool = True) -> str:
    """Read a Python file from a URL, using the encoding declared inside the file.

    Parameters
    ----------
    url : str
        The URL from which to fetch the file.
    errors : str
        How to handle decoding errors in the file. Options are the same as for
        bytes.decode(), but here 'replace' is the default.
    skip_encoding_cookie : bool
        If True (the default), and the encoding declaration is found in the first
        two lines, that line will be excluded from the output.

    Returns
    -------
    A unicode string containing the contents of the file.
    """
    # Deferred import for faster start
    from urllib.request import urlopen 
    response = urlopen(url)
    data: bytes = response.read()
    buffer = io.BytesIO(data)
    result: str = source_to_unicode(buffer, errors, skip_encoding_cookie)
    # Ensure we return a string, not bytes
    assert isinstance(result, str), "source_to_unicode must return a string"
    return result

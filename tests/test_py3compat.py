"""Tests for IPython.utils.py3compat"""
import pytest
from IPython.utils.py3compat import decode, encode, cast_unicode, safe_unicode, PYPY


# ---------------------------------------------------------------------------
# decode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("data,encoding,expected", [
    (b"hello", "utf-8", "hello"),
    (b"hello", None, "hello"),
    ("already str".encode("utf-8"), "utf-8", "already str"),
    (b"\xff\xfe", "utf-8", "��"),  # invalid UTF-8 replaced
])
def test_decode(data, encoding, expected):
    assert decode(data, encoding) == expected


# ---------------------------------------------------------------------------
# encode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("data,encoding,expected", [
    ("hello", "utf-8", b"hello"),
    ("hello", None, "hello".encode()),
    ("café", "ascii", b"caf?"),  # unencodable char replaced
])
def test_encode(data, encoding, expected):
    assert encode(data, encoding) == expected


# ---------------------------------------------------------------------------
# cast_unicode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("data,expected_type", [
    (b"bytes input", str),
    ("str input", str),
    ("", str),
    (b"", str),
])
def test_cast_unicode_returns_str(data, expected_type):
    result = cast_unicode(data)
    assert isinstance(result, expected_type)


def test_cast_unicode_passthrough_str():
    s = "already unicode"
    assert cast_unicode(s) is s


def test_cast_unicode_decodes_bytes():
    assert cast_unicode(b"hello") == "hello"


# ---------------------------------------------------------------------------
# safe_unicode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("obj,expected", [
    (42, "42"),
    ("hello", "hello"),
    (3.14, "3.14"),
    (None, "None"),
    ([1, 2], "[1, 2]"),
])
def test_safe_unicode_basic(obj, expected):
    assert safe_unicode(obj) == expected


def test_safe_unicode_exception():
    exc = ValueError("something went wrong")
    result = safe_unicode(exc)
    assert "something went wrong" in result


# ---------------------------------------------------------------------------
# PYPY constant
# ---------------------------------------------------------------------------

def test_pypy_is_bool():
    assert isinstance(PYPY, bool)

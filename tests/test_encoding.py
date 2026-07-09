"""Tests for IPython.utils.encoding."""

import sys
import warnings
from unittest import mock

import pytest

from IPython.utils.encoding import DEFAULT_ENCODING, get_stream_enc, getdefaultencoding


# ---------------------------------------------------------------------------
# get_stream_enc
# ---------------------------------------------------------------------------


def test_get_stream_enc_returns_encoding_attribute():
    stream = mock.Mock(encoding="utf-8")
    assert get_stream_enc(stream) == "utf-8"


def test_get_stream_enc_no_encoding_attribute_returns_default():
    stream = mock.Mock(spec=[])  # no attributes
    assert get_stream_enc(stream) is None


def test_get_stream_enc_no_encoding_attribute_uses_default_arg():
    stream = mock.Mock(spec=[])
    assert get_stream_enc(stream, default="latin-1") == "latin-1"


def test_get_stream_enc_empty_encoding_returns_default():
    stream = mock.Mock(encoding="")
    assert get_stream_enc(stream) is None


def test_get_stream_enc_none_encoding_returns_default():
    stream = mock.Mock(encoding=None)
    assert get_stream_enc(stream) is None


def test_get_stream_enc_with_real_stdin():
    result = get_stream_enc(sys.stdin, default="utf-8")
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# getdefaultencoding
# ---------------------------------------------------------------------------


def test_getdefaultencoding_returns_string():
    enc = getdefaultencoding()
    assert isinstance(enc, str)
    assert len(enc) > 0


def test_getdefaultencoding_is_valid_encoding():
    enc = getdefaultencoding()
    "test".encode(enc)  # raises LookupError if invalid


def test_getdefaultencoding_deprecated_prefer_stream_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        getdefaultencoding(prefer_stream=True)
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "prefer_stream" in str(w[0].message)


def test_getdefaultencoding_cp0_returns_cp1252():
    with mock.patch("locale.getpreferredencoding", return_value="cp0"):
        with mock.patch("sys.getdefaultencoding", return_value="cp0"):
            with mock.patch(
                "IPython.utils.encoding.get_stream_enc", return_value=None
            ):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    result = getdefaultencoding()
                    assert result == "cp1252"
                    assert any(issubclass(warning.category, RuntimeWarning) for warning in w)


# ---------------------------------------------------------------------------
# DEFAULT_ENCODING
# ---------------------------------------------------------------------------


def test_default_encoding_is_string():
    assert isinstance(DEFAULT_ENCODING, str)
    assert len(DEFAULT_ENCODING) > 0


def test_default_encoding_is_valid():
    "test".encode(DEFAULT_ENCODING)  # raises LookupError if invalid

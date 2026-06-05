"""Tests for IPython.core.error exception hierarchy."""

import pytest

from IPython.core.error import (
    IPythonCoreError,
    InputRejected,
    StdinNotImplementedError,
    TryNext,
    UsageError,
)


def test_ipython_core_error_is_exception():
    assert issubclass(IPythonCoreError, Exception)


def test_try_next_is_ipython_core_error():
    assert issubclass(TryNext, IPythonCoreError)


def test_usage_error_is_ipython_core_error():
    assert issubclass(UsageError, IPythonCoreError)


def test_stdin_not_implemented_error_is_ipython_core_error():
    assert issubclass(StdinNotImplementedError, IPythonCoreError)


def test_stdin_not_implemented_error_is_not_implemented_error():
    assert issubclass(StdinNotImplementedError, NotImplementedError)


def test_input_rejected_is_exception():
    assert issubclass(InputRejected, Exception)


def test_input_rejected_is_not_ipython_core_error():
    assert not issubclass(InputRejected, IPythonCoreError)


@pytest.mark.parametrize("exc_class", [
    IPythonCoreError,
    TryNext,
    UsageError,
    StdinNotImplementedError,
    InputRejected,
])
def test_exceptions_are_raise_and_catchable(exc_class):
    with pytest.raises(exc_class):
        raise exc_class("test message")


def test_try_next_message():
    with pytest.raises(TryNext, match="skip this hook"):
        raise TryNext("skip this hook")


def test_usage_error_message():
    with pytest.raises(UsageError, match="bad argument"):
        raise UsageError("bad argument")


def test_stdin_not_implemented_caught_as_not_implemented():
    with pytest.raises(NotImplementedError):
        raise StdinNotImplementedError("no stdin here")


def test_try_next_caught_as_ipython_core_error():
    with pytest.raises(IPythonCoreError):
        raise TryNext("try next")


def test_usage_error_caught_as_ipython_core_error():
    with pytest.raises(IPythonCoreError):
        raise UsageError("bad usage")

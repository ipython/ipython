"""Tests for IPython.core.display_functions."""

import pytest
from unittest import mock

from IPython.core.display_functions import (
    DisplayHandle,
    _merge,
    _new_id,
    display,
    update_display,
)


# ---------------------------------------------------------------------------
# _merge
# ---------------------------------------------------------------------------


def test_merge_flat_dicts():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    result = _merge(d1, d2)
    assert result == {"a": 1, "b": 3, "c": 4}
    assert result is d1


def test_merge_nested_dicts():
    d1 = {"a": {"x": 1, "y": 2}}
    d2 = {"a": {"y": 99, "z": 3}}
    _merge(d1, d2)
    assert d1 == {"a": {"x": 1, "y": 99, "z": 3}}


def test_merge_non_dict_d2_returns_d2():
    assert _merge({"a": 1}, "not a dict") == "not a dict"


def test_merge_non_dict_d1_returns_d2():
    assert _merge("not a dict", {"b": 2}) == {"b": 2}


def test_merge_empty_dicts():
    d1 = {}
    _merge(d1, {"a": 1})
    assert d1 == {"a": 1}


# ---------------------------------------------------------------------------
# _new_id
# ---------------------------------------------------------------------------


def test_new_id_is_hex_string():
    id_ = _new_id()
    assert isinstance(id_, str)
    int(id_, 16)  # raises ValueError if not valid hex


def test_new_id_unique():
    ids = {_new_id() for _ in range(20)}
    assert len(ids) == 20


def test_new_id_length():
    assert len(_new_id()) == 32  # 16 bytes → 32 hex chars


# ---------------------------------------------------------------------------
# DisplayHandle
# ---------------------------------------------------------------------------


def test_display_handle_auto_id():
    handle = DisplayHandle()
    assert isinstance(handle.display_id, str)
    int(handle.display_id, 16)


def test_display_handle_explicit_id():
    handle = DisplayHandle(display_id="my-unique-id")
    assert handle.display_id == "my-unique-id"


def test_display_handle_repr():
    handle = DisplayHandle(display_id="abc123")
    r = repr(handle)
    assert "DisplayHandle" in r
    assert "abc123" in r


def test_display_handle_different_instances_different_ids():
    h1 = DisplayHandle()
    h2 = DisplayHandle()
    assert h1.display_id != h2.display_id


# ---------------------------------------------------------------------------
# display() — without InteractiveShell (fallback to print)
# ---------------------------------------------------------------------------


def test_display_without_shell_prints(capsys):
    from IPython.core.interactiveshell import InteractiveShell

    with mock.patch.object(InteractiveShell, "initialized", return_value=False):
        display("hello", "world")

    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "world" in captured.out


def test_display_without_shell_returns_none(capsys):
    from IPython.core.interactiveshell import InteractiveShell

    with mock.patch.object(InteractiveShell, "initialized", return_value=False):
        result = display("hello", display_id="some-id")

    assert result is None


# ---------------------------------------------------------------------------
# display() — with InteractiveShell
# ---------------------------------------------------------------------------


def test_display_with_display_id_true_returns_handle():
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        pytest.skip("No IPython shell available")

    handle = display("test", display_id=True)
    assert isinstance(handle, DisplayHandle)
    assert handle.display_id is not None


def test_display_with_display_id_string_returns_handle():
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        pytest.skip("No IPython shell available")

    handle = display("test", display_id="my-id")
    assert isinstance(handle, DisplayHandle)
    assert handle.display_id == "my-id"


def test_display_without_display_id_returns_none():
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        pytest.skip("No IPython shell available")

    result = display("test")
    assert result is None


def test_display_update_without_display_id_raises():
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        pytest.skip("No IPython shell available")

    with pytest.raises(TypeError, match="display_id required"):
        display("test", update=True)


def test_display_no_objects_with_display_id_returns_handle():
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        pytest.skip("No IPython shell available")

    handle = display(display_id=True)
    assert isinstance(handle, DisplayHandle)


@pytest.mark.parametrize("value", [
    pytest.param(42, id="int"),
    pytest.param("hello", id="str"),
    pytest.param([1, 2, 3], id="list"),
    pytest.param({"a": 1}, id="dict"),
])
def test_display_various_types(value):
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        pytest.skip("No IPython shell available")

    result = display(value)
    assert result is None


# ---------------------------------------------------------------------------
# update_display
# ---------------------------------------------------------------------------


def test_update_display_calls_display_with_update_flag():
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        pytest.skip("No IPython shell available")

    with mock.patch(
        "IPython.core.display_functions.display", wraps=display
    ) as mock_display:
        update_display("new content", display_id="test-id")
        mock_display.assert_called_once()
        call_kwargs = mock_display.call_args[1]
        assert call_kwargs.get("update") is True
        assert call_kwargs.get("display_id") == "test-id"

"""Tests for IPython.core.macro."""

import pickle

import pytest

from IPython.core.macro import Macro


def test_macro_stores_code():
    m = Macro("x = 1\nprint(x)")
    assert "x = 1" in m.value
    assert "print(x)" in m.value


def test_macro_value_ends_with_newline():
    m = Macro("x = 1")
    assert m.value.endswith("\n")


def test_macro_strips_coding_declaration():
    code = "# coding: utf-8\nx = 1"
    m = Macro(code)
    assert "coding" not in m.value
    assert "x = 1" in m.value


def test_macro_strips_coding_declaration_equals_style():
    code = "# coding= latin-1\nx = 1"
    m = Macro(code)
    assert "coding" not in m.value
    assert "x = 1" in m.value


def test_macro_empty_string():
    m = Macro("")
    assert m.value == "\n"


def test_macro_str():
    m = Macro("y = 2")
    assert str(m) == m.value


def test_macro_repr():
    m = Macro("z = 3")
    r = repr(m)
    assert "Macro" in r
    assert "z = 3" in r


@pytest.mark.parametrize("code", [
    "x = 1",
    "import os\nprint(os.getcwd())",
    "for i in range(10):\n    print(i)",
])
def test_macro_preserves_code(code):
    m = Macro(code)
    assert code in m.value


def test_macro_add_macro():
    m1 = Macro("a = 1\n")
    m2 = Macro("b = 2\n")
    m3 = m1 + m2
    assert isinstance(m3, Macro)
    assert "a = 1" in m3.value
    assert "b = 2" in m3.value


def test_macro_add_string():
    m = Macro("a = 1\n")
    m2 = m + "b = 2\n"
    assert isinstance(m2, Macro)
    assert "a = 1" in m2.value
    assert "b = 2" in m2.value


def test_macro_add_invalid_type_raises_typeerror():
    m = Macro("x = 1")
    with pytest.raises(TypeError, match="Macro"):
        m + 42


def test_macro_add_invalid_type_message_contains_type():
    m = Macro("x = 1")
    with pytest.raises(TypeError, match="int"):
        m + 42


def test_macro_pickle_roundtrip():
    m = Macro("x = 1\ny = 2")
    data = pickle.dumps(m)
    m2 = pickle.loads(data)
    assert m2.value == m.value
    assert isinstance(m2, Macro)


def test_macro_getstate():
    m = Macro("x = 1")
    state = m.__getstate__()
    assert state == {"value": m.value}


def test_macro_setstate():
    m = Macro.__new__(Macro)
    m.__setstate__({"value": "restored\n"})
    assert m.value == "restored\n"

"""Tests for IPython.core.macro"""

import pickle

import pytest

from IPython.core.macro import Macro


def test_macro_stores_code_with_trailing_newline():
    m = Macro("a = 1")
    assert m.value == "a = 1\n"


def test_macro_multiline():
    m = Macro("a = 1\nb = 2")
    assert m.value == "a = 1\nb = 2\n"


def test_macro_strips_coding_declaration():
    m = Macro("# coding: utf-8\na = 1")
    assert m.value == "a = 1\n"


def test_macro_strips_coding_declaration_equals_form():
    m = Macro("#coding=latin-1\na = 1")
    assert m.value == "a = 1\n"


def test_macro_strips_coding_declaration_equals_style_spaced():
    m = Macro("# coding= latin-1\na = 1")
    assert m.value == "a = 1\n"


def test_macro_empty_string():
    m = Macro("")
    assert m.value == "\n"


def test_macro_str():
    m = Macro("print('hi')")
    assert str(m) == "print('hi')\n"


def test_macro_repr():
    m = Macro("a = 1")
    assert repr(m) == "IPython.macro.Macro('a = 1\\n')"


@pytest.mark.parametrize("code", [
    "x = 1",
    "import os\nprint(os.getcwd())",
    "for i in range(10):\n    print(i)",
])
def test_macro_preserves_code(code):
    m = Macro(code)
    assert code in m.value


def test_macro_getstate():
    """__getstate__ is needed for safe pickling via %store."""
    m = Macro("a = 1")
    assert m.__getstate__() == {"value": "a = 1\n"}


def test_macro_setstate():
    m = Macro.__new__(Macro)
    m.__setstate__({"value": "restored\n"})
    assert m.value == "restored\n"


def test_macro_pickle_roundtrip():
    m = Macro("x = 1\ny = 2")
    data = pickle.dumps(m)
    m2 = pickle.loads(data)
    assert m2.value == m.value
    assert isinstance(m2, Macro)


def test_macro_add_macro():
    m = Macro("a = 1") + Macro("b = 2")
    assert isinstance(m, Macro)
    assert m.value == "a = 1\nb = 2\n"


def test_macro_add_str():
    m = Macro("a = 1") + "b = 2"
    assert isinstance(m, Macro)
    assert m.value == "a = 1\nb = 2\n"


def test_macro_add_invalid_type():
    with pytest.raises(TypeError, match="Macro"):
        Macro("a = 1") + 42


def test_macro_runs_in_shell():
    """A macro defined on the shell executes its code when invoked."""
    name = "_test_macro_runs_in_shell_macro"
    try:
        ip.define_macro(name, "_test_macro_result = 21 * 2")
        assert isinstance(ip.user_ns[name], Macro)
        ip.run_cell(name)
        assert ip.user_ns["_test_macro_result"] == 42
    finally:
        ip.user_ns.pop(name, None)
        ip.user_ns.pop("_test_macro_result", None)

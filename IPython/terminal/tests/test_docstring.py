import asyncio
import inspect
from unittest.mock import Mock

import pytest
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.shortcuts import PromptSession

from IPython.terminal.docstring import (
    DocstringTooltip,
    find_float_container,
    get_doc_info,
)


def custom_function(a: int, b: str = "test") -> bool:
    """A custom function docstring for testing."""
    return True


class SampleClass:
    def sample_method(self, x, y=10):
        """A sample method docstring."""
        pass


def dangerous_callable():
    raise RuntimeError("This function must never be executed during doc lookup!")


class MockShell:
    def __init__(self, user_ns=None):
        self.user_ns = user_ns or {}
        self.user_global_ns = {}

    def _ofind(self, name):
        from IPython.core.oinspect import OInfo

        obj = self.user_ns.get(name)
        if obj is not None:
            return OInfo(
                ismagic=False,
                isalias=False,
                found=True,
                namespace="Interactive",
                parent=None,
                obj=obj,
            )
        import builtins

        obj = getattr(builtins, name, None)
        if obj is not None:
            return OInfo(
                ismagic=False,
                isalias=False,
                found=True,
                namespace="builtins",
                parent=None,
                obj=obj,
            )
        return OInfo(
            ismagic=False,
            isalias=False,
            found=False,
            namespace=None,
            parent=None,
            obj=None,
        )


@pytest.fixture
def mock_shell():
    ns = {
        "custom_function": custom_function,
        "inst": SampleClass(),
        "dangerous": dangerous_callable,
        "no_doc": lambda x: x,
        "inspect": inspect,
    }
    return MockShell(ns)


def test_get_doc_info_builtins(mock_shell):
    res = get_doc_info("len(", 4, [mock_shell.user_ns], mock_shell)
    assert res is not None
    assert res["name"] == "len"
    assert "len(" in res["signature"]
    assert "number of items" in res["docstring"]

    res_print = get_doc_info("print(", 6, [mock_shell.user_ns], mock_shell)
    assert res_print is not None
    assert res_print["name"] == "print"
    assert "print(" in res_print["signature"]

    res_sorted = get_doc_info("sorted(", 7, [mock_shell.user_ns], mock_shell)
    assert res_sorted is not None
    assert res_sorted["name"] == "sorted"


def test_get_doc_info_user_namespace(mock_shell):
    res = get_doc_info("custom_function(", 16, [mock_shell.user_ns], mock_shell)
    assert res is not None
    assert res["name"] == "custom_function"
    assert "a: int" in res["signature"]
    assert "A custom function docstring" in res["docstring"]


def test_get_doc_info_method(mock_shell):
    res = get_doc_info("inst.sample_method(", 19, [mock_shell.user_ns], mock_shell)
    assert res is not None
    assert res["name"] == "sample_method"
    assert "x" in res["signature"]
    assert "sample method docstring" in res["docstring"]


def test_get_doc_info_nested_calls(mock_shell):
    text = "custom_function(len("
    res = get_doc_info(text, len(text), [mock_shell.user_ns], mock_shell)
    assert res is not None
    assert res["name"] == "len"

    text2 = "custom_function(len([1, 2]), "
    res2 = get_doc_info(text2, len(text2), [mock_shell.user_ns], mock_shell)
    assert res2 is not None
    assert res2["name"] == "custom_function"


def test_get_doc_info_closed_parens(mock_shell):
    assert get_doc_info("len()", 5, [mock_shell.user_ns], mock_shell) is None
    assert get_doc_info("((a + b))", 9, [mock_shell.user_ns], mock_shell) is None


def test_get_doc_info_definition_headers(mock_shell):
    assert get_doc_info("def foo(", 8, [mock_shell.user_ns], mock_shell) is None
    assert get_doc_info("class Bar(", 10, [mock_shell.user_ns], mock_shell) is None
    assert get_doc_info("async def baz(", 14, [mock_shell.user_ns], mock_shell) is None


def test_get_doc_info_inside_string(mock_shell):
    text = 's = "a string with ("'
    assert get_doc_info(text, len(text), [mock_shell.user_ns], mock_shell) is None


def test_get_doc_info_non_callable_and_syntax_error(mock_shell):
    assert get_doc_info("((1 + ", 6, [mock_shell.user_ns], mock_shell) is None
    assert get_doc_info("1 + 2", 5, [mock_shell.user_ns], mock_shell) is None


def test_get_doc_info_callable_without_docstring(mock_shell):
    res = get_doc_info("no_doc(", 7, [mock_shell.user_ns], mock_shell)
    assert res is not None
    assert res["name"] == "<lambda>"
    assert res["docstring"] == ""


def test_get_doc_info_dangerous_callable_never_executed(mock_shell):
    res = get_doc_info("dangerous(", 10, [mock_shell.user_ns], mock_shell)
    assert res is not None
    assert res["name"] == "dangerous_callable"


def test_get_doc_info_multiline(mock_shell):
    text = "x = 1\ncustom_function(x, "
    res = get_doc_info(text, len(text), [mock_shell.user_ns], mock_shell)
    assert res is not None
    assert res["name"] == "custom_function"


def test_get_doc_info_shell_fallback(mock_shell):
    # Test shell fallback when jedi is not used / mocked
    from unittest.mock import patch

    with patch.dict("sys.modules", {"jedi": None}):
        res = get_doc_info(
            "custom_function(", 16, [mock_shell.user_ns], mock_shell
        )
        assert res is not None
        assert res["name"] == "custom_function"
        assert "custom_function(" in res["signature"]
        assert "A custom function docstring" in res["docstring"]


def test_docstring_tooltip_connect(mock_shell):
    session = PromptSession(output=DummyOutput())
    tooltip = DocstringTooltip(mock_shell, delay=0.1)
    tooltip.connect(session)

    assert tooltip._connected is True
    fc = find_float_container(session.layout.container)
    assert fc is not None
    assert any(
        getattr(f.content, "content", None) is not None
        and hasattr(getattr(f.content, "content", None), "content")
        for f in fc.floats
    )


def test_docstring_tooltip_formatted_text(mock_shell):
    tooltip = DocstringTooltip(mock_shell, max_lines=3)
    assert tooltip._get_formatted_text() == []

    tooltip.doc_info = {
        "name": "func",
        "signature": "func(x: int) -> None",
        "docstring": "Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    }
    fragments = tooltip._get_formatted_text()
    assert len(fragments) > 0
    # Signature line
    assert fragments[0][0] == "class:completion-menu.completion.current bold"
    assert "func(x: int) -> None" in fragments[0][1]

    # Docstring lines truncated to max_lines + "..."
    doc_text = "".join(f[1] for f in fragments[1:])
    assert "Line 1" in doc_text
    assert "Line 3" in doc_text
    assert "..." in doc_text
    assert "Line 5" not in doc_text


def test_docstring_tooltip_clear(mock_shell):
    tooltip = DocstringTooltip(mock_shell)
    tooltip.doc_info = {"signature": "foo()", "docstring": "bar"}
    assert tooltip.visible is True

    tooltip.clear()
    assert tooltip.doc_info is None
    assert tooltip.visible is False


def test_docstring_tooltip_on_text_changed_clears_on_closed_parens(mock_shell):
    session = PromptSession(output=DummyOutput())
    tooltip = DocstringTooltip(mock_shell)
    tooltip.connect(session)

    tooltip.doc_info = {"signature": "len()", "docstring": ""}
    buf = Buffer()
    buf.document = Document("len()", cursor_position=5)
    tooltip._on_text_changed(buf)

    assert tooltip.doc_info is None
    assert tooltip.visible is False


@pytest.mark.asyncio
async def test_docstring_tooltip_debounced_lookup(mock_shell):
    session = PromptSession(output=DummyOutput())
    tooltip = DocstringTooltip(mock_shell, delay=0.01)
    tooltip.connect(session)

    buf = Buffer()
    buf.document = Document("custom_function(", cursor_position=16)

    await tooltip._debounced_lookup(buf)
    assert tooltip.doc_info is not None
    assert tooltip.doc_info["name"] == "custom_function"
    assert tooltip.visible is True


def test_terminal_interactiveshell_traits():
    from IPython.terminal.interactiveshell import TerminalInteractiveShell

    shell = TerminalInteractiveShell.instance()
    assert hasattr(shell, "display_docstring_popup")
    assert hasattr(shell, "docstring_popup_delay")
    assert shell.display_docstring_popup is True
    assert shell.docstring_popup_delay == 0.2


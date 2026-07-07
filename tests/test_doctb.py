"""Tests for IPython.core.doctb (doc-oriented traceback formatter)."""

import io
import sys

import pytest
import stack_data

from IPython.core.doctb import DocTB, _format_traceback_lines
from IPython.utils.PyColorize import theme_table


def _divide():
    x = 1
    y = 0
    return x / y


def _call_divide():
    return _divide()


def _zero_division_exc_info():
    try:
        _call_divide()
    except ZeroDivisionError:
        return sys.exc_info()


@pytest.fixture
def doctb():
    return DocTB(theme_name="nocolor")


def test_basic_traceback_module_frame(doctb):
    etype, evalue, etb = _zero_division_exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, context=1)
    assert isinstance(stb, list)
    assert all(isinstance(part, str) for part in stb)
    text = "".join(stb)
    assert text.startswith("Traceback (most recent call last):")
    assert "test_doctb.py" in text
    # only the first frame is shown, the rest are summarized
    assert "[... 2 skipped frames]" in text
    assert "ZeroDivisionError: division by zero" in text
    # only the outermost frame is displayed, with its call signature
    assert "in _zero_division_exc_info()" in text
    assert "_call_divide()" in text


def test_tb_offset_shows_function_frame_and_locals(doctb):
    etype, evalue, etb = _zero_division_exc_info()
    # skip the two outer frames so the failing frame is displayed
    stb = doctb.structured_traceback(etype, evalue, etb, tb_offset=2, context=1)
    text = "".join(stb)
    assert "in _divide()" in text
    # the offending line is displayed with an arrow
    assert "return x / y" in text
    # local variables used in the failing statement are displayed
    assert "x = 1" in text
    assert "y = 0" in text
    assert "skipped frames" not in text


def test_include_vars_false():
    doctb = DocTB(theme_name="nocolor", include_vars=False)
    etype, evalue, etb = _zero_division_exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, tb_offset=2, context=1)
    text = "".join(stb)
    assert "in _divide()" in text
    assert "return x / y" in text
    assert "x = 1" not in text
    assert "y = 0" not in text


def test_default_tb_offset_from_constructor():
    doctb = DocTB(theme_name="nocolor", tb_offset=2)
    etype, evalue, etb = _zero_division_exc_info()
    # tb_offset=None falls back to the instance attribute
    stb = doctb.structured_traceback(etype, evalue, etb, context=1)
    text = "".join(stb)
    assert "in _divide()" in text


def test_colored_output():
    doctb = DocTB(theme_name="linux")
    assert doctb.has_colors
    etype, evalue, etb = _zero_division_exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, tb_offset=2, context=1)
    text = "".join(stb)
    assert "\x1b[" in text
    assert "ZeroDivisionError" in text
    assert "division by zero" in text


def test_exception_notes(doctb):
    try:
        e = ValueError("something went wrong")
        e.add_note("PEP-678 note attached")
        raise e
    except ValueError:
        etype, evalue, etb = sys.exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, context=1)
    text = "".join(stb)
    assert "ValueError: something went wrong" in text
    assert "PEP-678 note attached" in text


def test_exception_notes_not_a_sequence(doctb):
    # a malformed (non-sequence) __notes__ attribute is repr()'d
    try:
        e = ValueError("weird notes")
        e.__notes__ = 42
        raise e
    except ValueError:
        etype, evalue, etb = sys.exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, context=1)
    text = "".join(stb)
    assert "ValueError: weird notes" in text
    assert "42" in text


def test_broken_str_exception(doctb):
    # an exception whose __str__ raises must not crash the formatter
    class BadStr(Exception):
        def __str__(self):
            raise RuntimeError("broken __str__")

    try:
        raise BadStr()
    except BadStr:
        etype, evalue, etb = sys.exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, context=1)
    text = "".join(stb)
    assert "RuntimeError" in text
    assert "broken __str__" in text


def test_broken_repr_local(doctb):
    # a local variable whose repr() raises is reported instead of crashing
    class BadRepr:
        def __repr__(self):
            raise ValueError("no repr for you")

    def bad_repr_frame():
        bad = BadRepr()
        return bad.missing_attr

    try:
        bad_repr_frame()
    except AttributeError:
        etype, evalue, etb = sys.exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, tb_offset=1, context=1)
    text = "".join(stb)
    assert "AttributeError" in text
    assert "Exception trying to inspect frame. No more locals available." in text


def test_exec_code_with_missing_file(doctb):
    # code exec'd from a filename which does not exist on disk
    src = "def boom():\n    raise KeyError('boom')\nboom()\n"
    code = compile(src, "made_up_file_for_doctb_test.py", "exec")
    try:
        exec(code, {})
    except KeyError:
        etype, evalue, etb = sys.exc_info()
    # offset past the test frame so the exec'd <module> frame is first: it
    # has no call signature
    stb = doctb.structured_traceback(etype, evalue, etb, tb_offset=1, context=1)
    text = "".join(stb)
    assert "made_up_file_for_doctb_test.py" in text
    assert ", in" not in text.split("\n")[0]
    assert "KeyError" in text
    assert "'boom'" in text


def test_ipython_frames_excluded_from_line_count(doctb):
    # frames from IPython's own modules take a separate path in get_records
    from IPython.utils.importstring import import_item

    try:
        import_item("no_such_module_for_doctb_test")
    except ImportError:
        etype, evalue, etb = sys.exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, context=1)
    text = "".join(stb)
    assert "ModuleNotFoundError" in text
    assert "no_such_module_for_doctb_test" in text


def test_recursion_repeated_frames(doctb):
    def rec(n):
        return rec(n + 1)

    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(200)
    try:
        try:
            rec(0)
        except RecursionError:
            etype, evalue, etb = sys.exc_info()
    finally:
        sys.setrecursionlimit(limit)

    stb = doctb.structured_traceback(etype, evalue, etb, context=1)
    text = "".join(stb)
    assert "RecursionError" in text

    # repeated frames are summarized by format_record
    records = doctb.get_records(etb, 1, 0)
    repeated = [
        r for r in records if isinstance(r._sd, stack_data.RepeatedFrames)
    ]
    assert repeated
    formatted = doctb.format_record(repeated[0])
    assert "[... skipping similar frames:" in formatted
    assert "rec at line" in formatted


def test_format_record_of_normal_frame(doctb):
    etype, evalue, etb = _zero_division_exc_info()
    records = doctb.get_records(etb, 1, 0)
    # the innermost record is the failing function
    formatted = doctb.format_record(records[-1])
    assert "in _divide()" in formatted
    assert "return x / y" in formatted


def test_format_traceback_lines_line_gap():
    theme = theme_table["nocolor"]
    tokens = _format_traceback_lines([stack_data.LINE_GAP], theme, False, [])
    rendered = theme.format(tokens)
    assert "(...)" in rendered


def test_multiline_statement_context_lines(doctb):
    # a statement spanning several lines shows the whole piece, with the
    # current line marked by an arrow and the others by "..."
    def multi():
        return (
            1
            /
            0
        )

    try:
        multi()
    except ZeroDivisionError:
        etype, evalue, etb = sys.exc_info()
    stb = doctb.structured_traceback(etype, evalue, etb, tb_offset=1, context=1)
    text = "".join(stb)
    # nested function names use the code qualname
    assert "multi()" in text
    assert "->" in text
    assert "..." in text


def test_etype_without_dunder_name(doctb):
    # a pre-stringified etype (no __name__ attribute) is used as-is
    try:
        raise ValueError("boom")
    except ValueError:
        _, evalue, etb = sys.exc_info()
    stb = doctb.structured_traceback("MyFakeError", evalue, etb, context=1)
    text = "".join(stb)
    assert "MyFakeError: boom" in text


def test_handler_currently_unsupported():
    # DocTB.handler() relies on TBTools.text() whose default context is 5,
    # which trips DocTB's internal `context == 1` assertion.  This documents
    # the current behavior.
    sio = io.StringIO()
    doctb = DocTB(theme_name="nocolor", ostream=sio)
    try:
        1 / 0
    except ZeroDivisionError:
        info = sys.exc_info()
    with pytest.raises(AssertionError):
        doctb.handler(info)


def test_prepare_header(doctb):
    head = doctb.prepare_header("ValueError")
    assert "Traceback (most recent call last):" in head


def test_format_exception(doctb):
    formatted = doctb.format_exception("ValueError", ValueError("oops"))
    assert formatted == ["ValueError: oops"]


def test_debugger_disabled(doctb):
    with pytest.raises(RuntimeError, match="Docs mode"):
        doctb.debugger()


def test_chained_exception_cause_currently_unsupported(doctb):
    # DocTB forces context == 1 but its chained-exception loop passes a
    # hard-coded context of 3, so formatting a chained exception currently
    # fails an internal assertion.  This documents the current behavior.
    def chain():
        try:
            1 / 0
        except ZeroDivisionError as e:
            raise ValueError("bad value") from e

    try:
        chain()
    except ValueError:
        etype, evalue, etb = sys.exc_info()
    with pytest.raises(AssertionError):
        doctb.structured_traceback(etype, evalue, etb, context=1)


def test_structured_traceback_rejects_other_context(doctb):
    etype, evalue, etb = _zero_division_exc_info()
    with pytest.raises(AssertionError):
        doctb.structured_traceback(etype, evalue, etb, context=5)

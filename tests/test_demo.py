# -*- coding: utf-8 -*-
"""Tests for the IPython.lib.demo module."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import builtins
import io

import pytest

from IPython.lib import demo as demo_module
from IPython.lib.demo import (
    ClearDemo,
    ClearIPDemo,
    Demo,
    IPythonDemo,
    IPythonLineDemo,
    LineDemo,
    slide,
)

SAMPLE_DEMO = """\
print('hello')

# <demo> stop

x = 1
y = 2

# <demo> stop
# <demo> silent

z = x + y

# <demo> stop
# <demo> auto
print('auto block')

# <demo> --- stop ---

print('last block')
"""


@pytest.fixture
def make_demo(tmp_path):
    """Factory building demo objects from source text, closing files on exit."""
    demos = []

    def _make(src_text, cls=Demo, filename="sample_demo.py", **kwargs):
        fname = tmp_path / filename
        fname.write_text(src_text, encoding="utf-8")
        d = cls(str(fname), **kwargs)
        demos.append(d)
        return d

    yield _make
    for d in demos:
        d.fobj.close()


def run_to_completion(d):
    """Run all remaining blocks of an automatic demo."""
    while not d.finished:
        d()


def test_demo_parsing(make_demo):
    d = make_demo(SAMPLE_DEMO)
    assert d.nblocks == 5
    assert d._silent == [False, False, True, False, False]
    assert d._auto == [False, False, False, True, False]
    assert d.auto_all is False
    assert d.block_index == 0
    assert d.finished is False
    assert d.title == "sample_demo.py"
    # stop markers are removed by the block splitting, auto tags stripped
    assert "<demo> stop" not in "".join(d.src_blocks)
    assert "<demo> auto" not in d.src_blocks[3]
    assert "auto block" in d.src_blocks[3]


def test_demo_title_and_argv(make_demo):
    d = make_demo(SAMPLE_DEMO, title="My Demo", arg_str="--opt value")
    assert d.title == "My Demo"
    assert d.sys_argv[1:] == ["--opt", "value"]


def test_demo_from_filelike():
    src = io.StringIO("print('from filelike')\n")
    d = Demo(src)
    assert d.fname == "from a file-like object"
    assert d.title == "from a file-like object"
    assert d.nblocks == 1
    src.close()

    src2 = io.StringIO("print('named')\n")
    d2 = Demo(src2, title="named demo")
    assert d2.title == "named demo"
    src2.close()


def test_demo_auto_all_tag(make_demo):
    src = "# <demo> auto_all\na = 1\n# <demo> stop\nb = 2\n"
    d = make_demo(src)
    assert d.auto_all is True
    # the auto_all marker must be stripped from the first block
    assert "auto_all" not in d.src_blocks[0]
    run_to_completion(d)
    assert d.user_ns["a"] == 1
    assert d.user_ns["b"] == 2


def test_demo_run_and_finish(make_demo, capsys):
    d = make_demo(SAMPLE_DEMO, auto_all=True)
    run_to_completion(d)
    out = capsys.readouterr().out
    assert "hello" in out
    assert "auto block" in out
    assert "last block" in out
    assert "Executing silent block" in out
    assert "END OF DEMO" in out
    assert d.finished is True
    assert d.user_ns["z"] == 3
    # the interactive namespace is updated at each block
    assert d.ip_ns["z"] == 3

    # calling a finished demo only prints a message
    capsys.readouterr()
    d()
    out = capsys.readouterr().out
    assert "Demo finished" in out
    # explicitly running one block by index still works on a finished demo
    d(0)
    out = capsys.readouterr().out
    assert "hello" in out


def test_demo_interactive_confirm(make_demo, capsys, monkeypatch):
    d = make_demo("run_me = True\n")
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    d()
    out = capsys.readouterr().out
    assert "Press <q> to quit" in out
    assert d.user_ns["run_me"] is True


def test_demo_interactive_quit(make_demo, capsys, monkeypatch):
    d = make_demo("skipped = True\n")
    monkeypatch.setattr("builtins.input", lambda prompt="": "q")
    d()
    out = capsys.readouterr().out
    assert "Block NOT executed" in out
    assert "skipped" not in d.user_ns


def test_demo_seek_back_jump_again(make_demo, capsys):
    d = make_demo(SAMPLE_DEMO, auto_all=True)
    d()  # block 0
    d()  # block 1
    assert d.block_index == 2
    d.back()
    assert d.block_index == 1
    d.jump(1)
    assert d.block_index == 2
    d.seek(0)
    assert d.block_index == 0
    # negative indices seek from the end
    d.seek(-1)
    assert d.block_index == d.nblocks - 1
    run_to_completion(d)
    assert d.finished is True
    # seeking resets the finished flag
    d.seek(1)
    assert d.finished is False
    # again() re-runs the previous block
    d()
    capsys.readouterr()
    d.again()
    assert d.block_index == 2
    out = capsys.readouterr().out
    assert "block # 1" in out


def test_demo_invalid_index(make_demo):
    d = make_demo(SAMPLE_DEMO, auto_all=True)
    with pytest.raises(ValueError, match="invalid block index"):
        d.seek(d.nblocks)
    with pytest.raises(ValueError, match="invalid block index"):
        d(-1)
    with pytest.raises(ValueError, match="invalid block index"):
        d.jump(1000)


def test_demo_reload(make_demo):
    d = make_demo(SAMPLE_DEMO, auto_all=True)
    run_to_completion(d)
    # reload() re-reads the source (closing the previous file) and resets
    d.reload()
    assert d.block_index == 0
    assert d.finished is False
    assert d.nblocks == 5


def test_demo_show_and_edit_when_finished(make_demo, capsys):
    d = make_demo("done = 1\n", auto_all=True)
    run_to_completion(d)
    capsys.readouterr()
    # show() and edit() on a finished demo just print a message
    d.show()
    assert "Demo finished" in capsys.readouterr().out
    d.edit()
    assert "Demo finished" in capsys.readouterr().out


def test_demo_reset(make_demo):
    d = make_demo(SAMPLE_DEMO, auto_all=True)
    run_to_completion(d)
    assert d.finished is True
    d.reset()
    assert d.block_index == 0
    assert d.finished is False
    assert d.user_ns == {}


def test_demo_show(make_demo, capsys):
    d = make_demo(SAMPLE_DEMO)
    d.show(0)
    out = capsys.readouterr().out
    assert "block # 0" in out
    assert "4 remaining" in out
    assert "hello" in out


def test_demo_show_all(make_demo, capsys):
    d = make_demo(SAMPLE_DEMO)
    d.show_all()
    out = capsys.readouterr().out
    # every block is shown, silent ones marked as such
    assert "block # 0" in out
    assert "SILENT block # 2" in out
    assert "last block" in out


def test_demo_exception_shows_traceback(make_demo, monkeypatch):
    d = make_demo("1/0\n", auto_all=True)
    tracebacks = []
    monkeypatch.setattr(
        d, "ip_showtb", lambda *a, **kw: tracebacks.append(kw), raising=False
    )
    d()
    assert tracebacks == [{"filename": d.fname}]
    assert d.finished is True


def test_demo_outside_ipython(make_demo, monkeypatch, capsys):
    monkeypatch.delattr(builtins, "get_ipython")
    d = make_demo("standalone = 42\n", auto_all=True)
    assert d.inside_ipython is False
    run_to_completion(d)
    assert d.user_ns["standalone"] == 42
    assert "END OF DEMO" in capsys.readouterr().out


def test_demo_edit(make_demo, monkeypatch, capsys):
    d = make_demo("first = 1\n# <demo> stop\nsecond = 2\n", auto_all=True)
    d()  # run block 0

    def fake_editor(filename, linenum=None, *args, **kwargs):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("first = 100\n")

    monkeypatch.setattr(d.shell.hooks, "editor", fake_editor, raising=False)
    d.edit()
    # the edited block was stored and re-executed
    assert d.src_blocks[0] == "first = 100\n"
    assert d.user_ns["first"] == 100
    assert d.block_index == 1


def test_demo_marquee():
    src = io.StringIO("pass\n")
    d = Demo(src)
    mq = d.marquee("hello", width=20, mark="*")
    assert "hello" in mq
    assert "*" in mq
    src.close()


def test_ipython_demo(make_demo, capsys):
    d = make_demo("via_ip = 11\nprint('ip ran')\n", cls=IPythonDemo, auto_all=True)
    run_to_completion(d)
    out = capsys.readouterr().out
    assert "ip ran" in out
    # IPythonDemo runs code through the real shell namespace
    assert d.shell.user_ns["via_ip"] == 11


def test_line_demo(make_demo):
    d = make_demo("a = 1\n\nb = 2\nc = a + b\n", cls=LineDemo)
    # blank lines are dropped, each remaining line is a block
    assert d.nblocks == 3
    assert d.auto_all is True
    assert d._silent == [False] * 3
    assert d._auto == [True] * 3
    d()
    assert d.user_ns["a"] == 1
    assert "b" not in d.user_ns
    run_to_completion(d)
    assert d.user_ns["c"] == 3
    assert d.finished is True


def test_ipython_line_demo(make_demo):
    d = make_demo("line_demo_x = 5\n", cls=IPythonLineDemo)
    run_to_completion(d)
    assert d.shell.user_ns["line_demo_x"] == 5


def test_clear_demo(make_demo, monkeypatch, capsys):
    cleared = []
    from IPython.utils import terminal

    monkeypatch.setattr(terminal, "_term_clear", lambda: cleared.append(True))
    d = make_demo("cleared_var = 1\n", cls=ClearDemo, auto_all=True)
    # ClearMixin uses empty marquees
    assert d.marquee("anything") == ""
    run_to_completion(d)
    out = capsys.readouterr().out
    # empty marquee suppresses the END OF DEMO banner
    assert "END OF DEMO" not in out
    assert cleared == [True]
    assert d.user_ns["cleared_var"] == 1
    assert d.finished is True


def test_clear_ip_demo(make_demo, monkeypatch):
    from IPython.utils import terminal

    monkeypatch.setattr(terminal, "_term_clear", lambda: None)
    d = make_demo("clear_ip_var = 7\n", cls=ClearIPDemo, auto_all=True)
    assert d.marquee("x") == ""
    run_to_completion(d)
    assert d.shell.user_ns["clear_ip_var"] == 7


def test_demo_format_rst(make_demo):
    src = '"""A docstring long enough for rst.\n\nMore text.\n"""\n# a comment\nx = 1\n'
    d = make_demo(src, format_rst=True)
    assert d.format_rst is True
    assert hasattr(d, "rst_lexer")
    colored = d.src_blocks_colored[0]
    assert "comment" in colored
    assert "x" in colored
    # highlight() can also be called directly on new content
    assert "y" in d.highlight("y = 2  # another comment")


def test_slide(tmp_path, monkeypatch, capsys):
    fname = tmp_path / "slides.py"
    fname.write_text("s1 = 1\n# <demo> stop\ns2 = 2\n", encoding="utf-8")

    created = []

    class TrackingDemo(Demo):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created.append(self)

    monkeypatch.setattr(demo_module, "Demo", TrackingDemo)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    try:
        slide(str(fname), noclear=True, auto_all=True, format_rst=False)
        (d,) = created
        assert d.finished is True
        assert d.user_ns["s2"] == 2
        out = capsys.readouterr().out
        # the delimiter prompt is emitted between slides
        assert "END OF DEMO" in out
    finally:
        for d in created:
            d.fobj.close()


def test_slide_with_clear(tmp_path, monkeypatch, capsys):
    from IPython.utils import terminal

    fname = tmp_path / "slides_clear.py"
    fname.write_text("c1 = 1\n", encoding="utf-8")

    created = []

    class TrackingClearDemo(ClearDemo):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created.append(self)

    monkeypatch.setattr(demo_module, "ClearDemo", TrackingClearDemo)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    monkeypatch.setattr(terminal, "_term_clear", lambda: None)
    try:
        slide(str(fname), noclear=False, auto_all=True, format_rst=False)
        (d,) = created
        assert isinstance(d, ClearDemo)
        assert d.finished is True
        assert d.user_ns["c1"] == 1
    finally:
        for d in created:
            d.fobj.close()


def test_slide_keyboard_interrupt(tmp_path, monkeypatch):
    fname = tmp_path / "slides2.py"
    fname.write_text("s1 = 1\n", encoding="utf-8")

    created = []

    class TrackingDemo(Demo):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created.append(self)

    def raise_interrupt(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr(demo_module, "Demo", TrackingDemo)
    monkeypatch.setattr("builtins.input", raise_interrupt)
    try:
        with pytest.raises(SystemExit):
            slide(str(fname), noclear=True, auto_all=True, format_rst=False)
    finally:
        for d in created:
            d.fobj.close()

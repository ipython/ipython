# coding: utf-8
"""Tests for the code management magics (%save, %load, %pastebin, %edit)."""

import importlib.util
import os
from pathlib import Path
from urllib.parse import parse_qs

import pytest

from IPython.testing.decorators import skip_win32

from IPython.core.error import StdinNotImplementedError, TryNext, UsageError
from IPython.core.macro import Macro
from IPython.core.magics import code


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------


def test_extract_code_ranges_skips_invalid_tokens():
    # tokens which do not look like ranges are silently ignored
    assert list(code.extract_code_ranges("abc 3-4 x-y")) == [(2, 4)]


def test_strip_initial_indent_blank_lines():
    lines = ["    a = 1", "", "\n", "    b = 2", "c = 3", "    d = 4"]
    # blank lines are passed through, dedenting stops at first less-indented
    # line, and the remaining lines are untouched.
    assert list(code.strip_initial_indent(lines)) == [
        "a = 1",
        "",
        "\n",
        "b = 2",
        "c = 3",
        "    d = 4",
    ]


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


class EditorStub:
    """Stand-in for the editor hook. Records calls, optionally writes
    ``content`` into the file or runs ``side_effect`` on it."""

    def __init__(self):
        self.calls = []
        self.content = None
        self.side_effect = None

    def __call__(self, filename, line=None):
        filename = filename.strip("'")
        self.calls.append((filename, line))
        if self.side_effect is not None:
            self.side_effect(filename)
        if self.content is not None:
            Path(filename).write_text(self.content, encoding="utf-8")


@pytest.fixture
def editor():
    ip = get_ipython()
    stub = EditorStub()
    orig = ip.hooks.editor
    ip.hooks.editor = stub
    try:
        yield stub
    finally:
        ip.hooks.editor = orig


@pytest.fixture
def next_input(monkeypatch):
    """Capture strings passed to shell.set_next_input."""
    ip = get_ipython()
    captured = []
    monkeypatch.setattr(
        ip, "set_next_input", lambda s, replace=False: captured.append(s)
    )
    return captured


# -----------------------------------------------------------------------------
# %save
# -----------------------------------------------------------------------------


def test_save_missing_filename():
    ip = get_ipython()
    with pytest.raises(UsageError):
        ip.run_line_magic("save", "")


def test_save_string_variable(tmp_path, capsys):
    ip = get_ipython()
    ip.user_ns["_save_src"] = "saved_line = 1"
    fname = tmp_path / "savetest"
    ip.run_line_magic("save", "%s _save_src" % fname)
    written = (tmp_path / "savetest.py").read_text(encoding="utf-8")
    assert written == "# coding: utf-8\nsaved_line = 1\n"
    out = capsys.readouterr().out
    assert "The following commands were written" in out


def test_save_raw_uses_ipy_extension(tmp_path):
    ip = get_ipython()
    ip.user_ns["_save_src"] = "saved_line = 2"
    fname = tmp_path / "savetest_raw"
    ip.run_line_magic("save", "-r %s _save_src" % fname)
    assert (tmp_path / "savetest_raw.ipy").is_file()


def test_save_existing_prompt_cancel(tmp_path, capsys, monkeypatch):
    ip = get_ipython()
    ip.user_ns["_save_src"] = "saved_line = 3"
    fname = tmp_path / "existing.py"
    fname.write_text("original = True\n", encoding="utf-8")
    monkeypatch.setattr(ip, "ask_yes_no", lambda *a, **k: False)
    ip.run_line_magic("save", "%s _save_src" % fname)
    assert "Operation cancelled." in capsys.readouterr().out
    assert fname.read_text(encoding="utf-8") == "original = True\n"


def test_save_existing_prompt_overwrite(tmp_path, monkeypatch):
    ip = get_ipython()
    ip.user_ns["_save_src"] = "saved_line = 4"
    fname = tmp_path / "existing.py"
    fname.write_text("original = True\n", encoding="utf-8")
    monkeypatch.setattr(ip, "ask_yes_no", lambda *a, **k: True)
    ip.run_line_magic("save", "%s _save_src" % fname)
    assert fname.read_text(encoding="utf-8") == "# coding: utf-8\nsaved_line = 4\n"


def test_save_existing_stdin_not_implemented(tmp_path, capsys, monkeypatch):
    ip = get_ipython()
    ip.user_ns["_save_src"] = "saved_line = 5"
    fname = tmp_path / "existing.py"
    fname.write_text("original = True\n", encoding="utf-8")

    def raiser(*a, **k):
        raise StdinNotImplementedError()

    monkeypatch.setattr(ip, "ask_yes_no", raiser)
    ip.run_line_magic("save", "%s _save_src" % fname)
    out = capsys.readouterr().out
    assert "force overwrite" in out
    assert fname.read_text(encoding="utf-8") == "original = True\n"


def test_save_force_overwrite(tmp_path):
    ip = get_ipython()
    ip.user_ns["_save_src"] = "saved_line = 6"
    fname = tmp_path / "existing.py"
    fname.write_text("original = True\n", encoding="utf-8")
    ip.run_line_magic("save", "-f %s _save_src" % fname)
    assert fname.read_text(encoding="utf-8") == "# coding: utf-8\nsaved_line = 6\n"


def test_save_append(tmp_path):
    ip = get_ipython()
    ip.user_ns["_save_src"] = "appended_line = 7"
    fname = tmp_path / "existing.py"
    fname.write_text("original = True\n", encoding="utf-8")
    ip.run_line_magic("save", "-a %s _save_src" % fname)
    # no coding header is added when appending to an existing file
    assert (
        fname.read_text(encoding="utf-8") == "original = True\nappended_line = 7\n"
    )


def test_save_bad_target_prints_error(tmp_path, capsys):
    ip = get_ipython()
    fname = tmp_path / "never_written"
    ip.run_line_magic("save", "%s nonexistent_range_xyz" % fname)
    assert "was not found in history" in capsys.readouterr().out
    assert not (tmp_path / "never_written.py").exists()


# -----------------------------------------------------------------------------
# %pastebin
# -----------------------------------------------------------------------------


class _FakePasteResponse:
    headers = {"Location": "https://dpaste.com/FAKEID"}


def test_pastebin_posts_code(monkeypatch):
    ip = get_ipython()
    posted = {}

    def fake_urlopen(request, data):
        posted["url"] = request.full_url
        posted["data"] = data
        return _FakePasteResponse()

    monkeypatch.setattr(code, "urlopen", fake_urlopen)
    ip.user_ns["_paste_src"] = "print('hello dpaste')"
    url = ip.run_line_magic("pastebin", '-d "my description" -e 10 _paste_src')
    assert url == "https://dpaste.com/FAKEID"
    assert posted["url"] == "https://dpaste.com/api/v2/"
    fields = parse_qs(posted["data"].decode("utf-8"))
    assert fields["title"] == ["my description"]
    assert fields["expiry_days"] == ["10"]
    assert fields["content"] == ["print('hello dpaste')"]
    assert fields["syntax"] == ["python"]


def _fail_urlopen(*a, **k):
    raise AssertionError("urlopen should not have been called")


def test_pastebin_expiry_not_an_int(monkeypatch, capsys):
    ip = get_ipython()
    monkeypatch.setattr(code, "urlopen", _fail_urlopen)
    ip.user_ns["_paste_src"] = "x = 1"
    result = ip.run_line_magic("pastebin", "-e notanumber _paste_src")
    assert result is None
    assert "Invalid literal" in capsys.readouterr().out


def test_pastebin_expiry_out_of_range(monkeypatch, capsys):
    ip = get_ipython()
    monkeypatch.setattr(code, "urlopen", _fail_urlopen)
    ip.user_ns["_paste_src"] = "x = 1"
    result = ip.run_line_magic("pastebin", "-e 999 _paste_src")
    assert result is None
    assert "Expiry days should be in range of 1 to 365" in capsys.readouterr().out


def test_pastebin_missing_code(monkeypatch, capsys):
    ip = get_ipython()
    monkeypatch.setattr(code, "urlopen", _fail_urlopen)
    result = ip.run_line_magic("pastebin", "nonexistent_var_zzz")
    assert result is None
    assert "was not found in history" in capsys.readouterr().out


# -----------------------------------------------------------------------------
# %load / %loadpy
# -----------------------------------------------------------------------------


def test_load_file(next_input, tmp_path):
    ip = get_ipython()
    f = tmp_path / "loadme.py"
    f.write_text("la = 1\nlb = 2\n", encoding="utf-8")
    ip.run_line_magic("load", str(f))
    assert len(next_input) == 1
    assert next_input[0].startswith(f"# %load {f}\n")
    assert "la = 1\nlb = 2\n" in next_input[0]


def test_loadpy_alias(next_input, tmp_path):
    ip = get_ipython()
    f = tmp_path / "loadme.py"
    f.write_text("la = 1\n", encoding="utf-8")
    ip.run_line_magic("loadpy", str(f))
    assert len(next_input) == 1
    assert "la = 1" in next_input[0]


def test_load_line_range(next_input, tmp_path):
    ip = get_ipython()
    f = tmp_path / "loadme.py"
    f.write_text("la = 1\nlb = 2\nlc = 3\n", encoding="utf-8")
    ip.run_line_magic("load", "-r 1-2 %s" % f)
    assert "la = 1" in next_input[0]
    assert "lb = 2" in next_input[0]
    assert "lc = 3" not in next_input[0]


_SYMBOLS_SOURCE = "def fa():\n    return 1\n\nclass CB:\n    pass\n"


def test_load_symbol(next_input, tmp_path):
    ip = get_ipython()
    f = tmp_path / "symbols.py"
    f.write_text(_SYMBOLS_SOURCE, encoding="utf-8")
    ip.run_line_magic("load", "-s CB %s" % f)
    assert "class CB:" in next_input[0]
    assert "def fa" not in next_input[0]


def test_load_symbol_not_found_warns(next_input, tmp_path):
    ip = get_ipython()
    f = tmp_path / "symbols.py"
    f.write_text(_SYMBOLS_SOURCE, encoding="utf-8")
    with pytest.warns(UserWarning, match="`missing_sym` was not found"):
        ip.run_line_magic("load", "-s fa,missing_sym %s" % f)
    assert "def fa" in next_input[0]


def test_load_symbols_not_found_warns_plural(next_input, tmp_path):
    ip = get_ipython()
    f = tmp_path / "symbols.py"
    f.write_text(_SYMBOLS_SOURCE, encoding="utf-8")
    with pytest.warns(UserWarning, match="`m1` and `m2` were not found"):
        ip.run_line_magic("load", "-s m1,m2 %s" % f)


def test_load_symbols_non_python_source(next_input, tmp_path, caplog):
    ip = get_ipython()
    f = tmp_path / "notpython.txt"
    f.write_text("this is :: not python\n", encoding="utf-8")
    ip.run_line_magic("load", "-s anything %s" % f)
    assert "Unable to parse the input as valid Python code" in caplog.text
    assert next_input == []


def test_load_big_file_cancelled(next_input, tmp_path, capsys, monkeypatch):
    ip = get_ipython()
    f = tmp_path / "big.py"
    f.write_text("a = 1\n" * 40000, encoding="utf-8")  # > 200 000 chars
    monkeypatch.setattr(ip, "ask_yes_no", lambda *a, **k: False)
    ip.run_line_magic("load", str(f))
    assert "Operation cancelled." in capsys.readouterr().out
    assert next_input == []


def test_load_big_file_confirmed(next_input, tmp_path, monkeypatch):
    ip = get_ipython()
    f = tmp_path / "big.py"
    f.write_text("a = 1\n" * 40000, encoding="utf-8")
    monkeypatch.setattr(ip, "ask_yes_no", lambda *a, **k: True)
    ip.run_line_magic("load", str(f))
    assert len(next_input) == 1


def test_load_big_file_stdin_not_implemented(next_input, tmp_path, monkeypatch):
    # if raw input is not available, assume yes
    ip = get_ipython()
    f = tmp_path / "big.py"
    f.write_text("a = 1\n" * 40000, encoding="utf-8")

    def raiser(*a, **k):
        raise StdinNotImplementedError()

    monkeypatch.setattr(ip, "ask_yes_no", raiser)
    ip.run_line_magic("load", str(f))
    assert len(next_input) == 1


def test_load_big_file_y_flag(next_input, tmp_path, monkeypatch):
    ip = get_ipython()
    f = tmp_path / "big.py"
    f.write_text("a = 1\n" * 40000, encoding="utf-8")
    monkeypatch.setattr(ip, "ask_yes_no", _fail_urlopen)
    ip.run_line_magic("load", "-y %s" % f)
    assert len(next_input) == 1


# -----------------------------------------------------------------------------
# %edit
# -----------------------------------------------------------------------------


def test_edit_temp_file_executes(editor, capsys):
    ip = get_ipython()
    ip.user_ns.pop("_edit_tmp_var", None)
    editor.content = "_edit_tmp_var = 42\n"
    result = ip.run_line_magic("edit", "")
    out = capsys.readouterr().out
    assert "IPython will make a temporary file" in out
    assert "done. Executing edited code..." in out
    assert ip.user_ns["_edit_tmp_var"] == 42
    assert result == "_edit_tmp_var = 42\n"
    assert len(editor.calls) == 1


def test_edit_file_executes(editor, tmp_path):
    ip = get_ipython()
    ip.user_ns.pop("_edit_file_var", None)
    f = tmp_path / "edit_exec.py"
    f.write_text("_edit_file_var = 7\n", encoding="utf-8")
    result = ip.run_line_magic("edit", str(f))
    assert result is None  # not a temp file
    assert ip.user_ns["_edit_file_var"] == 7
    assert editor.calls[-1][0] == str(f)


def test_edit_x_does_not_execute(editor, tmp_path, capsys):
    ip = get_ipython()
    ip.user_ns.pop("_edit_noexec_var", None)
    f = tmp_path / "edit_noexec.py"
    f.write_text("_edit_noexec_var = 1\n", encoding="utf-8")
    ip.run_line_magic("edit", "-x -n 3 %s" % f)
    assert "_edit_noexec_var" not in ip.user_ns
    assert "Executing edited code" not in capsys.readouterr().out
    # -n passes the line number through to the editor hook
    assert editor.calls[-1] == (str(f), "3")


@skip_win32
def test_edit_filename_with_space_is_quoted(editor, tmp_path):
    ip = get_ipython()
    d = tmp_path / "dir with space"
    d.mkdir()
    f = d / "edit_space.py"
    f.write_text("x = 1\n", encoding="utf-8")
    ip.run_line_magic("edit", "-x '%s'" % f)
    # the stub strips the quotes added for filenames containing spaces
    assert editor.calls[-1][0] == str(f)


def test_edit_raw_option(editor, tmp_path):
    ip = get_ipython()
    ip.user_ns.pop("_edit_raw_var", None)
    f = tmp_path / "edit_raw.py"
    f.write_text("_edit_raw_var = 4\n", encoding="utf-8")
    result = ip.run_line_magic("edit", "-r %s" % f)
    assert result is None
    assert ip.user_ns["_edit_raw_var"] == 4


def test_edit_string_variable(editor):
    ip = get_ipython()
    ip.user_ns.pop("_edit_str_var", None)
    ip.user_ns["_edit_str_src"] = "_edit_str_var = 3"
    result = ip.run_line_magic("edit", "_edit_str_src")
    assert ip.user_ns["_edit_str_var"] == 3
    assert "_edit_str_var = 3" in result


def test_edit_history_range(editor):
    ip = get_ipython()
    ip.run_cell("_rng_edit_var = 10", store_history=True)
    # session history lines are positional indices into the input cache; the
    # shell's execution_count may be out of sync with it after other tests
    lineno = len(ip.history_manager.input_hist_parsed) - 1
    result = ip.run_line_magic("edit", "-x %s" % lineno)
    assert "_rng_edit_var = 10" in result
    assert "_rng_edit_var = 10" in Path(editor.calls[-1][0]).read_text(
        encoding="utf-8"
    )


def test_edit_macro(editor):
    ip = get_ipython()
    ip.user_ns["_test_macro_ed"] = Macro("print('orig')\n")
    editor.content = "print('changed')\n"
    ip.run_line_magic("edit", "_test_macro_ed")
    new_macro = ip.user_ns["_test_macro_ed"]
    assert isinstance(new_macro, Macro)
    assert new_macro.value == "print('changed')\n"


def test_edit_previous(editor):
    ip = get_ipython()
    ip.user_ns["_edit_prev_src"] = "prev_edit_var = 7"
    ip.run_line_magic("edit", "-x _edit_prev_src")
    # make sure '_<prompt_count>' does not shadow the stored argument
    ip.user_ns.pop("_%s" % ip.displayhook.prompt_count, None)
    result = ip.run_line_magic("edit", "-x -p")
    assert "prev_edit_var = 7" in result


def test_edit_nonexistent_warns(editor):
    ip = get_ipython()
    ip.user_ns.pop("no_such_thing_xyz", None)
    with pytest.warns(UserWarning, match="found as a variable"):
        result = ip.run_line_magic("edit", "no_such_thing_xyz")
    assert result is None
    assert editor.calls == []


@skip_win32
def test_edit_object_with_source_file(editor, tmp_path):
    ip = get_ipython()
    mod_file = tmp_path / "edit_target_mod.py"
    mod_file.write_text("def target_func():\n    return 1\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("edit_target_mod", mod_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ip.user_ns["_edit_obj_func"] = module.target_func
    ip.run_line_magic("edit", "-x _edit_obj_func")
    filename, lineno = editor.calls[-1]
    assert filename == str(mod_file)
    assert lineno == 1


def test_edit_object_without_source_warns(editor):
    ip = get_ipython()
    ip.user_ns["_edit_builtin_obj"] = len
    with pytest.warns(UserWarning, match="cannot be read or found"):
        result = ip.run_line_magic("edit", "_edit_builtin_obj")
    assert result is None
    assert editor.calls == []


def test_edit_interactively_defined(editor, capsys):
    ip = get_ipython()
    # %edit on an interactively defined object looks the input up by the
    # prompt number embedded in the compiled cell filename, so the execution
    # count must match the session input cache (other tests may have left
    # them out of sync). Never lower execution_count to resync: cells would
    # then reuse (session, line) numbers already written to the history db.
    hm = ip.history_manager
    if ip.execution_count > len(hm.input_hist_raw):
        hm.input_hist_raw.extend(
            [""] * (ip.execution_count - len(hm.input_hist_raw))
        )
        hm.input_hist_parsed.extend(
            [""] * (ip.execution_count - len(hm.input_hist_parsed))
        )
    else:
        ip.execution_count = len(hm.input_hist_raw)
    ip.run_cell("def _intdef_f(): return 41", store_history=True)
    editor.content = "def _intdef_f(): return 42\n"
    result = ip.run_line_magic("edit", "_intdef_f")
    assert "Editing In[" in capsys.readouterr().out
    assert ip.user_ns["_intdef_f"]() == 42
    assert result == "def _intdef_f(): return 42\n"


def test_edit_known_temp_file(editor):
    ip = get_ipython()
    editor.content = "_edit_kt_var = 3\n"
    ip.run_line_magic("edit", "")
    tempname = editor.calls[-1][0]
    editor.content = None
    # editing the same temp file again is recognized, so its contents are
    # returned even though a filename argument was given
    result = ip.run_line_magic("edit", "-x %s" % tempname)
    assert result == "_edit_kt_var = 3\n"


def test_edit_editor_trynext_warns(editor, tmp_path):
    ip = get_ipython()
    f = tmp_path / "edit_trynext.py"
    f.write_text("x = 1\n", encoding="utf-8")

    def raise_trynext(filename):
        raise TryNext()

    editor.side_effect = raise_trynext
    with pytest.warns(UserWarning, match="Could not open editor"):
        result = ip.run_line_magic("edit", "-x %s" % f)
    assert result is None


def test_edit_pasted_block(editor):
    ip = get_ipython()
    orig = ip.user_ns.get("pasted_block")
    try:
        ip.user_ns["pasted_block"] = "pb = 1\n"
        editor.content = "pb = 2\n"
        ip.run_line_magic("edit", "-x pasted_block")
        assert ip.user_ns["pasted_block"] == "pb = 2\n"
    finally:
        if orig is None:
            ip.user_ns.pop("pasted_block", None)
        else:
            ip.user_ns["pasted_block"] = orig


def test_edit_temp_file_deleted_warns(editor):
    ip = get_ipython()
    editor.side_effect = os.unlink
    with pytest.warns(UserWarning, match="File not found"):
        result = ip.run_line_magic("edit", "-x")
    assert result is None

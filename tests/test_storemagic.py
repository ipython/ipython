import tempfile, os
from pathlib import Path

import pytest
from traitlets.config.loader import Config

from IPython.core.error import UsageError


def setup_module():
    ip.run_line_magic("load_ext", "storemagic")


def test_store_restore():
    assert "bar" not in ip.user_ns, "Error: some other test leaked `bar` in user_ns"
    assert "foo" not in ip.user_ns, "Error: some other test leaked `foo` in user_ns"
    assert (
        "foobar" not in ip.user_ns
    ), "Error: some other test leaked `foobar` in user_ns"
    assert (
        "foobaz" not in ip.user_ns
    ), "Error: some other test leaked `foobaz` in user_ns"
    ip.user_ns["foo"] = 78
    ip.run_line_magic("alias", 'bar echo "hello"')
    ip.user_ns["foobar"] = 79
    ip.user_ns["foobaz"] = "80"
    tmpd = tempfile.mkdtemp()
    ip.run_line_magic("cd", tmpd)
    ip.run_line_magic("store", "foo")
    ip.run_line_magic("store", "bar")
    ip.run_line_magic("store", "foobar foobaz")

    # Check storing
    assert ip.db["autorestore/foo"] == 78
    assert "bar" in ip.db["stored_aliases"]
    assert ip.db["autorestore/foobar"] == 79
    assert ip.db["autorestore/foobaz"] == "80"

    # Remove those items
    ip.user_ns.pop("foo", None)
    ip.user_ns.pop("foobar", None)
    ip.user_ns.pop("foobaz", None)
    ip.alias_manager.undefine_alias("bar")
    ip.run_line_magic("cd", "-")
    ip.user_ns["_dh"][:] = []

    # Check restoring
    ip.run_line_magic("store", "-r foo bar foobar foobaz")
    assert ip.user_ns["foo"] == 78
    assert ip.alias_manager.is_alias("bar")
    assert ip.user_ns["foobar"] == 79
    assert ip.user_ns["foobaz"] == "80"

    ip.run_line_magic("store", "-r")  # restores _dh too
    assert any(Path(tmpd).samefile(p) for p in ip.user_ns["_dh"])

    os.rmdir(tmpd)


def test_autorestore():
    ip.user_ns["foo"] = 95
    ip.run_line_magic("store", "foo")
    del ip.user_ns["foo"]
    c = Config()
    c.StoreMagics.autorestore = False
    orig_config = ip.config
    try:
        ip.config = c
        ip.extension_manager.reload_extension("storemagic")
        assert "foo" not in ip.user_ns
        c.StoreMagics.autorestore = True
        ip.extension_manager.reload_extension("storemagic")
        assert ip.user_ns["foo"] == 95
    finally:
        ip.config = orig_config


def test_store_list(capsys):
    ip.user_ns["stored_var_x"] = 123
    try:
        ip.run_line_magic("store", "stored_var_x")
        assert "Stored 'stored_var_x' (int)" in capsys.readouterr().out
        ip.run_line_magic("store", "")
        out = capsys.readouterr().out
        assert "Stored variables and their in-db values:" in out
        assert "stored_var_x" in out
        assert "123" in out
    finally:
        ip.user_ns.pop("stored_var_x", None)
        ip.db.pop("autorestore/stored_var_x", None)


def test_store_delete():
    ip.user_ns["stored_var_d"] = 42
    try:
        ip.run_line_magic("store", "stored_var_d")
        assert "autorestore/stored_var_d" in ip.db.keys("autorestore/*")
        ip.run_line_magic("store", "-d stored_var_d")
        assert "autorestore/stored_var_d" not in ip.db.keys("autorestore/*")
    finally:
        ip.user_ns.pop("stored_var_d", None)
        ip.db.pop("autorestore/stored_var_d", None)


def test_store_delete_no_args():
    with pytest.raises(UsageError, match="You must provide the variable to forget"):
        ip.run_line_magic("store", "-d")


def test_store_delete_failure(monkeypatch):
    # pickleshare silently ignores missing keys, so simulate a backend that
    # fails to delete to exercise the error path.
    def raising_delitem(self, key):
        raise KeyError(key)

    monkeypatch.setattr(type(ip.db), "__delitem__", raising_delitem)
    with pytest.raises(UsageError, match="Can't delete variable 'no_such_var'"):
        ip.run_line_magic("store", "-d no_such_var")


def test_store_reset():
    ip.user_ns["stored_var_z1"] = 1
    ip.user_ns["stored_var_z2"] = 2
    try:
        ip.run_line_magic("store", "stored_var_z1 stored_var_z2")
        assert len(ip.db.keys("autorestore/*")) >= 2
        ip.run_line_magic("store", "-z")
        assert ip.db.keys("autorestore/*") == []
    finally:
        ip.user_ns.pop("stored_var_z1", None)
        ip.user_ns.pop("stored_var_z2", None)


def test_store_list_empty(capsys):
    ip.run_line_magic("store", "-z")
    ip.run_line_magic("store", "")
    out = capsys.readouterr().out
    assert "Stored variables and their in-db values:" in out


def test_store_restore_unknown_name(capsys):
    ip.run_line_magic("store", "-r no_such_var_or_alias")
    assert (
        "no stored variable or alias no_such_var_or_alias" in capsys.readouterr().out
    )


def test_store_unknown_variable_raises():
    with pytest.raises(UsageError, match="Unknown variable 'no_such_var'"):
        ip.run_line_magic("store", "no_such_var")


def test_store_string_to_file(tmp_path, capsys):
    fname = tmp_path / "out.txt"
    ip.user_ns["stored_str"] = "hello"
    try:
        ip.run_line_magic("store", "stored_str >%s" % fname)
        out = capsys.readouterr().out
        assert "Writing 'stored_str' (str) to file" in out
        assert fname.read_text(encoding="utf-8") == "hello\n"
        # >> appends instead of overwriting
        ip.run_line_magic("store", "stored_str >>%s" % fname)
        assert fname.read_text(encoding="utf-8") == "hello\nhello\n"
    finally:
        ip.user_ns.pop("stored_str", None)


def test_store_object_to_file(tmp_path, capsys):
    fname = tmp_path / "out.txt"
    ip.user_ns["stored_list"] = ["a", "b"]
    try:
        ip.run_line_magic("store", "stored_list >%s" % fname)
        out = capsys.readouterr().out
        assert "Writing 'stored_list' (list) to file" in out
        assert fname.read_text(encoding="utf-8") == "['a', 'b']\n"
    finally:
        ip.user_ns.pop("stored_list", None)


def test_store_interactively_defined_class_warns(capsys):
    ip.run_cell("class _StoreTestClass: pass\n_store_inst = _StoreTestClass()")
    try:
        ip.run_line_magic("store", "_store_inst")
        out = capsys.readouterr().out
        assert "Warning:_store_inst is" in out
        assert "autorestore/_store_inst" not in ip.db.keys("autorestore/*")
    finally:
        ip.user_ns.pop("_StoreTestClass", None)
        ip.user_ns.pop("_store_inst", None)


def test_refresh_corrupt_variable(capsys):
    # A stored value whose pickle can't be read is skipped with a message.
    root = Path(ip.db.root)
    (root / "autorestore").mkdir(exist_ok=True)
    corrupt = root / "autorestore" / "corrupt_key"
    corrupt.write_bytes(b"this is not a pickle")
    try:
        ip.run_line_magic("store", "-r corrupt_key")
        # explicit name goes through the alias fallback path
        assert "no stored variable or alias corrupt_key" in capsys.readouterr().out
        ip.run_line_magic("store", "-r")
        assert "Unable to restore variable 'corrupt_key'" in capsys.readouterr().out
        assert "corrupt_key" not in ip.user_ns
    finally:
        corrupt.unlink()

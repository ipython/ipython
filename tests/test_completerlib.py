# -*- coding: utf-8 -*-
"""Tests for completerlib."""

import os
import sys
from os.path import join
from tempfile import TemporaryDirectory

import pytest

from IPython.core.completerlib import magic_run_completer, module_completion, try_import
from IPython.testing.decorators import onlyif_unicode_paths


class MockEvent(object):
    def __init__(self, line):
        self.line = line


@pytest.fixture
def run_completer_dir(tmp_path, monkeypatch):
    files = ["aao.py", "a.py", "b.py", "aao.txt"]
    dirs = ["adir/", "bdir/"]
    for fil in files:
        (tmp_path / fil).write_text("pass\n", encoding="utf-8")
    for d in dirs:
        (tmp_path / d).mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path, files, dirs


@pytest.mark.parametrize("line,expected_match", [
    ("%run a", {"a.py", "aao.py", "adir/"}),
    ("%run aa", {"aao.py"}),
    ('%run "a', {"a.py", "aao.py", "adir/"}),
])
def test_magic_run_completer(run_completer_dir, line, expected_match):
    match = set(magic_run_completer(None, MockEvent(line)))
    assert match == expected_match


def test_magic_run_completer_more_args(run_completer_dir):
    tmp_path, files, dirs = run_completer_dir
    match = set(magic_run_completer(None, MockEvent("%run a.py ")))
    assert match == set(files + dirs)


def test_magic_run_completer_in_dir(run_completer_dir):
    # Github issue #3459
    tmp_path, files, dirs = run_completer_dir
    event = MockEvent("%run a.py {}".format(join(str(tmp_path), "a")))
    match = set(magic_run_completer(None, event))
    assert match == {
        join(str(tmp_path), f).replace("\\", "/")
        for f in ("a.py", "aao.py", "aao.txt", "adir/")
    }


@pytest.fixture
def run_completer_dir_nonascii(tmp_path, monkeypatch):
    for fil in ["aaø.py", "a.py", "b.py"]:
        (tmp_path / fil).write_text("pass\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@onlyif_unicode_paths
@pytest.mark.parametrize("line,expected_match", [
    ("%run a", {"a.py", "aaø.py"}),
    ("%run aa", {"aaø.py"}),
    ('%run "a', {"a.py", "aaø.py"}),
])
def test_magic_run_completer_nonascii(run_completer_dir_nonascii, line, expected_match):
    match = set(magic_run_completer(None, MockEvent(line)))
    assert match == expected_match


def test_import_invalid_module():
    """Testing of issue https://github.com/ipython/ipython/issues/1107"""
    invalid_module_names = {"foo-bar", "foo:bar", "10foo"}
    valid_module_names = {"foobar"}
    with TemporaryDirectory() as tmpdir:
        sys.path.insert(0, tmpdir)
        for name in invalid_module_names | valid_module_names:
            filename = os.path.join(tmpdir, name + ".py")
            open(filename, "w", encoding="utf-8").close()

        s = set(module_completion("import foo"))
        intersection = s.intersection(invalid_module_names)
        assert intersection == set()

        assert valid_module_names.issubset(s), valid_module_names.intersection(s)


def test_bad_module_all():
    """Test module with invalid __all__

    https://github.com/ipython/ipython/issues/9678
    """
    testsdir = os.path.dirname(__file__)
    sys.path.insert(0, testsdir)
    try:
        results = module_completion("from bad_all import ")
        assert "puppies" in results
        for r in results:
            assert isinstance(r, str)

        results = module_completion("import bad_all.")
        assert results == []
    finally:
        sys.path.remove(testsdir)


def test_module_without_init():
    """
    Test module without __init__.py.

    https://github.com/ipython/ipython/issues/11226
    """
    fake_module_name = "foo_xder_134"
    with TemporaryDirectory() as tmpdir:
        sys.path.insert(0, tmpdir)
        try:
            os.makedirs(os.path.join(tmpdir, fake_module_name))
            s = try_import(mod=fake_module_name)
            assert s == [], f"for module {fake_module_name}"
        finally:
            sys.path.remove(tmpdir)


def test_valid_exported_submodules():
    """
    Test checking exported (__all__) objects are submodules
    """
    results = module_completion("import os.pa")
    assert "os.path" in results
    assert "os.pathconf" not in results

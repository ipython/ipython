# -*- coding: utf-8 -*-
"""Test suite for the deepreload module."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import types
from pathlib import Path

import pytest
from tempfile import TemporaryDirectory

from IPython.lib import deepreload
from IPython.lib.deepreload import modules_reloading
from IPython.lib.deepreload import reload as dreload
from IPython.utils.syspathcontext import prepended_to_syspath


def test_deepreload():
    "Test that dreload does deep reloads and skips excluded modules."
    with TemporaryDirectory() as tmpdir:
        with prepended_to_syspath(tmpdir):
            tmpdirpath = Path(tmpdir)
            with open(tmpdirpath / "A.py", "w", encoding="utf-8") as f:
                f.write("class Object:\n    pass\nok = True\n")
            with open(tmpdirpath / "B.py", "w", encoding="utf-8") as f:
                f.write("import A\nassert A.ok, 'we are fine'\n")
            import A
            import B

            # Test that A is not reloaded.
            obj = A.Object()
            dreload(B, exclude=["A"])
            assert isinstance(obj, A.Object) is True

            # Test that an import failure will not blow-up us.
            A.ok = False
            with pytest.raises(AssertionError, match="we are fine"):
                dreload(B, exclude=["A"])
            assert len(modules_reloading) == 0
            assert not A.ok

            # Test that A is reloaded.
            obj = A.Object()
            A.ok = False
            dreload(B)
            assert A.ok
            assert isinstance(obj, A.Object) is False


def test_deepreload_package_relative_imports():
    """Reloading a package exercises dotted, relative and star imports."""
    with TemporaryDirectory() as tmpdir:
        with prepended_to_syspath(tmpdir):
            pkgdir = Path(tmpdir) / "dpkg"
            pkgdir.mkdir()
            (pkgdir / "__init__.py").write_text(
                "from dpkg import dmod1\n__all__ = ['dmod1', 'dmod2']\n",
                encoding="utf-8",
            )
            (pkgdir / "dmod1.py").write_text(
                "from . import dmod2\nfrom .dmod2 import val\n", encoding="utf-8"
            )
            (pkgdir / "dmod2.py").write_text("val = 1\n", encoding="utf-8")
            main = Path(tmpdir) / "dmain.py"
            main.write_text(
                "import dpkg.dmod1\nfrom dpkg import dmod2\nfrom dpkg import *\n",
                encoding="utf-8",
            )

            import dmain
            import dpkg

            # mutate state that only a re-execution of the modules restores
            dpkg.dmod2.val = 999
            newmain = dreload(dmain)
            assert newmain is dmain
            # submodules reachable through relative imports were re-executed
            assert dpkg.dmod2.val == 1
            assert dmain.dmod2.val == 1
            assert dmain.dmod1.val == 1
            assert len(modules_reloading) == 0

            for name in list(sys.modules):
                if name == "dmain" or name.startswith("dpkg"):
                    del sys.modules[name]


def test_not_module():
    pytest.raises(TypeError, dreload, "modulename")


def test_not_in_sys_modules():
    fake_module = types.ModuleType("fake_module")
    with pytest.raises(ImportError, match="not in sys.modules"):
        dreload(fake_module)


def test_reload_types_module_is_noop():
    # the types module is hardcoded to never be reloaded
    assert dreload(types) is types


class TestGetParent:
    def test_no_level(self):
        assert deepreload.get_parent({"__package__": "os"}, 0) == (None, "")

    def test_globals_not_dict(self):
        assert deepreload.get_parent(None, 1) == (None, "")

    def test_package_not_string(self):
        with pytest.raises(ValueError, match="__package__ set to non-string"):
            deepreload.get_parent({"__package__": 42}, 1)

    def test_relative_import_in_non_package(self):
        with pytest.raises(ValueError, match="non-package"):
            deepreload.get_parent({"__package__": ""}, 1)

    def test_empty_package_negative_level(self):
        assert deepreload.get_parent({"__package__": ""}, -1) == (None, "")

    def test_package_set(self):
        parent, name = deepreload.get_parent({"__package__": "os"}, 1)
        assert parent is sys.modules["os"]
        assert name == "os"

    def test_no_name(self):
        assert deepreload.get_parent({}, 1) == (None, "")

    def test_name_with_path_is_package(self):
        import json

        globals_ = {"__name__": "json", "__path__": []}
        parent, name = deepreload.get_parent(globals_, 1)
        assert parent is json
        assert name == "json"
        # get_parent fills in __package__ as a side effect
        assert globals_["__package__"] == "json"

    def test_plain_module_infers_package(self):
        globals_ = {"__name__": "os.path"}
        parent, name = deepreload.get_parent(globals_, 1)
        assert parent is sys.modules["os"]
        assert name == "os"
        assert globals_["__package__"] == "os"

    def test_toplevel_module_relative_import(self):
        with pytest.raises(ValueError, match="non-package"):
            deepreload.get_parent({"__name__": "os"}, 1)

    def test_toplevel_module_absolute_import(self):
        globals_ = {"__name__": "os"}
        assert deepreload.get_parent(globals_, -1) == (None, "")
        assert globals_["__package__"] is None

    def test_relative_import_beyond_toplevel(self):
        with pytest.raises(ValueError, match="beyond top-level"):
            deepreload.get_parent({"__package__": "os"}, 2)

    def test_parent_not_loaded_relative(self):
        with pytest.raises(SystemError, match="not loaded"):
            deepreload.get_parent({"__package__": "not_a_real_module_xyz"}, 1)

    def test_parent_not_found_absolute(self):
        with pytest.warns(UserWarning, match="not found"):
            parent, name = deepreload.get_parent(
                {"__package__": "not_a_real_module_xyz"}, -1
            )
        assert parent is None
        assert name == "not_a_real_module_xyz"


class TestLoadNext:
    def test_empty_name(self):
        mod = types.ModuleType("mod")
        assert deepreload.load_next(mod, None, "", "buf") == (mod, None, "buf")

    def test_dot_prefixed_name(self):
        with pytest.raises(ValueError, match="Empty module name"):
            deepreload.load_next(None, None, ".foo", "")

    def test_import_failure(self, monkeypatch):
        monkeypatch.setattr(
            deepreload, "import_submodule", lambda mod, subname, fullname: None
        )
        with pytest.raises(ImportError, match="No module named"):
            deepreload.load_next(None, None, "foo", "")

    def test_altmod_fallback(self, monkeypatch):
        """When the parent lookup fails, load_next retries with altmod."""
        sentinel = types.ModuleType("sentinel")
        mod = types.ModuleType("mod")
        calls = []

        def fake_import_submodule(m, subname, fullname):
            calls.append((m, subname, fullname))
            return sentinel if m is None else None

        monkeypatch.setattr(deepreload, "import_submodule", fake_import_submodule)
        result, next_, buf = deepreload.load_next(mod, None, "foo.bar", "pfx")
        assert result is sentinel
        assert next_ == "bar"
        assert buf == "foo"
        assert calls == [(mod, "foo", "pfx.foo"), (None, "foo", "foo")]


class TestEnsureFromlist:
    def test_no_path_attribute(self):
        # modules without __path__ (i.e. not packages) are ignored
        mod = types.ModuleType("plain")
        assert deepreload.ensure_fromlist(mod, ["anything"], "plain", 0) is None

    def test_fromlist_item_not_string(self):
        pkg = types.ModuleType("fakepkg")
        pkg.__path__ = []
        with pytest.raises(TypeError, match="not a string"):
            deepreload.ensure_fromlist(pkg, [42], "fakepkg", 0)

    def test_star_without_all(self):
        pkg = types.ModuleType("fakepkg")
        pkg.__path__ = []
        # no __all__: '*' is silently ignored
        assert deepreload.ensure_fromlist(pkg, ["*"], "fakepkg", 0) is None

    def test_star_recursive_is_skipped(self):
        pkg = types.ModuleType("fakepkg")
        pkg.__path__ = []
        pkg.__all__ = ["*"]
        # a '*' inside __all__ must not recurse endlessly
        assert deepreload.ensure_fromlist(pkg, ["*"], "fakepkg", 1) is None

    def test_existing_attribute_not_reimported(self, monkeypatch):
        pkg = types.ModuleType("fakepkg")
        pkg.__path__ = []
        pkg.present = True

        def boom(mod, subname, fullname):
            raise AssertionError("should not be called")

        monkeypatch.setattr(deepreload, "import_submodule", boom)
        deepreload.ensure_fromlist(pkg, ["present"], "fakepkg", 0)

    def test_missing_attribute_imported(self, monkeypatch):
        pkg = types.ModuleType("fakepkg")
        pkg.__path__ = []
        imported = []
        monkeypatch.setattr(
            deepreload,
            "import_submodule",
            lambda mod, subname, fullname: imported.append((subname, fullname)),
        )
        deepreload.ensure_fromlist(pkg, ["missing"], "fakepkg", 0)
        assert imported == [("missing", "fakepkg.missing")]


class TestImportSubmodule:
    def test_already_found(self, monkeypatch):
        monkeypatch.setitem(deepreload.found_now, "os", 1)
        assert deepreload.import_submodule(None, "os", "os") is sys.modules["os"]

    def test_fresh_import(self, capsys):
        """A module not yet in sys.modules is imported, not reloaded."""
        with TemporaryDirectory() as tmpdir:
            with prepended_to_syspath(tmpdir):
                (Path(tmpdir) / "fresh_mod_xyz.py").write_text(
                    "fresh = True\n", encoding="utf-8"
                )
                try:
                    m = deepreload.import_submodule(
                        None, "fresh_mod_xyz", "fresh_mod_xyz"
                    )
                    assert m.fresh is True
                    assert "Reloading fresh_mod_xyz" in capsys.readouterr().out
                finally:
                    sys.modules.pop("fresh_mod_xyz", None)
                    deepreload.found_now.clear()

    def test_failed_reload_restores_module(self, monkeypatch, capsys):
        modname = "fake_failing_module"
        oldm = types.ModuleType(modname)
        monkeypatch.setitem(sys.modules, modname, oldm)

        def failing_reload(m):
            del sys.modules[modname]
            raise RuntimeError("reload failed")

        monkeypatch.setattr(deepreload.importlib, "reload", failing_reload)
        with pytest.raises(RuntimeError, match="reload failed"):
            deepreload.import_submodule(None, modname, modname)
        # the original module object must be restored
        assert sys.modules[modname] is oldm
        assert "Reloading fake_failing_module" in capsys.readouterr().out
        deepreload.found_now.clear()


class TestAddSubmodule:
    def test_mod_none_is_noop(self):
        assert deepreload.add_submodule(None, None, "foo", "foo") is None

    def test_sets_attribute(self):
        mod = types.ModuleType("parent")
        sub = types.ModuleType("parent.child")
        deepreload.add_submodule(mod, sub, "parent.child", "child")
        assert mod.child is sub

    def test_submod_none_looked_up_in_sys_modules(self):
        mod = types.ModuleType("parent")
        deepreload.add_submodule(mod, None, "os", "os")
        assert mod.os is sys.modules["os"]


class TestDeepImportHook:
    def test_empty_module_name(self):
        with pytest.raises(ValueError, match="Empty module name"):
            deepreload.deep_import_hook("")

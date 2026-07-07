"""Tests for the %matplotlib and %pylab magics (IPython.core.magics.pylab)."""

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from IPython.core.magics import pylab as pylab_magics_module


@pytest.fixture
def fake_enable_pylab(monkeypatch):
    """Replace shell.enable_pylab with a recorder to keep user_ns clean."""
    calls = {}

    def enable_pylab(gui=None, import_all=True):
        calls["gui"] = gui
        calls["import_all"] = import_all
        return gui, "agg", calls.pop("clobbered", [])

    monkeypatch.setattr(ip, "enable_pylab", enable_pylab)
    return calls


class FakeUninitializedApp:
    @staticmethod
    def initialized():
        return False


class FakeInitializedApp:
    pylab_import_all = False

    @staticmethod
    def initialized():
        return True

    @classmethod
    def instance(cls):
        return cls()


class FakeInitializedAppNoPylabTrait:
    @staticmethod
    def initialized():
        return True

    @classmethod
    def instance(cls):
        return cls()


def test_matplotlib_list(capsys):
    ip.run_line_magic("matplotlib", "--list")
    out = capsys.readouterr().out
    assert out.startswith("Available matplotlib backends: [")
    backends = out.split(":", 1)[1]
    assert "'agg'" in backends
    assert "'auto'" in backends


def test_matplotlib_explicit_backend(capsys):
    """An explicit non-auto backend is activated but not announced."""
    ip.run_line_magic("matplotlib", "agg")
    out = capsys.readouterr().out
    # explicit backend choice is not announced
    assert "Using matplotlib backend" not in out
    assert matplotlib.get_backend().lower() == "agg"
    assert matplotlib.is_interactive()


def test_matplotlib_no_arg_prints_backend(capsys):
    """Without an argument, the default backend is used and announced."""
    ip.run_line_magic("matplotlib", "")
    out = capsys.readouterr().out
    assert "Using matplotlib backend:" in out
    assert "agg" in out.lower()


def test_pylab_default_no_app(fake_enable_pylab, capsys, monkeypatch):
    monkeypatch.setattr(pylab_magics_module, "Application", FakeUninitializedApp)
    ip.run_line_magic("pylab", "")
    assert fake_enable_pylab == {"gui": None, "import_all": True}
    out = capsys.readouterr().out
    assert "Using matplotlib backend: agg" in out
    assert "%pylab is deprecated" in out
    assert "Populating the interactive namespace from numpy and matplotlib" in out


def test_pylab_gui_argument(fake_enable_pylab, capsys, monkeypatch):
    monkeypatch.setattr(pylab_magics_module, "Application", FakeUninitializedApp)
    ip.run_line_magic("pylab", "agg")
    assert fake_enable_pylab == {"gui": "agg", "import_all": True}
    out = capsys.readouterr().out
    # explicit gui choice is not announced
    assert "Using matplotlib backend" not in out
    assert "Populating the interactive namespace from numpy and matplotlib" in out


def test_pylab_no_import_all_flag(fake_enable_pylab, capsys):
    ip.run_line_magic("pylab", "--no-import-all")
    assert fake_enable_pylab == {"gui": None, "import_all": False}
    capsys.readouterr()


def test_pylab_import_all_from_app(fake_enable_pylab, capsys, monkeypatch):
    """With an initialized app, pylab_import_all governs the default."""
    monkeypatch.setattr(pylab_magics_module, "Application", FakeInitializedApp)
    ip.run_line_magic("pylab", "")
    assert fake_enable_pylab == {"gui": None, "import_all": False}
    capsys.readouterr()


def test_pylab_app_without_pylab_import_all(fake_enable_pylab, capsys, monkeypatch):
    """An initialized app without the pylab_import_all trait defaults to True."""
    monkeypatch.setattr(
        pylab_magics_module, "Application", FakeInitializedAppNoPylabTrait
    )
    ip.run_line_magic("pylab", "")
    assert fake_enable_pylab == {"gui": None, "import_all": True}
    capsys.readouterr()


def test_pylab_warns_about_clobbered_names(fake_enable_pylab, capsys, monkeypatch):
    monkeypatch.setattr(pylab_magics_module, "Application", FakeUninitializedApp)
    fake_enable_pylab["clobbered"] = ["plot", "sum"]
    with pytest.warns(UserWarning, match="pylab import has clobbered"):
        ip.run_line_magic("pylab", "")
    capsys.readouterr()

"""Tests for IPython.core.magics.packaging (%pip, %conda, %mamba, %micromamba, %uv).

No package manager is ever executed. ``ip.system`` is replaced by a recorder
so only the constructed command lines are asserted.
"""

import shlex
import sys
from pathlib import Path

import pytest

from IPython.testing.decorators import skip_win32

from IPython.core.magics import packaging


@pytest.fixture
def recorded_commands(monkeypatch):
    """Capture command strings passed to ip.system instead of running them."""
    commands = []
    monkeypatch.setattr(ip, "system", commands.append)
    return commands


@pytest.fixture
def fake_conda_env(monkeypatch, tmp_path):
    """Pretend the current interpreter lives in a conda environment."""
    meta = tmp_path / "conda-meta"
    meta.mkdir()
    (meta / "history").write_text("", encoding="utf-8")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(sys, "executable", str(bindir / "python"))
    # Make sure ambient conda/mamba variables can't leak into the tests.
    monkeypatch.delenv("CONDA_EXE", raising=False)
    monkeypatch.delenv("MAMBA_EXE", raising=False)
    return tmp_path


@skip_win32
def test_pip_runs_current_interpreter(recorded_commands, capsys):
    ip.run_line_magic("pip", "install foo")
    assert recorded_commands == [
        "%s -m pip install foo" % shlex.quote(sys.executable)
    ]
    assert "restart the kernel" in capsys.readouterr().out


@skip_win32
def test_pip_quotes_interpreter_path(recorded_commands, monkeypatch):
    monkeypatch.setattr(sys, "executable", "/spa ced/python")
    ip.run_line_magic("pip", "install foo")
    assert recorded_commands == ["'/spa ced/python' -m pip install foo"]


def test_pip_windows_quoting(recorded_commands, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\python.exe")
    ip.run_line_magic("pip", "install foo")
    assert recorded_commands == [
        '"C:\\Program Files\\python.exe" -m pip install foo'
    ]


@skip_win32
def test_uv_runs_current_interpreter(recorded_commands, capsys):
    ip.run_line_magic("uv", "pip install foo")
    assert recorded_commands == [
        "%s -m uv pip install foo" % shlex.quote(sys.executable)
    ]
    assert "restart the kernel" in capsys.readouterr().out


def test_uv_windows_quoting(recorded_commands, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\python.exe")
    ip.run_line_magic("uv", "pip install foo")
    assert recorded_commands == [
        '"C:\\Program Files\\python.exe" -m uv pip install foo'
    ]


def test_conda_outside_conda_environment_raises(monkeypatch, tmp_path):
    # sys.prefix has no conda-meta/history -> not a conda environment
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    with pytest.raises(ValueError, match="%pip install"):
        ip.run_line_magic("conda", "install foo")
    with pytest.raises(ValueError, match="%pip install"):
        ip.run_line_magic("mamba", "install foo")
    with pytest.raises(ValueError, match="%pip install"):
        ip.run_line_magic("micromamba", "install foo")


def test_conda_install_adds_prefix(fake_conda_env, recorded_commands, monkeypatch):
    conda_exe = fake_conda_env / "bin" / "conda"
    conda_exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("CONDA_EXE", str(conda_exe))
    ip.run_line_magic("conda", "install foo")
    assert recorded_commands == [
        "%s install --prefix %s foo" % (conda_exe.resolve(), fake_conda_env)
    ]


def test_conda_env_flag_suppresses_prefix(
    fake_conda_env, recorded_commands, monkeypatch
):
    conda_exe = fake_conda_env / "bin" / "conda"
    conda_exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("CONDA_EXE", str(conda_exe))
    ip.run_line_magic("conda", "install -n other foo")
    assert recorded_commands == ["%s install -n other foo" % conda_exe.resolve()]


def test_conda_adds_yes_when_stdin_disabled(
    fake_conda_env, recorded_commands, monkeypatch
):
    conda_exe = fake_conda_env / "bin" / "conda"
    conda_exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("CONDA_EXE", str(conda_exe))
    # A shell with a `kernel` attribute means stdin can't answer prompts.
    monkeypatch.setattr(ip, "kernel", object(), raising=False)
    ip.run_line_magic("conda", "remove foo")
    assert recorded_commands == [
        "%s remove --yes --prefix %s foo" % (conda_exe.resolve(), fake_conda_env)
    ]


def test_conda_does_not_duplicate_yes(fake_conda_env, recorded_commands, monkeypatch):
    conda_exe = fake_conda_env / "bin" / "conda"
    conda_exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("CONDA_EXE", str(conda_exe))
    monkeypatch.setattr(ip, "kernel", object(), raising=False)
    ip.run_line_magic("conda", "install -y foo")
    assert recorded_commands == [
        "%s install --prefix %s -y foo" % (conda_exe.resolve(), fake_conda_env)
    ]


def test_conda_command_not_requiring_prefix(
    fake_conda_env, recorded_commands, monkeypatch
):
    conda_exe = fake_conda_env / "bin" / "conda"
    conda_exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("CONDA_EXE", str(conda_exe))
    ip.run_line_magic("conda", "env list")
    assert recorded_commands == ["%s env list" % conda_exe.resolve()]


def test_mamba_uses_mamba_exe(fake_conda_env, recorded_commands, monkeypatch):
    mamba_exe = fake_conda_env / "bin" / "mamba"
    mamba_exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("MAMBA_EXE", str(mamba_exe))
    ip.run_line_magic("mamba", "install foo")
    assert recorded_commands == [
        "%s install --prefix %s foo" % (mamba_exe.resolve(), fake_conda_env)
    ]


def test_micromamba_found_next_to_python(fake_conda_env, recorded_commands):
    # No MAMBA_EXE set; a micromamba binary sits next to sys.executable.
    micromamba = fake_conda_env / "bin" / "micromamba"
    micromamba.write_text("", encoding="utf-8")
    ip.run_line_magic("micromamba", "update foo")
    assert recorded_commands == [
        "%s update --prefix %s foo" % (micromamba, fake_conda_env)
    ]


def test_executable_extracted_from_conda_history(fake_conda_env):
    history = fake_conda_env / "conda-meta" / "history"
    history.write_text(
        "==> 2024-01-01 00:00:00 <==\n"
        "# cmd: /opt/conda/bin/conda create -p /tmp/env python\n",
        encoding="utf-8",
    )
    assert (
        packaging._get_conda_like_executable("conda") == "/opt/conda/bin/conda"
    )


def test_executable_falls_back_to_command_name(fake_conda_env, monkeypatch):
    # CONDA_EXE points at a file that doesn't exist, history has no cmd line.
    monkeypatch.setenv("CONDA_EXE", str(fake_conda_env / "nonexistent"))
    assert packaging._get_conda_like_executable("conda") == "conda"


def test_conda_empty_line(fake_conda_env, recorded_commands):
    ip.run_line_magic("conda", "")
    assert recorded_commands == ["conda  "]

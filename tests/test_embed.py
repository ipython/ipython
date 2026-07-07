"""Test embedding of IPython"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import atexit
import gc
import os
import subprocess
import sys
import types

import pytest

from traitlets.config import Config

from IPython.core.history import HistoryManager
from IPython.core.interactiveshell import InteractiveShell
from IPython.terminal.embed import (
    InteractiveShellEmbed,
    KillEmbedded,
    _EmbedGlobals,
)
from IPython.utils.tempdir import NamedFileInTemporaryDirectory
from IPython.testing.decorators import skip_win32
from IPython.testing import IPYTHON_TESTING_TIMEOUT_SCALE

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_embed_globals_lookup_order():
    module_dict = {"g": 1, "shadowed": "global"}
    local_ns = {"foo": 42, "shadowed": "local"}
    g = _EmbedGlobals(module_dict, local_ns)

    # caller locals first, as regular closure lookup would
    assert g["foo"] == 42
    assert g["shadowed"] == "local"
    # then the module globals
    assert g["g"] == 1
    # globals set in the real module after entry are still visible
    module_dict["late"] = "added"
    assert g["late"] == "added"
    # missing names raise KeyError so LOAD_GLOBAL falls back to builtins
    with pytest.raises(KeyError):
        g["nowhere"]


def test_embed_globals_exec_nested_scopes():
    local_ns = {"foo": 42}
    g = _EmbedGlobals({"g": 1}, local_ns)

    # nested scopes resolve caller locals through globals, and
    # builtins (`range`) are still reachable
    exec("result = (lambda: [foo + g for _ in range(1)][0])()", g, local_ns)
    assert local_ns["result"] == 43


def test_embed_globals_sync_to_module():
    module_dict = {"unchanged": 1, "rebound": 2, "removed": 3}
    g = _EmbedGlobals(module_dict, {})

    # STORE_GLOBAL/DELETE_GLOBAL from code defined in the shell bypass
    # __setitem__ and mutate the C-level dict storage directly
    exec(
        "def s():\n"
        "    global added, rebound, removed\n"
        "    added = 5\n"
        "    rebound = 20\n"
        "    del removed\n"
        "s()",
        g,
        {},
    )
    assert "added" not in module_dict
    g.sync_to_module()
    assert module_dict["added"] == 5
    assert module_dict["rebound"] == 20
    assert module_dict["unchanged"] == 1
    assert "removed" not in module_dict


# -----------------------------------------------------------------------------
# In-process tests for InteractiveShellEmbed
# -----------------------------------------------------------------------------


def _queue_input(monkeypatch, lines):
    """Feed `lines` to the simple-prompt input(), then EOF to exit."""
    lines_iter = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(lines_iter)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)


def _embed_config():
    config = Config()
    config.HistoryManager.enabled = False
    config.TerminalInteractiveShell.simple_prompt = True
    config.TerminalInteractiveShell.confirm_exit = False
    config.TerminalInteractiveShell.colors = "nocolor"
    return config


@pytest.fixture(autouse=True)
def _reap_embedded_shells():
    """Release embedded shells created during a test.

    InteractiveShell.__init__ registers a bound method with atexit, which
    keeps every embedded shell (and its HistoryManager) alive for the rest
    of the test session; the HistoryManager._instances WeakSet then grows
    past _max_inst and trips the guard assertion in unrelated test files.
    """
    before = set(HistoryManager._instances)
    yield
    for hm in set(HistoryManager._instances) - before:
        if hm.save_thread is not None:
            atexit.unregister(hm.save_thread.stop)
            hm.save_thread.stop()
        if hm.shell is not None:
            atexit.unregister(hm.shell.atexit_operations)
        HistoryManager._instances.discard(hm)
    gc.collect()


@pytest.fixture
def embed_shell(monkeypatch):
    """An in-process InteractiveShellEmbed.

    The singleton machinery (the shell instance created by conftest) is
    saved and restored around the test, the same way ``IPython.embed()``
    does it.
    """
    monkeypatch.setattr(HistoryManager, "_max_inst", float("inf"))
    monkeypatch.setenv("IPY_TEST_SIMPLE_PROMPT", "1")
    # InteractiveShellEmbed.__init__ replaces sys.excepthook
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)

    saved_instance = InteractiveShell._instance
    saved_cls = type(saved_instance) if saved_instance is not None else None
    if saved_instance is not None:
        saved_cls.clear_instance()
    saved_inactive = set(InteractiveShellEmbed._inactive_locations)

    shell = InteractiveShellEmbed(config=_embed_config())

    yield shell

    InteractiveShellEmbed.clear_instance()
    InteractiveShellEmbed._inactive_locations.clear()
    InteractiveShellEmbed._inactive_locations.update(saved_inactive)
    if saved_instance is not None:
        saved_cls.clear_instance()
        for subclass in saved_cls._walk_mro():
            subclass._instance = saved_instance


def test_embed_shell_call_runs_code(embed_shell, monkeypatch, capsys):
    """A full __call__ runs the interactive loop against the caller's locals."""
    _queue_input(monkeypatch, ["zzz_embed_result = zzz_local + 1"])
    fake_mod = types.ModuleType("zzz_fake_embed_mod")
    local_ns = {"zzz_local": 41}
    orig_user_ns = embed_shell.user_ns
    embed_shell.exit_msg = "zzz-embed-bye"
    embed_shell(header="embed-test-header", local_ns=local_ns, module=fake_mod)
    # code typed in the shell could see the caller's locals, and new
    # variables were synced back into the local namespace on exit
    assert local_ns["zzz_embed_result"] == 42
    out, _ = capsys.readouterr()
    assert "embed-test-header" in out
    assert "zzz-embed-bye" in out
    # namespaces are restored after the call
    assert embed_shell.user_ns is orig_user_ns


def test_embed_shell_dummy_mode(embed_shell, monkeypatch):
    # dummy=True returns without ever prompting (no input is queued, so
    # actually prompting would raise)
    embed_shell(dummy=True)
    embed_shell.dummy_mode = True
    embed_shell()
    # dummy=False overrides dummy_mode and really interacts
    _queue_input(monkeypatch, [])
    embed_shell(dummy=False, local_ns={}, module=types.ModuleType("zzz_dummy_mod"))


def test_embed_shell_module_lookup_failure_warns(embed_shell, monkeypatch):
    """If the caller's __name__ is not in sys.modules, a fake module is used."""
    _queue_input(monkeypatch, [])
    src = "def zzz_caller(shell):\n    shell(local_ns={'zzz_a': 1})\n"
    weird_globals = {"__name__": "zzz_not_a_real_module_xyz"}
    exec(src, weird_globals)
    with pytest.warns(UserWarning, match="Failed to get module"):
        weird_globals["zzz_caller"](embed_shell)


def test_kill_embedded_magic(embed_shell, capsys):
    embed_shell(dummy=True)  # sets the call location id
    embed_shell.run_line_magic("kill_embedded", "--yes")
    out, _ = capsys.readouterr()
    assert "call location will not reactivate" in out
    assert embed_shell.embedded_active is False
    # a later call at the killed location returns immediately, without
    # prompting (no input is queued)
    embed_shell(_call_location_id=embed_shell._call_location_id)
    # reactivating discards the location again
    embed_shell.embedded_active = True
    assert embed_shell.embedded_active is True


def test_kill_embedded_instance(embed_shell, capsys):
    embed_shell(dummy=True)
    embed_shell.run_line_magic("kill_embedded", "--instance --yes --exit")
    out, _ = capsys.readouterr()
    assert "instance will not reactivate" in out
    assert embed_shell._init_location_id in InteractiveShellEmbed._inactive_locations
    assert embed_shell.embedded_active is False
    # --exit also asks the mainloop to stop
    assert embed_shell.keep_running is False
    embed_shell.embedded_active = True
    assert embed_shell.embedded_active is True


def test_kill_embedded_declined(embed_shell, monkeypatch, capsys):
    embed_shell(dummy=True)
    monkeypatch.setattr(
        "IPython.terminal.embed.ask_yes_no", lambda *args, **kwargs: False
    )
    embed_shell.run_line_magic("kill_embedded", "")
    assert embed_shell.embedded_active is True
    embed_shell.run_line_magic("kill_embedded", "--instance")
    assert embed_shell.embedded_active is True


def test_exit_raise_magic(embed_shell, monkeypatch):
    _queue_input(monkeypatch, [])
    embed_shell.run_line_magic("exit_raise", "")
    assert embed_shell.should_raise is True
    assert embed_shell.keep_running is False
    with pytest.raises(KillEmbedded):
        embed_shell(local_ns={}, module=types.ModuleType("zzz_exit_raise_mod"))


def test_embed_function_in_process(monkeypatch, capsys):
    """IPython.embed() runs in the caller's scope and restores the old shell."""
    from IPython.terminal import embed as embed_module

    monkeypatch.setattr(HistoryManager, "_max_inst", float("inf"))
    monkeypatch.setenv("IPY_TEST_SIMPLE_PROMPT", "1")
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    # use a lightweight default config (no sqlite history, no confirm-exit)
    monkeypatch.setattr(embed_module, "load_default_config", _embed_config)
    _queue_input(
        monkeypatch,
        [
            "zzz_embed_fn = 2 + 2",
            "print('zzz-value', zzz_embed_fn)",
            "print('zzz-outer', zzz_outer)",
        ],
    )
    # no sys.ps1/ps2 defined: nothing to save or restore
    monkeypatch.delattr(sys, "ps1", raising=False)
    monkeypatch.delattr(sys, "ps2", raising=False)
    saved_instance = InteractiveShell._instance
    zzz_outer = 10
    embed_module.embed(header="zzz-fn-header")
    # the previously active shell is restored
    assert InteractiveShell._instance is saved_instance
    out, _ = capsys.readouterr()
    assert "zzz-fn-header" in out
    assert "zzz-value 4" in out
    # the embedded shell saw the caller's locals
    assert "zzz-outer 10" in out


def test_embed_function_restores_sys_ps1(monkeypatch, capsys):
    """embed() saves and restores sys.ps1/ps2 when they are defined."""
    from IPython.terminal import embed as embed_module

    monkeypatch.setattr(HistoryManager, "_max_inst", float("inf"))
    monkeypatch.setenv("IPY_TEST_SIMPLE_PROMPT", "1")
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(embed_module, "load_default_config", _embed_config)
    monkeypatch.setattr(sys, "ps1", "zzz>>> ", raising=False)
    monkeypatch.setattr(sys, "ps2", "zzz... ", raising=False)
    _queue_input(monkeypatch, [])
    embed_module.embed()
    assert sys.ps1 == "zzz>>> "
    assert sys.ps2 == "zzz... "


_sample_embed = """
import IPython

a = 3
b = 14
print(a, '.', b)

IPython.embed()

print('bye!')
"""

_exit = "exit\r"


_sample_embed_locals = """
import IPython

shadowed = 'global'
seen_by_module = None

def check_seen():
    return seen_by_module

def bar(foo):
    shadowed = 'local'
    IPython.embed(banner1='', banner2='')
    return foo * 2

print('RESULT:', bar(21))
print('SYNCED:', check_seen())
"""

_embed_locals_commands = "\r".join(
    [
        "print('genexp:', sum(foo for _ in range(1)))",
        "print('lambda:', (lambda: foo)())",
        "print('listcomp:', [foo for _ in range(1)][0])",
        "def g():\r    return foo\r",
        "print('nested-def:', g())",
        "print('shadow:', (lambda: shadowed)())",
        "def s():\r    global seen_by_module\r    seen_by_module = 'set-in-shell'\r",
        "s()",
        "exit",
    ]
) + "\r"


def test_ipython_embed_sees_locals_in_nested_scopes():
    """Nested scopes created in an embedded shell see the caller's locals.

    Generator expressions, lambdas, comprehensions and function bodies typed
    into an embedded shell look up free variables through ``globals()``;
    check they can still resolve variables local to the embedding frame.
    See https://github.com/ipython/ipython/issues/136
    """
    with NamedFileInTemporaryDirectory("file_with_embed.py", "w") as f:
        f.write(_sample_embed_locals)
        f.flush()
        f.close()

        env = os.environ.copy()
        env["IPY_TEST_SIMPLE_PROMPT"] = "1"

        p = subprocess.Popen(
            [sys.executable, f.name],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="UTF-8",
        )
        std, err = p.communicate(_embed_locals_commands)

        assert p.returncode == 0, (p.returncode, std, err)
        assert "NameError" not in std, std
        assert "genexp: 21" in std
        assert "lambda: 21" in std
        assert "listcomp: 21" in std
        assert "nested-def: 21" in std
        # a local shadowing a module global wins, as in regular closures
        assert "shadow: local" in std
        assert "RESULT: 42" in std
        # `global` assignments made by shell-defined functions reach the
        # real module once the shell exits
        assert "SYNCED: set-in-shell" in std


def test_ipython_embed():
    """test that `IPython.embed()` works"""
    with NamedFileInTemporaryDirectory("file_with_embed.py", "w") as f:
        f.write(_sample_embed)
        f.flush()
        f.close()  # otherwise msft won't be able to read the file

        # run `python file_with_embed.py`
        cmd = [sys.executable, f.name]
        env = os.environ.copy()
        env["IPY_TEST_SIMPLE_PROMPT"] = "1"

        p = subprocess.Popen(
            cmd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="UTF-8",
        )
        std, err = p.communicate(_exit)
        assert isinstance(std, str), (std, err, p.returncode)

        assert p.returncode == 0, (p.returncode, std)
        assert "3 . 14" in std
        if os.name != "nt":
            # TODO: Fix up our different stdout references, see issue gh-14
            assert "IPython" in std
        assert "bye!" in std


@skip_win32
def test_nest_embed():
    """test that `IPython.embed()` is nestable"""
    import pexpect

    ipy_prompt = r"]:"  # ansi color codes give problems matching beyond this
    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"

    child = pexpect.spawn(
        sys.executable, ["-m", "IPython", "--colors=nocolor"], env=env
    )
    child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
    child.expect(ipy_prompt)
    child.timeout = 5 * IPYTHON_TESTING_TIMEOUT_SCALE
    child.sendline("import IPython")
    child.sendline("from IPython.core.history import HistoryManager")
    child.sendline("HistoryManager._max_inst = 3")
    child.expect(ipy_prompt)
    child.sendline("ip0 = get_ipython()")
    # enter first nested embed
    child.sendline("IPython.embed()")
    # skip the banner until we get to a prompt
    try:
        prompted = -1
        while prompted != 0:
            prompted = child.expect([ipy_prompt, "\r\n"])
    except pexpect.TIMEOUT as e:
        print(e)
        # child.interact()
    child.sendline("embed1 = get_ipython()")
    child.expect(ipy_prompt)
    child.sendline("print('true' if embed1 is not ip0 else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    child.sendline("print('true' if IPython.get_ipython() is embed1 else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    # enter second nested embed
    child.sendline("IPython.embed()")
    # skip the banner until we get to a prompt
    try:
        prompted = -1
        while prompted != 0:
            prompted = child.expect([ipy_prompt, "\r\n"])
    except pexpect.TIMEOUT as e:
        print(e)
        # child.interact()
    child.sendline("embed2 = get_ipython()")
    child.expect(ipy_prompt)
    child.sendline("print('true' if embed2 is not embed1 else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    child.sendline("print('true' if embed2 is IPython.get_ipython() else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    child.sendline("exit")
    # back at first embed
    child.expect(ipy_prompt)
    child.sendline("print('true' if get_ipython() is embed1 else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    child.sendline("print('true' if IPython.get_ipython() is embed1 else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    child.sendline("exit")
    # back at launching scope
    child.expect(ipy_prompt)
    child.sendline("print('true' if get_ipython() is ip0 else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    child.sendline("print('true' if IPython.get_ipython() is ip0 else 'false')")
    assert child.expect(["true\r\n", "false\r\n"]) == 0
    child.expect(ipy_prompt)
    child.sendline("exit")
    child.close()

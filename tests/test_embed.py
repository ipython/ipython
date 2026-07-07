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

import os
import subprocess
import sys

import pytest

from IPython.terminal.embed import _EmbedGlobals
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

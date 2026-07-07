"""Test installing editor hooks"""

import sys
from unittest import mock

import pytest

from IPython import get_ipython
from IPython.core.error import TryNext
from IPython.lib import editorhooks


def test_install_editor():
    called = []

    def fake_popen(*args, **kwargs):
        called.append(
            {
                "args": args,
                "kwargs": kwargs,
            }
        )
        return mock.MagicMock(**{"wait.return_value": 0})

    editorhooks.install_editor("foo -l {line} -f {filename}", wait=False)

    with mock.patch("subprocess.Popen", fake_popen):
        get_ipython().hooks.editor("the file", 64)

    assert len(called) == 1
    args = called[0]["args"]
    kwargs = called[0]["kwargs"]

    assert kwargs == {"shell": True}

    if sys.platform.startswith("win"):
        expected = ["foo", "-l", "64", "-f", "the file"]
    else:
        expected = "foo -l 64 -f 'the file'"
    cmd = args[0]
    assert cmd == expected


def test_install_editor_sets_editor_attribute():
    editorhooks.install_editor("myed {filename}")
    assert get_ipython().editor == "myed {filename}"


def test_line_none_defaults_to_zero():
    called = []

    def fake_popen(*args, **kwargs):
        called.append(args[0])
        return mock.MagicMock(**{"wait.return_value": 0})

    editorhooks.install_editor("foo -l {line} -f {filename}")

    with mock.patch("subprocess.Popen", fake_popen):
        get_ipython().hooks.editor("the file", None)

    if sys.platform.startswith("win"):
        assert called == [["foo", "-l", "0", "-f", "the file"]]
    else:
        assert called == ["foo -l 0 -f 'the file'"]


def test_nonzero_exit_raises_trynext():
    def fake_popen(*args, **kwargs):
        return mock.MagicMock(**{"wait.return_value": 1})

    editorhooks.install_editor("failing-editor {filename}")

    with mock.patch("subprocess.Popen", fake_popen), pytest.raises(TryNext):
        get_ipython().hooks.editor("the file", 1)


def test_wait_prompts_for_enter():
    prompts = []

    def fake_popen(cmd, **kwargs):
        # editor hooks installed by other tests stay in the hook chain and
        # run first; make them fail so they raise TryNext and the chain
        # falls through to the hook installed by this test.
        code = 0 if "slow-editor" in cmd else 1
        return mock.MagicMock(**{"wait.return_value": code})

    editorhooks.install_editor("slow-editor {filename}", wait=True)

    with (
        mock.patch("subprocess.Popen", fake_popen),
        mock.patch("builtins.input", lambda prompt: prompts.append(prompt)),
    ):
        get_ipython().hooks.editor("the file", 1)

    assert prompts == ["Press Enter when done editing:"]


@pytest.mark.parametrize(
    "hook, template, wait",
    [
        (editorhooks.komodo, "komodo -l {line} {filename}", True),
        (editorhooks.scite, "scite {filename} -goto:{line}", False),
        (editorhooks.notepadplusplus, "notepad++ -n{line} {filename}", False),
        (editorhooks.jed, "jed +{line} {filename}", False),
        (editorhooks.idle, "idle {filename}", False),
        (editorhooks.mate, "mate -w -l {line} {filename}", False),
        (editorhooks.emacs, "emacs +{line} {filename}", False),
        (editorhooks.gnuclient, "gnuclient -nw +{line} {filename}", False),
        (editorhooks.crimson_editor, "cedt.exe /L:{line} {filename}", False),
        (editorhooks.kate, "kate -u -l {line} {filename}", False),
    ],
)
def test_editor_shortcuts(hook, template, wait):
    """Each named-editor helper installs the expected command template"""
    with mock.patch.object(editorhooks, "install_editor") as install:
        hook()
    if wait:
        install.assert_called_once_with(template, wait=True)
    else:
        install.assert_called_once_with(template)


def test_editor_shortcuts_custom_exe():
    with mock.patch.object(editorhooks, "install_editor") as install:
        editorhooks.emacs("/opt/bin/emacs")
    install.assert_called_once_with("/opt/bin/emacs +{line} {filename}")

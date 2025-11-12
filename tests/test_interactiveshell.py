# -*- coding: utf-8 -*-
"""Tests for the key interactiveshell module.

Historically the main classes in interactiveshell have been under-tested.  This
module should grow as many single-method tests as possible to trap many of the
recurring bugs we seem to encounter with high-level interaction.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import asyncio
import ast
import os
import shlex
import signal
import shutil
import sys
import tempfile
import time
import pytest
from unittest import mock

from os.path import join

from IPython.core.error import InputRejected
from IPython.core import interactiveshell
from IPython.core.oinspect import OInfo
from IPython.testing.decorators import (
    skipif,
    skip_win32,
    onlyif_unicode_paths,
    onlyif_cmds_exist,
    skip_if_not_osx,
)
from IPython.testing import tools as tt
from IPython.utils.process import find_cmd

from IPython.core.interactiveshell import InteractiveShell
# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
# This is used by every single test, no point repeating it ad nauseam

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


class DerivedInterrupt(KeyboardInterrupt):
    pass


def test_stream_performance(capsys) -> None:
    """It should be fast to execute."""
    src = "for i in range(250_000): print(i)"
    start = time.perf_counter()
    ip.run_cell(src)
    end = time.perf_counter()
    # We try to read as otherwise on failure, pytest will print the 250k lines to stdout.
    capsys.readouterr()
    duration = end - start
    assert duration < 10


def test_naked_string_cells():
    """Test that cells with only naked strings are fully executed"""
    # Use store_history=True so that quiet() checks this cell (not a previous
    # semicolon-terminated cell), and the display hook actually fires.
    # Also clear _ / __ / ___ so the hook can update them cleanly even if a
    # previous test left them in a state that differs from the hook's tracking.
    ip.user_ns.pop("_", None)
    ip.user_ns.pop("__", None)
    ip.user_ns.pop("___", None)
    # First, single-line inputs
    ip.run_cell('"a"\n', store_history=True)
    assert ip.user_ns["_"] == "a"
    # And also multi-line cells
    ip.run_cell('"""a\nb"""\n', store_history=True)
    assert ip.user_ns["_"] == "a\nb"


def test_run_empty_cell():
    """Just make sure we don't get a horrible error with a blank
    cell of input. Yes, I did overlook that."""
    old_xc = ip.execution_count
    res = ip.run_cell("")
    assert ip.execution_count == old_xc
    assert res.execution_count is None


def test_run_cell_multiline():
    """Multi-block, multi-line cells must execute correctly."""
    src = "\n".join(
        [
            "x=1",
            "y=2",
            "if 1:",
            "    x += 1",
            "    y += 1",
        ]
    )
    res = ip.run_cell(src)
    assert ip.user_ns["x"] == 2
    assert ip.user_ns["y"] == 3
    assert res.success is True
    assert res.result is None


def test_multiline_string_cells():
    "Code sprinkled with multiline strings should execute (GH-306)"
    ip.run_cell("tmp=0")
    assert ip.user_ns["tmp"] == 0
    res = ip.run_cell('tmp=1;"""a\nb"""\n')
    assert ip.user_ns["tmp"] == 1
    assert res.success is True
    assert res.result == "a\nb"


def test_dont_cache_with_semicolon():
    "Ending a line with semicolon should not cache the returned object (GH-307)"
    oldlen = len(ip.user_ns["Out"])
    for cell in ["1;", "1;1;"]:
        res = ip.run_cell(cell, store_history=True)
        newlen = len(ip.user_ns["Out"])
        assert oldlen == newlen
        assert res.result is None
    i = 0
    # also test the default caching behavior
    for cell in ["1", "1;1"]:
        ip.run_cell(cell, store_history=True)
        newlen = len(ip.user_ns["Out"])
        i += 1
        assert oldlen + i == newlen


def test_syntax_error():
    res = ip.run_cell("raise = 3")
    assert isinstance(res.error_before_exec, SyntaxError)


def test_open_standard_input_stream():
    res = ip.run_cell("open(0)")
    assert isinstance(res.error_in_exec, ValueError)


def test_open_standard_output_stream():
    res = ip.run_cell("open(1)")
    assert isinstance(res.error_in_exec, ValueError)


def test_open_standard_error_stream():
    res = ip.run_cell("open(2)")
    assert isinstance(res.error_in_exec, ValueError)


def test_In_variable():
    "Verify that In variable grows with user input (GH-284)"
    oldlen = len(ip.user_ns["In"])
    ip.run_cell("1;", store_history=True)
    newlen = len(ip.user_ns["In"])
    assert oldlen + 1 == newlen
    assert ip.user_ns["In"][-1] == "1;"


def test_magic_names_in_string():
    ip.run_cell('a = """\n%exit\n"""')
    assert ip.user_ns["a"] == "\n%exit\n"


def test_trailing_newline():
    """test that running !(command) does not raise a SyntaxError"""
    ip.run_cell("!(true)\n", False)
    ip.run_cell("!(true)\n\n\n", False)


def test_gh_597():
    """Pretty-printing lists of objects with non-ascii reprs may cause
    problems."""

    class Spam(object):
        def __repr__(self):
            return "\xe9" * 50

    import IPython.core.formatters

    f = IPython.core.formatters.PlainTextFormatter()
    f([Spam(), Spam()])


def test_future_flags():
    """Check that future flags are used for parsing code (gh-777)"""
    ip.run_cell("from __future__ import barry_as_FLUFL")
    try:
        ip.run_cell("prfunc_return_val = 1 <> 2")
        assert "prfunc_return_val" in ip.user_ns
    finally:
        # Reset compiler flags so we don't mess up other tests.
        ip.compile.reset_compiler_flags()


def test_can_pickle():
    "Can we pickle objects defined interactively (GH-29)"
    ip = get_ipython()
    ip.reset()
    ip.run_cell(
        (
            "class Mylist(list):\n"
            "    def __init__(self,x=[]):\n"
            "        list.__init__(self,x)"
        )
    )
    ip.run_cell("w=Mylist([1,2,3])")

    from pickle import dumps

    # We need to swap in our main module - this is only necessary
    # inside the test framework, because IPython puts the interactive module
    # in place (but the test framework undoes this).
    _main = sys.modules["__main__"]
    sys.modules["__main__"] = ip.user_module
    try:
        res = dumps(ip.user_ns["w"])
    finally:
        sys.modules["__main__"] = _main
    assert isinstance(res, bytes)


def test_global_ns():
    "Code in functions must be able to access variables outside them."
    ip = get_ipython()
    ip.run_cell("a = 10")
    ip.run_cell(("def f(x):\n" "    return x + a"))
    ip.run_cell("b = f(12)")
    assert ip.user_ns["b"] == 22


def test_bad_custom_tb():
    """Check that InteractiveShell is protected from bad custom exception handlers"""
    ip.set_custom_exc((IOError,), lambda etype, value, tb: 1 / 0)
    assert ip.custom_exceptions == (IOError,)
    with tt.AssertPrints("Custom TB Handler failed", channel="stderr"):
        ip.run_cell('raise IOError("foo")')
    assert ip.custom_exceptions == ()


def test_bad_custom_tb_return():
    """Check that InteractiveShell is protected from bad return types in custom exception handlers"""
    ip.set_custom_exc((NameError,), lambda etype, value, tb, tb_offset=None: 1)
    assert ip.custom_exceptions == (NameError,)
    with tt.AssertPrints("Custom TB Handler failed", channel="stderr"):
        ip.run_cell("a=abracadabra")
    assert ip.custom_exceptions == ()


def test_drop_by_id():
    myvars = {"a": object(), "b": object(), "c": object()}
    ip.push(myvars, interactive=False)
    for name in myvars:
        assert name in ip.user_ns, name
        assert name in ip.user_ns_hidden, name
    ip.user_ns["b"] = 12
    ip.drop_by_id(myvars)
    for name in ["a", "c"]:
        assert name not in ip.user_ns, name
        assert name not in ip.user_ns_hidden, name
    assert ip.user_ns["b"] == 12
    ip.reset()


def test_var_expand():
    ip.user_ns["f"] = "Ca\xf1o"
    assert ip.var_expand("echo $f") == "echo Ca\xf1o"
    assert ip.var_expand("echo {f}") == "echo Ca\xf1o"
    assert ip.var_expand("echo {f[:-1]}") == "echo Ca\xf1"
    assert ip.var_expand("echo {1*2}") == "echo 2"

    assert (
        ip.var_expand("grep x | awk '{print $1}'") == "grep x | awk '{print $1}'"
    )

    ip.user_ns["f"] = b"Ca\xc3\xb1o"
    # This should not raise any exception:
    ip.var_expand("echo $f")


def test_var_expand_local():
    """Test local variable expansion in !system and %magic calls"""
    # !system
    ip.run_cell(
        "def test():\n"
        '    lvar = "ttt"\n'
        "    ret = !echo {lvar}\n"
        "    return ret[0]\n"
    )
    res = ip.user_ns["test"]()
    assert "ttt" in res

    # %magic
    ip.run_cell(
        "def makemacro():\n"
        '    macroname = "macro_var_expand_locals"\n'
        "    %macro {macroname} codestr\n"
    )
    ip.user_ns["codestr"] = "str(12)"
    ip.run_cell("makemacro()")
    assert "macro_var_expand_locals" in ip.user_ns


def test_var_expand_self():
    """Test variable expansion with the name 'self', which was failing.

    See https://github.com/ipython/ipython/issues/1878#issuecomment-7698218
    """
    ip.run_cell(
        "class cTest:\n"
        '  classvar="see me"\n'
        "  def test(self):\n"
        "    res = !echo Variable: {self.classvar}\n"
        "    return res[0]\n"
    )
    assert "see me" in ip.user_ns["cTest"]().test()


def test_bad_var_expand():
    """var_expand on invalid formats shouldn't raise"""
    # SyntaxError
    assert ip.var_expand("{'a':5}") == "{'a':5}"
    # NameError
    assert ip.var_expand("{asdf}") == "{asdf}"
    # ZeroDivisionError
    assert ip.var_expand("{1/0}") == "{1/0}"


def test_silent_postexec():
    """run_cell(silent=True) doesn't invoke pre/post_run_cell callbacks"""
    pre_explicit = mock.Mock()
    pre_always = mock.Mock()
    post_explicit = mock.Mock()
    post_always = mock.Mock()
    all_mocks = [pre_explicit, pre_always, post_explicit, post_always]

    ip.events.register("pre_run_cell", pre_explicit)
    ip.events.register("pre_execute", pre_always)
    ip.events.register("post_run_cell", post_explicit)
    ip.events.register("post_execute", post_always)

    try:
        ip.run_cell("1", silent=True)
        assert pre_always.called
        assert not pre_explicit.called
        assert post_always.called
        assert not post_explicit.called
        # double-check that non-silent exec did what we expected
        # silent to avoid
        ip.run_cell("1")
        assert pre_explicit.called
        assert post_explicit.called
        (info,) = pre_explicit.call_args[0]
        (result,) = post_explicit.call_args[0]
        assert info == result.info
        # check that post hooks are always called
        [m.reset_mock() for m in all_mocks]
        ip.run_cell("syntax error")
        assert pre_always.called
        assert pre_explicit.called
        assert post_always.called
        assert post_explicit.called
        (info,) = pre_explicit.call_args[0]
        (result,) = post_explicit.call_args[0]
        assert info == result.info
    finally:
        # remove post-exec
        ip.events.unregister("pre_run_cell", pre_explicit)
        ip.events.unregister("pre_execute", pre_always)
        ip.events.unregister("post_run_cell", post_explicit)
        ip.events.unregister("post_execute", post_always)


def test_silent_noadvance():
    """run_cell(silent=True) doesn't advance execution_count"""
    ec = ip.execution_count
    # silent should force store_history=False
    ip.run_cell("1", store_history=True, silent=True)

    assert ec == ip.execution_count
    # double-check that non-silent exec did what we expected
    # silent to avoid
    ip.run_cell("1", store_history=True)
    assert ec + 1 == ip.execution_count


def test_silent_nodisplayhook():
    """run_cell(silent=True) doesn't trigger displayhook"""
    d = dict(called=False)

    trap = ip.display_trap
    save_hook = trap.hook

    def failing_hook(*args, **kwargs):
        d["called"] = True

    try:
        trap.hook = failing_hook
        res = ip.run_cell("1", silent=True)
        assert not d["called"]
        assert res.result is None
        # double-check that non-silent exec did what we expected
        # silent to avoid
        ip.run_cell("1")
        assert d["called"]
    finally:
        trap.hook = save_hook


def test_ofind_line_magic():
    from IPython.core.magic import register_line_magic

    @register_line_magic
    def lmagic(line):
        "A line magic"

    # Get info on line magic
    lfind = ip._ofind("lmagic")
    info = OInfo(
        found=True,
        isalias=False,
        ismagic=True,
        namespace="IPython internal",
        obj=lmagic,
        parent=None,
    )
    assert lfind == info


def test_ofind_cell_magic():
    from IPython.core.magic import register_cell_magic

    @register_cell_magic
    def cmagic(line, cell):
        "A cell magic"

    # Get info on cell magic
    find = ip._ofind("cmagic")
    info = OInfo(
        found=True,
        isalias=False,
        ismagic=True,
        namespace="IPython internal",
        obj=cmagic,
        parent=None,
    )
    assert find == info


def test_ofind_property_with_error():
    class A(object):
        @property
        def foo(self):
            raise NotImplementedError()  # pragma: no cover

    a = A()

    found = ip._ofind("a.foo", [("locals", locals())])
    info = OInfo(
        found=True,
        isalias=False,
        ismagic=False,
        namespace="locals",
        obj=A.foo,
        parent=a,
    )
    assert found == info


def test_ofind_multiple_attribute_lookups():
    class A(object):
        @property
        def foo(self):
            raise NotImplementedError()  # pragma: no cover

    a = A()
    a.a = A()
    a.a.a = A()

    found = ip._ofind("a.a.a.foo", [("locals", locals())])
    info = OInfo(
        found=True,
        isalias=False,
        ismagic=False,
        namespace="locals",
        obj=A.foo,
        parent=a.a.a,
    )
    assert found == info


def test_ofind_slotted_attributes():
    class A(object):
        __slots__ = ["foo"]

        def __init__(self):
            self.foo = "bar"

    a = A()
    found = ip._ofind("a.foo", [("locals", locals())])
    info = OInfo(
        found=True,
        isalias=False,
        ismagic=False,
        namespace="locals",
        obj=a.foo,
        parent=a,
    )
    assert found == info

    found = ip._ofind("a.bar", [("locals", locals())])
    expected = OInfo(
        found=False,
        isalias=False,
        ismagic=False,
        namespace=None,
        obj=None,
        parent=a,
    )
    assert found == expected


def test_ofind_prefers_property_to_instance_level_attribute():
    class A(object):
        @property
        def foo(self):
            return "bar"

    a = A()
    a.__dict__["foo"] = "baz"
    assert a.foo == "bar"
    found = ip._ofind("a.foo", [("locals", locals())])
    assert found.obj is A.foo


def test_custom_syntaxerror_exception():
    called = []

    def my_handler(shell, etype, value, tb, tb_offset=None):
        called.append(etype)
        shell.showtraceback((etype, value, tb), tb_offset=tb_offset)

    ip.set_custom_exc((SyntaxError,), my_handler)
    try:
        ip.run_cell("1f")
        # Check that this was called, and only once.
        assert called == [SyntaxError]
    finally:
        # Reset the custom exception hook
        ip.set_custom_exc((), None)


def test_custom_exception():
    called = []

    def my_handler(shell, etype, value, tb, tb_offset=None):
        called.append(etype)
        shell.showtraceback((etype, value, tb), tb_offset=tb_offset)

    ip.set_custom_exc((ValueError,), my_handler)
    try:
        res = ip.run_cell("raise ValueError('test')")
        # Check that this was called, and only once.
        assert called == [ValueError]
        # Check that the error is on the result object
        assert isinstance(res.error_in_exec, ValueError)
    finally:
        # Reset the custom exception hook
        ip.set_custom_exc((), None)


@mock.patch("builtins.print")
def test_showtraceback_with_surrogates(mocked_print):
    values = []

    def mock_print_func(value, sep=" ", end="\n", file=sys.stdout, flush=False):
        values.append(value)
        if value == chr(0xD8FF):
            raise UnicodeEncodeError("utf-8", chr(0xD8FF), 0, 1, "")

    # mock builtins.print
    mocked_print.side_effect = mock_print_func

    # ip._showtraceback() is replaced in globalipapp.py.
    # Call original method to test.
    interactiveshell.InteractiveShell._showtraceback(ip, None, None, chr(0xD8FF))

    assert mocked_print.call_count == 2
    assert values == [chr(0xD8FF), "\\ud8ff"]


def test_mktempfile():
    filename = ip.mktempfile()
    # Check that we can open the file again on Windows
    with open(filename, "w", encoding="utf-8") as f:
        f.write("abc")

    filename = ip.mktempfile(data="blah")
    with open(filename, "r", encoding="utf-8") as f:
        assert f.read() == "blah"


def test_new_main_mod():
    # Smoketest to check that this accepts a unicode module name
    name = "jiefmw"
    mod = ip.new_main_mod("%s.py" % name, name)
    assert mod.__name__ == name


def test_get_exception_only():
    try:
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        msg = ip.get_exception_only()
    assert msg == "KeyboardInterrupt\n"

    try:
        raise DerivedInterrupt("foo")
    except KeyboardInterrupt:
        msg = ip.get_exception_only()
    assert msg == "tests.test_interactiveshell.DerivedInterrupt: foo\n"


def test_inspect_text():
    ip.run_cell("a = 5")
    text = ip.object_inspect_text("a")
    assert isinstance(text, str)


def test_last_execution_result():
    """Check that last execution result gets set correctly (GH-10702)"""
    result = ip.run_cell("a = 5; a")
    assert ip.last_execution_succeeded
    assert ip.last_execution_result.result == 5

    result = ip.run_cell("a = x_invalid_id_x")
    assert not ip.last_execution_succeeded
    assert not ip.last_execution_result.success
    assert isinstance(ip.last_execution_result.error_in_exec, NameError)


def test_reset_aliasing():
    """Check that standard posix aliases work after %reset."""
    if os.name != "posix":
        return

    ip.reset()
    for cmd in ("clear", "more", "less", "man"):
        res = ip.run_cell("%" + cmd)
        assert res.success is True


@pytest.fixture
def safe_execfile_nonascii_path():
    """Setup and teardown for non-ascii path test"""
    BASETESTDIR = tempfile.mkdtemp()
    TESTDIR = join(BASETESTDIR, "åäö")
    os.mkdir(TESTDIR)
    with open(
        join(TESTDIR, "åäötestscript.py"), "w", encoding="utf-8"
    ) as sfile:
        sfile.write("pass\n")
    oldpath = os.getcwd()
    os.chdir(TESTDIR)
    fname = "åäötestscript.py"

    yield fname

    os.chdir(oldpath)
    shutil.rmtree(BASETESTDIR)


@pytest.mark.skipif(
    sys.implementation.name == "pypy"
    and ((7, 3, 13) < sys.implementation.version < (7, 3, 16)),
    reason="Unicode issues with scandir on PyPy, see https://github.com/pypy/pypy/issues/4860",
)
@onlyif_unicode_paths
def test_safe_execfile_nonascii_path(safe_execfile_nonascii_path):
    """Test safe_execfile with non-ascii path"""
    ip.safe_execfile(safe_execfile_nonascii_path, {}, raise_exceptions=True)


class ExitCodeChecks:
    def setup_method(self):
        """Setup method replacing TempFileMixin and setUp"""
        self.system = ip.system_raw
        self.fname = None
        self._temp_files = []

    def teardown_method(self):
        """Cleanup temp files"""
        for f in self._temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except (OSError, IOError):
                    pass

    def mktmp(self, src, ext=".py"):
        """Create a temporary file with the given source."""
        fd, self.fname = tempfile.mkstemp(ext)
        os.close(fd)
        self._temp_files.append(self.fname)
        with open(self.fname, "w", encoding="utf-8") as f:
            f.write(src)

    def test_exit_code_ok(self):
        self.system("exit 0")
        assert ip.user_ns["_exit_code"] == 0

    def test_exit_code_error(self):
        self.system("exit 1")
        assert ip.user_ns["_exit_code"] == 1

    @skipif(not hasattr(signal, "SIGALRM"))
    def test_exit_code_signal(self):
        self.mktmp(
            "import signal, time\n"
            "signal.setitimer(signal.ITIMER_REAL, 0.1)\n"
            "time.sleep(1)\n"
        )
        self.system("%s %s" % (shlex.quote(sys.executable), shlex.quote(self.fname)))
        assert ip.user_ns["_exit_code"] == -signal.SIGALRM

    @onlyif_cmds_exist("csh")
    def test_exit_code_signal_csh(self):  # pragma: no cover
        SHELL = os.environ.get("SHELL", None)
        os.environ["SHELL"] = find_cmd("csh")
        try:
            self.test_exit_code_signal()
        finally:
            if SHELL is not None:
                os.environ["SHELL"] = SHELL
            else:
                del os.environ["SHELL"]


class TestSystemRaw(ExitCodeChecks):
    def setup_method(self):
        super().setup_method()
        self.system = ip.system_raw

    @onlyif_unicode_paths
    def test_1(self):
        """Test system_raw with non-ascii cmd"""
        cmd = """python -c "'åäö'"   """
        ip.system_raw(cmd)

    @mock.patch("subprocess.call", side_effect=KeyboardInterrupt)
    @mock.patch("os.system", side_effect=KeyboardInterrupt)
    def test_control_c(self, *mocks):
        try:
            self.system("sleep 1 # won't happen")
        except KeyboardInterrupt:  # pragma: no cove
            pytest.fail(
                "system call should intercept "
                "keyboard interrupt from subprocess.call"
            )
        assert ip.user_ns["_exit_code"] == -signal.SIGINT


@pytest.mark.parametrize("magic_cmd", ["pip", "conda", "cd"])
def test_magic_warnings(magic_cmd):
    if sys.platform == "win32":
        to_mock = "os.system"
        expected_arg, expected_kwargs = magic_cmd, dict()
    else:
        to_mock = "subprocess.call"
        expected_arg, expected_kwargs = magic_cmd, dict(
            shell=True, executable=os.environ.get("SHELL", None)
        )

    with mock.patch(to_mock, return_value=0) as mock_sub:
        with pytest.warns(Warning, match=r"You executed the system command"):
            ip.system_raw(magic_cmd)
        mock_sub.assert_called_once_with(expected_arg, **expected_kwargs)


# TODO: Exit codes are currently ignored on Windows.
class TestSystemPipedExitCode(ExitCodeChecks):
    def setup_method(self):
        super().setup_method()
        self.system = ip.system_piped

    @skip_win32
    def test_exit_code_ok(self):
        ExitCodeChecks.test_exit_code_ok(self)

    @skip_win32
    def test_exit_code_error(self):
        ExitCodeChecks.test_exit_code_error(self)

    @skip_win32
    def test_exit_code_signal(self):
        ExitCodeChecks.test_exit_code_signal(self)


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing"""
    fd, fname = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    yield fname
    try:
        os.remove(fname)
    except (OSError, IOError):
        pass


def test_extraneous_loads(temp_python_file):
    """Test we're not loading modules on startup that we shouldn't."""
    with open(temp_python_file, "w") as f:
        f.write(
            "import sys\n"
            "print('numpy' in sys.modules)\n"
            "print('ipyparallel' in sys.modules)\n"
            "print('ipykernel' in sys.modules)\n"
        )
    out = "False\nFalse\nFalse\n"
    tt.ipexec_validate(temp_python_file, out)


class Negator(ast.NodeTransformer):
    """Negates all number literals in an AST."""

    def visit_Num(self, node):
        node.value = -node.value
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, int):
            return self.visit_Num(node)
        return node


@pytest.fixture
def ast_negator_transform():
    """Setup and teardown for negator AST transformer"""
    negator = Negator()
    ip.ast_transformers.append(negator)
    yield negator
    ip.ast_transformers.remove(negator)


def test_ast_transform_non_int_const(ast_negator_transform):
    with tt.AssertPrints("hello"):
        ip.run_cell('print("hello")')


def test_ast_transform_run_cell(ast_negator_transform):
    with tt.AssertPrints("-34"):
        ip.run_cell("print(12 + 22)")

    # A named reference to a number shouldn't be transformed.
    ip.user_ns["n"] = 55
    with tt.AssertNotPrints("-55"):
        ip.run_cell("print(n)")


def test_ast_transform_timeit(ast_negator_transform):
    called = set()

    def f(x):
        called.add(x)

    ip.push({"f": f})

    with tt.AssertPrints("std. dev. of"):
        ip.run_line_magic("timeit", "-n1 f(1)")
    assert called == {-1}
    called.clear()

    with tt.AssertPrints("std. dev. of"):
        ip.run_cell_magic("timeit", "-n1 f(2)", "f(3)")
    assert called == {-2, -3}


def test_ast_transform_time(ast_negator_transform):
    called = []

    def f(x):
        called.append(x)

    ip.push({"f": f})

    # Test with an expression
    with tt.AssertPrints("Wall time: "):
        ip.run_line_magic("time", "f(5+9)")
    assert called == [-14]
    called[:] = []

    # Test with a statement (different code path)
    with tt.AssertPrints("Wall time: "):
        ip.run_line_magic("time", "a = f(-3 + -2)")
    assert called == [5]


def test_ast_transform_macro(ast_negator_transform):
    ip.push({"a": 10})
    # The AST transformation makes this do a+=-1
    ip.define_macro("amacro", "a+=1\nprint(a)")

    with tt.AssertPrints("9"):
        ip.run_cell("amacro")
    with tt.AssertPrints("8"):
        ip.run_cell("amacro")


def test_transform_only_once():
    cleanup = 0
    line_t = 0

    def count_cleanup(lines):
        nonlocal cleanup
        cleanup += 1
        return lines

    def count_line_t(lines):
        nonlocal line_t
        line_t += 1
        return lines

    ip.input_transformer_manager.cleanup_transforms.append(count_cleanup)
    ip.input_transformer_manager.line_transforms.append(count_line_t)

    ip.run_cell("1")

    assert cleanup == 1
    assert line_t == 1


class IntegerWrapper(ast.NodeTransformer):
    """Wraps all integers in a call to Integer()"""

    # for Python 3.7 and earlier
    def visit_Num(self, node):
        if isinstance(node.value, int):
            return ast.Call(
                func=ast.Name(id="Integer", ctx=ast.Load()), args=[node], keywords=[]
            )
        return node

    # For Python 3.8+
    def visit_Constant(self, node):
        if isinstance(node.value, int):
            return self.visit_Num(node)
        return node


@pytest.fixture
def integer_wrapper_transform():
    """Setup and teardown for integer wrapper AST transformer"""
    intwrapper = IntegerWrapper()
    ip.ast_transformers.append(intwrapper)

    calls = []

    def Integer(*args):
        calls.append(args)
        return args

    ip.push({"Integer": Integer})

    yield intwrapper, calls

    ip.ast_transformers.remove(intwrapper)
    del ip.user_ns["Integer"]


def test_ast_transform2_run_cell(integer_wrapper_transform):
    intwrapper, calls = integer_wrapper_transform
    ip.run_cell("n = 2")
    assert calls == [(2,)]

    # This shouldn't throw an error
    ip.run_cell("o = 2.0")
    assert ip.user_ns["o"] == 2.0


def test_ast_transform2_run_cell_non_int(integer_wrapper_transform):
    intwrapper, calls = integer_wrapper_transform
    ip.run_cell("n = 'a'")
    assert calls == []


def test_ast_transform2_timeit(integer_wrapper_transform):
    intwrapper, calls = integer_wrapper_transform
    called = set()

    def f(x):
        called.add(x)

    ip.push({"f": f})

    with tt.AssertPrints("std. dev. of"):
        ip.run_line_magic("timeit", "-n1 f(1)")
    assert called == {(1,)}
    called.clear()

    with tt.AssertPrints("std. dev. of"):
        ip.run_cell_magic("timeit", "-n1 f(2)", "f(3)")
    assert called == {(2,), (3,)}


    def test_timeit_multiline_cell_magic(self):
        called = set()

        def f(x):
            called.add(x)

        ip.push({"f": f})

        code = """
f(3)
f(4)
"""

        with tt.AssertPrints("std. dev. of"):
            ip.run_cell_magic("timeit", "-n1 -r2 f(2)", code)

        self.assertEqual(called, {(2,), (3,), (4,)})


class ErrorTransformer(ast.NodeTransformer):
    """Throws an error when it sees a number."""

    def visit_Constant(self, node):
        if isinstance(node.value, int):
            raise ValueError("test")
        return node


def test_ast_transform_error_unregistering():
    err_transformer = ErrorTransformer()
    ip.ast_transformers.append(err_transformer)

    with pytest.warns(UserWarning, match="It will be unregistered"):
        ip.run_cell("1 + 2")

    # This should have been removed.
    assert err_transformer not in ip.ast_transformers


class StringRejector(ast.NodeTransformer):
    """Throws an InputRejected when it sees a string literal.

    Used to verify that NodeTransformers can signal that a piece of code should
    not be executed by throwing an InputRejected.
    """

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            raise InputRejected("test")
        return node


@pytest.fixture
def string_rejector_transformer():
    """Setup and teardown for string rejector AST transformer"""
    transformer = StringRejector()
    ip.ast_transformers.append(transformer)
    yield transformer
    ip.ast_transformers.remove(transformer)


def test_input_rejection(string_rejector_transformer):
    """Check that NodeTransformers can reject input."""

    expect_exception_tb = tt.AssertPrints("InputRejected: test")
    expect_no_cell_output = tt.AssertNotPrints("'unsafe'", suppress=False)

    # Run the same check twice to verify that the transformer is not
    # disabled after raising.
    with expect_exception_tb, expect_no_cell_output:
        ip.run_cell("'unsafe'")

    with expect_exception_tb, expect_no_cell_output:
        res = ip.run_cell("'unsafe'")

    assert isinstance(res.error_before_exec, InputRejected)


def test__IPYTHON__():
    # This shouldn't raise a NameError, that's all
    __IPYTHON__


class DummyRepr(object):
    def __repr__(self):
        return "DummyRepr"

    def _repr_html_(self):
        return "<b>dummy</b>"

    def _repr_javascript_(self):
        return "console.log('hi');", {"key": "value"}


def test_user_variables():
    # enable all formatters
    ip.display_formatter.active_types = ip.display_formatter.format_types

    ip.user_ns["dummy"] = d = DummyRepr()
    keys = {"dummy", "doesnotexist"}
    r = ip.user_expressions({key: key for key in keys})

    assert keys == set(r.keys())
    dummy = r["dummy"]
    assert {"status", "data", "metadata"} == set(dummy.keys())
    assert dummy["status"] == "ok"
    data = dummy["data"]
    metadata = dummy["metadata"]
    assert data.get("text/html") == d._repr_html_()
    js, jsmd = d._repr_javascript_()
    assert data.get("application/javascript") == js
    assert metadata.get("application/javascript") == jsmd

    dne = r["doesnotexist"]
    assert dne["status"] == "error"
    assert dne["ename"] == "NameError"

    # back to text only
    ip.display_formatter.active_types = ["text/plain"]


def test_user_expression():
    # enable all formatters
    ip.display_formatter.active_types = ip.display_formatter.format_types
    query = {
        "a": "1 + 2",
        "b": "1/0",
    }
    r = ip.user_expressions(query)
    import pprint

    pprint.pprint(r)
    assert set(r.keys()) == set(query.keys())
    a = r["a"]
    assert {"status", "data", "metadata"} == set(a.keys())
    assert a["status"] == "ok"
    data = a["data"]
    metadata = a["metadata"]
    assert data.get("text/plain") == "3"

    b = r["b"]
    assert b["status"] == "error"
    assert b["ename"] == "ZeroDivisionError"

    # back to text only
    ip.display_formatter.active_types = ["text/plain"]


def _syntaxerror_transformer(lines):
    """Transformer that raises SyntaxError when it sees 'syntaxerror'"""
    for line in lines:
        pos = line.find("syntaxerror")
        if pos >= 0:
            e = SyntaxError('input contains "syntaxerror"')
            e.text = line
            e.offset = pos + 1
            raise e
    return lines


@pytest.fixture
def syntaxerror_input_transformer():
    """Setup and teardown for SyntaxError input transformer"""
    ip.input_transformers_post.append(_syntaxerror_transformer)
    yield
    ip.input_transformers_post.remove(_syntaxerror_transformer)


def test_syntaxerror_input_transformer(syntaxerror_input_transformer):
    """Check that SyntaxError raised by an input transformer is handled by run_cell()"""
    with tt.AssertPrints("1234"):
        ip.run_cell("1234")
    with tt.AssertPrints("SyntaxError: invalid syntax"):
        ip.run_cell("1 2 3")  # plain python syntax error
    with tt.AssertPrints('SyntaxError: input contains "syntaxerror"'):
        ip.run_cell("2345  # syntaxerror")  # input transformer syntax error
    with tt.AssertPrints("3456"):
        ip.run_cell("3456")


def test_warning_suppression():
    """Test that warnings are suppressed properly and can be re-issued."""
    ip.run_cell("import warnings")
    try:
        with pytest.warns(UserWarning, match="asdf"):
            ip.run_cell("warnings.warn('asdf')")
        # Here's the real test -- if we run that again, we should get the
        # warning again. Traditionally, each warning was only issued once per
        # IPython session (approximately), even if the user typed in new and
        # different code that should have also triggered the warning, leading
        # to much confusion.
        with pytest.warns(UserWarning, match="asdf"):
            ip.run_cell("warnings.warn('asdf')")
    finally:
        ip.run_cell("del warnings")


def test_deprecation_warning():
    """Test that deprecation warnings are properly raised."""
    ip.run_cell(
        """
import warnings
def wrn():
    warnings.warn(
        "I AM  A WARNING",
        DeprecationWarning
    )
        """
    )
    try:
        with pytest.warns(DeprecationWarning, match="I AM  A WARNING"):
            ip.run_cell("wrn()")
    finally:
        ip.run_cell("del warnings")
        ip.run_cell("del wrn")


@pytest.fixture
def temp_module_with_warning():
    """Create a temporary Python module with a warning function"""
    fd, fname = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    with open(fname, "w") as f:
        f.write(
            """
import warnings
def wrn():
    warnings.warn(
        "I AM  A WARNING",
        DeprecationWarning
    )
"""
        )
    yield fname
    try:
        os.remove(fname)
    except (OSError, IOError):
        pass


def test_no_dep(temp_module_with_warning):
    """
    No deprecation warning should be raised from imported functions
    """
    ip.run_cell("from {} import wrn".format(temp_module_with_warning))

    with tt.AssertNotPrints("I AM  A WARNING"):
        ip.run_cell("wrn()")
    ip.run_cell("del wrn")


def test_custom_exc_count():
    hook = mock.Mock(return_value=None)
    ip.set_custom_exc((SyntaxError,), hook)
    before = ip.execution_count
    ip.run_cell("def foo()", store_history=True)
    # restore default excepthook
    ip.set_custom_exc((), None)
    assert hook.call_count == 1
    assert ip.execution_count == before + 1


def test_run_cell_async():
    ip.run_cell("import asyncio")
    coro = ip.run_cell_async("await asyncio.sleep(0.01)\n5")
    assert asyncio.iscoroutine(coro)
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(coro)
    assert isinstance(result, interactiveshell.ExecutionResult)
    assert result.result == 5


def test_run_cell_await():
    ip.run_cell("import asyncio")
    result = ip.run_cell("await asyncio.sleep(0.01); 10")
    assert ip.user_ns["_"] == 10


def test_run_cell_asyncio_run():
    ip.run_cell("import asyncio")
    result = ip.run_cell("await asyncio.sleep(0.01); 1")
    assert ip.user_ns["_"] == 1
    result = ip.run_cell("asyncio.run(asyncio.sleep(0.01)); 2")
    assert ip.user_ns["_"] == 2
    result = ip.run_cell("await asyncio.sleep(0.01); 3")
    assert ip.user_ns["_"] == 3


def test_should_run_async():
    assert not ip.should_run_async("a = 5", transformed_cell="a = 5")
    assert ip.should_run_async("await x", transformed_cell="await x")
    assert ip.should_run_async(
        "import asyncio; await asyncio.sleep(1)",
        transformed_cell="import asyncio; await asyncio.sleep(1)",
    )


def test_set_custom_completer():
    num_completers = len(ip.Completer.matchers)

    def foo(*args, **kwargs):
        return "I'm a completer!"

    ip.set_custom_completer(foo, 0)

    # check that we've really added a new completer
    assert len(ip.Completer.matchers) == num_completers + 1

    # check that the first completer is the function we defined
    assert ip.Completer.matchers[0]() == "I'm a completer!"

    # clean up
    ip.Completer.custom_matchers.pop()


@pytest.fixture
def restore_showtraceback():
    """Restore the original showtraceback method after test"""
    orig_showtraceback = interactiveshell.InteractiveShell.showtraceback
    yield
    interactiveshell.InteractiveShell.showtraceback = orig_showtraceback


def test_set_show_tracebacks_none(restore_showtraceback):
    """Test that the interactive shell is resilient when showtracebacks is set to None"""

    result = ip.run_cell(
        """
        import IPython.core.interactiveshell
        IPython.core.interactiveshell.InteractiveShell.showtraceback = None

        assert False, "This should not raise an exception"
    """
    )
    print(result)

    assert result.result is None
    assert isinstance(result.error_in_exec, TypeError)
    assert str(result.error_in_exec) == "'NoneType' object is not callable"


def test_set_show_tracebacks_noop(restore_showtraceback):
    """Test that the interactive shell is resilient when showtracebacks is a no-op"""

    result = ip.run_cell(
        """
        import IPython.core.interactiveshell
        IPython.core.interactiveshell.InteractiveShell.showtraceback = lambda *args, **kwargs: None

        assert False, "This should not raise an exception"
    """
    )
    print(result)

    assert result.result is None
    assert isinstance(result.error_in_exec, AssertionError)
    assert str(result.error_in_exec) == "This should not raise an exception"


def test_enable_gui_tk_simple_prompt_message(capsys):
    simple_prompt = ip.simple_prompt
    ip.simple_prompt = True
    try:
        ip.enable_gui("tk")
        output = capsys.readouterr().out
    finally:
        ip.simple_prompt = simple_prompt

    assert output == (
        "Tk is supported natively when running with `--simple-prompt`; "
        "no event loop hook will be installed.\n"
    )


@skip_if_not_osx
def test_enable_gui_osx():
    simple_prompt = ip.simple_prompt
    ip.simple_prompt = False

    ip.enable_gui("osx")
    assert ip.active_eventloop == "osx"
    ip.enable_gui()

    # The following line fails for IPython <= 8.25.0
    ip.enable_gui("macosx")
    assert ip.active_eventloop == "osx"
    ip.enable_gui()

    ip.simple_prompt = simple_prompt

def test_cell_meta():
    ip:InteractiveShell = get_ipython()
    ip.reset()
    reply = ip.run_cell(("a=1\n"), cell_meta={"test": [1, 2, 3]})
    assert reply.info.cell_meta == {"test": [1, 2, 3]}

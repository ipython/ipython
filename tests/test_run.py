# encoding: utf-8
"""Tests for code execution (%run and related), which is particularly tricky.

Because of how %run manages namespaces, and the fact that we are trying here to
verify subtle object deletion and reference counting issues, the %run tests
will be kept in this separate file.  This makes it easier to aggregate in one
place the tricks needed to handle it; most other magics are much easier to test
and we do so in a common test_magic file.

Note that any test using `run -i` should make sure to do a `reset` afterwards,
as otherwise it may influence later tests.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.


import functools
import os
import platform
import random
import string
import sys
import textwrap
from os.path import join as pjoin
from unittest.mock import patch

import pytest
from tempfile import TemporaryDirectory

from IPython.core import debugger
from IPython.testing import decorators as dec
from IPython.testing import tools as tt
from IPython.utils.capture import capture_output
from IPython.utils.io import temp_pyfile


@pytest.fixture
def run_tmpfile():
    created = []

    def mktmp(src, ext=".py"):
        fname = temp_pyfile(src, ext)
        created.append(fname)
        return fname

    yield mktmp

    for fname in created:
        try:
            os.unlink(fname)
        except OSError:
            pass


def doctest_refbug():
    """Very nasty problem with references held by multiple runs of a script.
    See: https://github.com/ipython/ipython/issues/141

    In [1]: _ip.clear_main_mod_cache()
    # random

    In [2]: %run refbug

    In [3]: call_f()
    lowercased: hello

    In [4]: %run refbug

    In [5]: call_f()
    lowercased: hello
    lowercased: hello
    """


def doctest_run_builtins():
    r"""Check that %run doesn't damage __builtins__.

    In [1]: import tempfile

    In [2]: bid1 = id(__builtins__)

    In [3]: fname = tempfile.mkstemp('.py')[1]

    In [3]: f = open(fname, 'w', encoding='utf-8')

    In [4]: dummy= f.write('pass\n')

    In [5]: f.flush()

    In [6]: t1 = type(__builtins__)

    In [7]: %run $fname

    In [7]: f.close()

    In [8]: bid2 = id(__builtins__)

    In [9]: t2 = type(__builtins__)

    In [10]: t1 == t2
    Out[10]: True

    In [10]: bid1 == bid2
    Out[10]: True

    In [12]: try:
       ....:     os.unlink(fname)
       ....: except:
       ....:     pass
       ....:
    """


def doctest_run_option_parser():
    r"""Test option parser in %run.

    In [1]: %run print_argv.py
    []

    In [2]: %run print_argv.py print*.py
    ['print_argv.py']

    In [3]: %run -G print_argv.py print*.py
    ['print*.py']

    """


@dec.skip_win32
def doctest_run_option_parser_for_posix():
    r"""Test option parser in %run (Linux/OSX specific).

    You can use a backslash to escape glob in POSIX systems:

    In [1]: %run print_argv.py print\\*.py
    ['print*.py']

    You can also use single or double quotes to suppress glob expansion (#12726):

    In [2]: %run print_argv.py 'print*.py'
    ['print*.py']

    In [3]: %run print_argv.py "print*.py"
    ['print*.py']

    """


doctest_run_option_parser_for_posix.__skip_doctest__ = sys.platform == "win32"


@dec.skip_if_not_win32
def doctest_run_option_parser_for_windows():
    r"""Test option parser in %run (Windows specific).

    In Windows, you can't escape ``*` `by backslash:

    In [1]: %run print_argv.py print\\*.py
    ['print\\\\*.py']

    You can use quote to escape glob:

    In [2]: %run print_argv.py 'print*.py'
    ["'print*.py'"]

    """


doctest_run_option_parser_for_windows.__skip_doctest__ = sys.platform != "win32"


def doctest_reset_del():
    """Test that resetting doesn't cause errors in __del__ methods.

    In [2]: class A(object):
       ...:     def __del__(self):
       ...:         print(str("Hi"))
       ...:

    In [3]: a = A()

    In [4]: get_ipython().reset(); import gc; x = gc.collect()
    Hi

    In [5]: 1+1
    Out[5]: 2
    """


# For some tests, it will be handy to organize them in a class with a common
# setup that makes a temp file

import sysconfig

is_freethreaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))


def test_builtins_id(run_tmpfile):
    """Check that %run doesn't damage __builtins__"""
    _ip = get_ipython()
    fname = run_tmpfile("a = [1,2,3]\nb = 1")
    bid1 = id(_ip.user_ns["__builtins__"])
    _ip.run_line_magic("run", fname)
    bid2 = id(_ip.user_ns["__builtins__"])
    assert bid1 == bid2


def test_builtins_type(run_tmpfile):
    """Check that the type of __builtins__ doesn't change with %run."""
    _ip = get_ipython()
    fname = run_tmpfile("a = [1,2,3]\nb = 1")
    _ip.run_line_magic("run", fname)
    assert type(_ip.user_ns["__builtins__"]) == type(sys)


def test_run_profile(run_tmpfile):
    """Test that the option -p, which invokes the profiler, do not crash by invoking execfile"""
    _ip = get_ipython()
    fname = run_tmpfile("a = [1,2,3]\nb = 1")
    _ip.run_line_magic("run", "-p %s" % fname)


def test_run_debug_twice(run_tmpfile):
    # https://github.com/ipython/ipython/issues/10028
    _ip = get_ipython()
    fname = run_tmpfile("a = [1,2,3]\nb = 1")
    with tt.fake_input(["c"]):
        _ip.run_line_magic("run", "-d %s" % fname)
    with tt.fake_input(["c"]):
        _ip.run_line_magic("run", "-d %s" % fname)


def test_run_debug_twice_with_breakpoint(run_tmpfile):
    """Make a valid python temp file."""
    _ip = get_ipython()
    fname = run_tmpfile("a = [1,2,3]\nb = 1")
    with tt.fake_input(["b 2", "c", "c"]):
        _ip.run_line_magic("run", "-d %s" % fname)

    with tt.fake_input(["c"]):
        with tt.AssertNotPrints("KeyError"):
            _ip.run_line_magic("run", "-d %s" % fname)


def test_simpledef(run_tmpfile):
    """Test that simple class definitions work."""
    fname = run_tmpfile("class foo: pass\ndef f(): return foo()")
    _ip.run_line_magic("run", str(fname))
    _ip.run_cell("t = isinstance(f(), foo)")
    assert _ip.user_ns["t"] is True


@pytest.mark.xfail(
    platform.python_implementation() == "PyPy",
    reason="expecting __del__ call on exit is unreliable and doesn't happen on PyPy",
)
def test_obj_del(run_tmpfile):
    """Test that object's __del__ methods are called on exit."""
    fname = run_tmpfile(
        "class A(object):\n"
        "    def __del__(self):\n"
        "        print('object A deleted')\n"
        "a = A()\n"
    )
    tt.ipexec_validate(fname, "object A deleted", None)


def test_aggressive_namespace_cleanup(run_tmpfile):
    """Test that namespace cleanup is not too aggressive GH-238"""
    empty_fname = run_tmpfile("")
    src = (
        "ip = get_ipython()\n"
        "for i in range(5):\n"
        "   try:\n"
        "       ip.run_line_magic(%r, %r)\n"
        "   except NameError as e:\n"
        "       print(i)\n"
        "       break\n" % ("run", empty_fname)
    )
    fname = run_tmpfile(src)
    _ip.run_line_magic("run", str(fname))
    _ip.run_cell("ip == get_ipython()")
    assert _ip.user_ns["i"] == 4


def test_run_second(run_tmpfile):
    """Test that running a second file doesn't clobber the first, gh-3547"""
    fname = run_tmpfile("avar = 1\ndef afunc():\n  return avar\n")
    empty_fname = run_tmpfile("")
    _ip.run_line_magic("run", fname)
    _ip.run_line_magic("run", empty_fname)
    assert _ip.user_ns["afunc"]() == 1


@pytest.mark.xfail(is_freethreaded, reason="C-third leaks on free-threaded python")
def test_tclass(run_tmpfile):
    mydir = os.path.dirname(__file__)
    tc = os.path.join(mydir, "tclass")
    src = f"""\
import gc
%run "{tc}" C-first
gc.collect(0)
%run "{tc}" C-second
gc.collect(0)
%run "{tc}" C-third
gc.collect(0)
%reset -f
"""
    fname = run_tmpfile(src, ".ipy")
    out = """\
ARGV 1-: ['C-first']
ARGV 1-: ['C-second']
tclass.py: deleting object: C-first
ARGV 1-: ['C-third']
tclass.py: deleting object: C-second
tclass.py: deleting object: C-third
"""
    tt.ipexec_validate(fname, out, None)


def test_run_i_after_reset(run_tmpfile):
    """Check that %run -i still works after %reset (gh-693)"""
    fname = run_tmpfile("yy = zz\n")
    _ip.run_cell("zz = 23")
    try:
        _ip.run_line_magic("run", "-i %s" % fname)
        assert _ip.user_ns["yy"] == 23
    finally:
        _ip.run_line_magic("reset", "-f")

    _ip.run_cell("zz = 23")
    try:
        _ip.run_line_magic("run", "-i %s" % fname)
        assert _ip.user_ns["yy"] == 23
    finally:
        _ip.run_line_magic("reset", "-f")


def test_unicode():
    """Check that files in odd encodings are accepted."""
    mydir = os.path.dirname(__file__)
    na = os.path.join(mydir, "nonascii.py")
    _ip.run_line_magic("run", na)
    assert _ip.user_ns["u"] == "Ўт№Ф"


def test_run_py_file_attribute(run_tmpfile):
    """Test handling of `__file__` attribute in `%run <file>.py`."""
    fname = run_tmpfile("t = __file__\n")
    _missing = object()
    file1 = _ip.user_ns.get("__file__", _missing)
    _ip.run_line_magic("run", fname)
    file2 = _ip.user_ns.get("__file__", _missing)
    assert _ip.user_ns["t"] == fname
    assert file1 == file2


def test_run_ipy_file_attribute(run_tmpfile):
    """Test handling of `__file__` attribute in `%run <file.ipy>`."""
    fname = run_tmpfile("t = __file__\n", ext=".ipy")
    _missing = object()
    file1 = _ip.user_ns.get("__file__", _missing)
    _ip.run_line_magic("run", fname)
    file2 = _ip.user_ns.get("__file__", _missing)
    assert _ip.user_ns["t"] == fname
    assert file1 == file2


def test_run_formatting(run_tmpfile):
    """Test that %run -t -N<N> does not raise a TypeError for N > 1."""
    fname = run_tmpfile("pass")
    _ip.run_line_magic("run", "-t -N 1 %s" % fname)
    _ip.run_line_magic("run", "-t -N 10 %s" % fname)


def test_ignore_sys_exit(run_tmpfile):
    """Test the -e option to ignore sys.exit()"""
    fname = run_tmpfile("import sys; sys.exit(1)")
    with tt.AssertPrints("SystemExit"):
        _ip.run_line_magic("run", fname)

    with tt.AssertNotPrints("SystemExit"):
        _ip.run_line_magic("run", "-e %s" % fname)


def test_run_nb(run_tmpfile):
    """Test %run notebook.ipynb"""
    pytest.importorskip("nbformat")
    from nbformat import v4, writes

    nb = v4.new_notebook(
        cells=[
            v4.new_markdown_cell("The Ultimate Question of Everything"),
            v4.new_code_cell("answer=42"),
        ]
    )
    fname = run_tmpfile(writes(nb, version=4), ext=".ipynb")
    _ip.run_line_magic("run", fname)
    assert _ip.user_ns["answer"] == 42


def test_run_nb_error(run_tmpfile):
    """Test %run notebook.ipynb error"""
    pytest.importorskip("nbformat")
    from nbformat import v4, writes

    pytest.raises(Exception, _ip.run_line_magic, "run")
    pytest.raises(Exception, _ip.run_line_magic, "run", "foobar.ipynb")

    nb = v4.new_notebook(cells=[v4.new_code_cell("0/0")])
    fname = run_tmpfile(writes(nb, version=4), ext=".ipynb")
    pytest.raises(Exception, _ip.run_line_magic, "run", fname)


def test_file_options(run_tmpfile):
    fname = run_tmpfile("import sys\n" 'a = " ".join(sys.argv[1:])\n')
    test_opts = "-x 3 --verbose"
    _ip.run_line_magic("run", "{0} {1}".format(fname, test_opts))
    assert _ip.user_ns["a"] == test_opts


def _fake_debugger(func):
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        with patch.object(debugger.Pdb, "run", staticmethod(eval)):
            return func(*args, **kwds)
    return wrapper


@pytest.fixture
def run_with_package(tmp_path, monkeypatch):
    package = "tmp{0}".format(
        "".join([random.choice(string.ascii_letters) for i in range(10)])
    )
    value = int(random.random() * 10000)

    monkeypatch.syspath_prepend(str(tmp_path))

    def writefile(name, content):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content), encoding="utf-8")

    writefile(os.path.join(package, "__init__.py"), "")
    writefile(os.path.join(package, "sub.py"), f"x = {value!r}\n")
    writefile(os.path.join(package, "relative.py"), "from .sub import x\n")
    writefile(os.path.join(package, "absolute.py"), f"from {package}.sub import x\n")
    writefile(os.path.join(package, "args.py"), 'import sys\na = " ".join(sys.argv[1:])\n')

    return package, value


def _check_run_submodule(package, value, submodule, opts=""):
    _ip.user_ns.pop("x", None)
    _ip.run_line_magic("run", f"{opts} -m {package}.{submodule}")
    assert _ip.user_ns["x"] == value, f"Variable `x` is not loaded from module `{submodule}`."


@pytest.mark.parametrize("submodule,opts", [
    ("absolute", ""),
    ("relative", ""),
    ("absolute", "-p"),
    ("relative", "-p"),
])
def test_run_submodule(run_with_package, submodule, opts):
    package, value = run_with_package
    _check_run_submodule(package, value, submodule, opts)


@pytest.mark.parametrize("submodule", ["absolute", "relative"])
@_fake_debugger
def test_debug_run_submodule(run_with_package, submodule):
    package, value = run_with_package
    _check_run_submodule(package, value, submodule, "-d")


def test_module_options(run_with_package):
    package, _ = run_with_package
    _ip.user_ns.pop("a", None)
    test_opts = "-x abc -m test"
    _ip.run_line_magic("run", f"-m {package}.args {test_opts}")
    assert _ip.user_ns["a"] == test_opts


def test_module_options_with_separator(run_with_package):
    package, _ = run_with_package
    _ip.user_ns.pop("a", None)
    test_opts = "-x abc -m test"
    _ip.run_line_magic("run", f"-m {package}.args -- {test_opts}")
    assert _ip.user_ns["a"] == test_opts


def test_run_quoted_glob_arg_is_not_expanded():
    """Quoted glob args to ``%run`` are passed through unexpanded (#12726)"""
    with TemporaryDirectory() as td:
        cwd = os.getcwd()
        try:
            os.chdir(td)
            # Files that *would* match the glob if expansion happened.
            for name in ("foo.txt", "bar.txt"):
                with open(name, "w", encoding="utf-8") as f:
                    f.write("")

            script = pjoin(td, "show_argv.py")
            with open(script, "w", encoding="utf-8") as f:
                f.write("import sys\nargs = sys.argv[1:]\n")

            # Sanity check: bare glob still expands as before.
            _ip.user_ns.pop("args", None)
            _ip.run_line_magic("run", '-i {} *.txt'.format(script))
            assert sorted(_ip.user_ns["args"]) == ["bar.txt", "foo.txt"]

            # Double-quoted glob should pass through literally on all platforms.
            _ip.user_ns.pop("args", None)
            _ip.run_line_magic("run", '-i {} "*.txt"'.format(script))
            assert _ip.user_ns["args"] == ["*.txt"]

            # Single-quoted glob — POSIX only. On windows single quotes aren't
            # stripped by the splitter (see %run docstring), so skip.
            if os.name == "posix":
                _ip.user_ns.pop("args", None)
                _ip.run_line_magic("run", "-i {} '*.txt'".format(script))
                assert _ip.user_ns["args"] == ["*.txt"]
        finally:
            os.chdir(cwd)
            _ip.run_line_magic("reset", "-f")


def test_run__name__():
    with TemporaryDirectory() as td:
        path = pjoin(td, "foo.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write("q = __name__")

        _ip.user_ns.pop("q", None)
        _ip.run_line_magic("run", "{}".format(path))
        assert _ip.user_ns.pop("q") == "__main__"

        _ip.run_line_magic("run", "-n {}".format(path))
        assert _ip.user_ns.pop("q") == "foo"

        try:
            _ip.run_line_magic("run", "-i -n {}".format(path))
            assert _ip.user_ns.pop("q") == "foo"
        finally:
            _ip.run_line_magic("reset", "-f")


def test_run_tb():
    """Test traceback offset in %run"""
    with TemporaryDirectory() as td:
        path = pjoin(td, "foo.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                "\n".join(
                    [
                        "def foo():",
                        "    return bar()",
                        "def bar():",
                        "    raise RuntimeError('hello!')",
                        "foo()",
                    ]
                )
            )
        with capture_output() as io:
            _ip.run_line_magic("run", "{}".format(path))
        out = io.stdout
        assert "execfile" not in out
        assert "RuntimeError" in out
        assert out.count("---->") == 3
        del ip.user_ns["bar"]
        del ip.user_ns["foo"]


def test_multiprocessing_run():
    """Set we can run mutiprocesgin without messing up up main namespace

    Note that import `nose.tools as nt` modify the values
    sys.module['__mp_main__'] so we need to temporarily set it to None to test
    the issue.
    """
    with TemporaryDirectory() as td:
        mpm = sys.modules.get("__mp_main__")
        sys.modules["__mp_main__"] = None
        try:
            path = pjoin(td, "test.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write("import multiprocessing\nprint('hoy')")
            with capture_output() as io:
                _ip.run_line_magic("run", path)
                _ip.run_cell("i_m_undefined")
            out = io.stdout
            assert "hoy" in out
            assert "AttributeError" not in out
            assert "NameError" in out
            assert out.count("---->") == 1
        except:
            raise
        finally:
            sys.modules["__mp_main__"] = mpm


def test_script_tb():
    """Test traceback offset in `ipython script.py`"""
    with TemporaryDirectory() as td:
        path = pjoin(td, "foo.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                "\n".join(
                    [
                        "def foo():",
                        "    return bar()",
                        "def bar():",
                        "    raise RuntimeError('hello!')",
                        "foo()",
                    ]
                )
            )
        out, err = tt.ipexec(path)
        assert "execfile" not in out
        assert "RuntimeError" in out
        assert out.count("---->") == 3

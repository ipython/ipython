# encoding: utf-8
"""Tests for IPython.core.ultratb"""
import functools
import io
import os.path
import platform
import re
import sys
import traceback
from textwrap import dedent

import pytest

from tempfile import TemporaryDirectory

from IPython.core.ultratb import VerboseTB, FormattedTB
from IPython.testing import tools as tt
from IPython.testing.decorators import onlyif_unicode_paths, skip_without
from IPython.utils.syspathcontext import prepended_to_syspath

file_1 = """1
2
3
def f():
  1/0
"""

file_2 = """def f():
  1/0
"""


def recursionlimit(frames):
    """
    decorator to set the recursion limit temporarily
    """

    def inner(test_function):
        @functools.wraps(test_function)
        def wrapper(*args, **kwargs):
            rl = sys.getrecursionlimit()
            sys.setrecursionlimit(frames)
            try:
                return test_function(*args, **kwargs)
            finally:
                sys.setrecursionlimit(rl)

        return wrapper

    return inner


def test_changing_py_file():
    """Traceback produced if the line where the error occurred is missing?

    https://github.com/ipython/ipython/issues/1456
    """
    with TemporaryDirectory() as td:
        fname = os.path.join(td, "foo_1456.py")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(file_1)

        with prepended_to_syspath(td):
            ip.run_cell("import foo_1456")

        with tt.AssertPrints("ZeroDivisionError"):
            ip.run_cell("foo_1456.f()")

        # Make the file shorter, so the line of the error is missing.
        with open(fname, "w", encoding="utf-8") as f:
            f.write(file_2)

        # For some reason, this was failing on the *second* call after
        # changing the file, so we call f() twice.
        with tt.AssertNotPrints("Internal Python error", channel="stderr"):
            with tt.AssertPrints("ZeroDivisionError"):
                ip.run_cell("foo_1456.f()")
            with tt.AssertPrints("ZeroDivisionError"):
                ip.run_cell("foo_1456.f()")


iso_8859_5_file = '''# coding: iso-8859-5

def fail():
    """дбИЖ"""
    1/0     # дбИЖ
'''


@onlyif_unicode_paths
def test_nonascii_path():
    with TemporaryDirectory(suffix="é") as td:
        fname = os.path.join(td, "fooé.py")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(file_1)

        with prepended_to_syspath(td):
            ip.run_cell("import fooé")

        with tt.AssertPrints("ZeroDivisionError"):
            ip.run_cell("fooé.f()")


def test_iso8859_5():
    with TemporaryDirectory() as td:
        fname = os.path.join(td, "dfghjkl.py")

        with io.open(fname, "w", encoding="iso-8859-5") as f:
            f.write(iso_8859_5_file)

        with prepended_to_syspath(td):
            ip.run_cell("from dfghjkl import fail")

        with tt.AssertPrints("ZeroDivisionError"):
            with tt.AssertPrints("дбИЖ", suppress=False):
                ip.run_cell("fail()")


def test_nonascii_msg():
    cell = "raise Exception('é')"
    expected = "Exception('é')"
    ip.run_cell("%xmode plain")
    with tt.AssertPrints(expected):
        ip.run_cell(cell)

    ip.run_cell("%xmode verbose")
    with tt.AssertPrints(expected):
        ip.run_cell(cell)

    ip.run_cell("%xmode context")
    with tt.AssertPrints(expected):
        ip.run_cell(cell)

    ip.run_cell("%xmode minimal")
    with tt.AssertPrints("Exception: é"):
        ip.run_cell(cell)

    ip.run_cell("%xmode context")


def test_nested_genexpr():
    """Regression test for gh-8293 and gh-8205."""
    code = dedent(
        """\
        class SpecificException(Exception):
            pass

        def foo_8293(x):
            raise SpecificException("Success!")

        sum(sum(foo_8293(x) for _ in [0]) for x in [0])
        """
    )
    with tt.AssertPrints("SpecificException: Success!", suppress=False):
        ip.run_cell(code)


indentationerror_file = """if True:
zoom()
"""


def test_indentationerror_shows_line():
    # See issue gh-2398
    with tt.AssertPrints("IndentationError"):
        with tt.AssertPrints("zoom()", suppress=False):
            ip.run_cell(indentationerror_file)

    with TemporaryDirectory() as td:
        fname = os.path.join(td, "foo_2398.py")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(indentationerror_file)

        with tt.AssertPrints("IndentationError"):
            with tt.AssertPrints("zoom()", suppress=False):
                ip.run_line_magic("run", fname)


@skip_without("pandas")
def test_dynamic_code():
    code = """
    import pandas
    df = pandas.DataFrame([])

    # Important: only fails inside of an "exec" call:
    exec("df.foobarbaz()")
    """

    with tt.AssertPrints("Could not get source"):
        ip.run_cell(code)


se_file_1 = """1
2
7/
"""

se_file_2 = """7/
"""


def test_syntaxerror_no_stacktrace_at_compile_time():
    syntax_error_at_compile_time = """
def foo_syntax_error_test():
    ..
"""
    with tt.AssertPrints("SyntaxError"):
        ip.run_cell(syntax_error_at_compile_time)

    with tt.AssertNotPrints("foo_syntax_error_test()"):
        ip.run_cell(syntax_error_at_compile_time)


def test_syntaxerror_stacktrace_when_running_compiled_code():
    syntax_error_at_runtime = """
def foo_syntax_error_test_2():
    eval("..")

def bar_syntax_error_test_2():
    foo_syntax_error_test_2()

bar_syntax_error_test_2()
"""
    with tt.AssertPrints("SyntaxError"):
        ip.run_cell(syntax_error_at_runtime)
    with tt.AssertPrints(
        ["foo_syntax_error_test_2()", "bar_syntax_error_test_2()"]
    ):
        ip.run_cell(syntax_error_at_runtime)
    del ip.user_ns["bar_syntax_error_test_2"]
    del ip.user_ns["foo_syntax_error_test_2"]


def test_syntax_error_changing_py_file():
    with TemporaryDirectory() as td:
        fname = os.path.join(td, "foo_test_changing_py_file.py")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(se_file_1)

        with tt.AssertPrints(["7/", "SyntaxError"]):
            ip.run_line_magic("run", fname)

        with open(fname, "w", encoding="utf-8") as f:
            f.write(se_file_2)

        with tt.AssertPrints(["7/", "SyntaxError"]):
            ip.run_line_magic("run", fname)


def test_non_syntaxerror():
    # SyntaxTB may be called with an error other than a SyntaxError (gh-4361)
    try:
        raise ValueError("QWERTY")
    except ValueError:
        with tt.AssertPrints("QWERTY"):
            ip.showsyntaxerror()


@pytest.mark.skipif(
    platform.python_implementation() == "PyPy",
    reason="New 3.9 Pgen Parser does not raise Memory error, except on failed malloc.",
)
def test_memoryerror():
    memoryerror_code = "(" * 200 + ")" * 200
    ip.run_cell(memoryerror_code)


_DIRECT_CAUSE_ERROR_CODE = """
try:
    x = 1 + 2
    print(not_defined_here)
except Exception as e:
    x += 55
    x - 1
    y = {}
    raise KeyError('uh') from e
    """

_EXCEPTION_DURING_HANDLING_CODE = """
try:
    x = 1 + 2
    print(not_defined_here)
except Exception as e:
    x += 55
    x - 1
    y = {}
    raise KeyError('uh')
    """

_SUPPRESS_CHAINING_CODE = """
try:
    1/0
except Exception:
    raise ValueError("Yikes") from None
    """

_SYS_EXIT_WITH_CONTEXT_CODE = """
try:
    1/0
except Exception as e:
    raise SystemExit(1)
    """


def test_direct_cause_error():
    with tt.AssertPrints(["KeyError", "NameError", "direct cause"]):
        ip.run_cell(_DIRECT_CAUSE_ERROR_CODE)


def test_exception_during_handling_error():
    with tt.AssertPrints(["KeyError", "NameError", "During handling"]):
        ip.run_cell(_EXCEPTION_DURING_HANDLING_CODE)


def test_sysexit_while_handling_error():
    with tt.AssertPrints(["SystemExit", "to see the full traceback"]):
        with tt.AssertNotPrints(["another exception"], suppress=False):
            ip.run_cell(_SYS_EXIT_WITH_CONTEXT_CODE)


def test_suppress_exception_chaining():
    with (
        tt.AssertNotPrints("ZeroDivisionError"),
        tt.AssertPrints("ValueError", suppress=False),
    ):
        ip.run_cell(_SUPPRESS_CHAINING_CODE)


def test_plain_direct_cause_error():
    with tt.AssertPrints(["KeyError", "NameError", "direct cause"]):
        ip.run_cell("%xmode Plain")
        ip.run_cell(_DIRECT_CAUSE_ERROR_CODE)
        ip.run_cell("%xmode Verbose")


def test_plain_exception_during_handling_error():
    with tt.AssertPrints(["KeyError", "NameError", "During handling"]):
        ip.run_cell("%xmode Plain")
        ip.run_cell(_EXCEPTION_DURING_HANDLING_CODE)
        ip.run_cell("%xmode Verbose")


def test_plain_suppress_exception_chaining():
    with (
        tt.AssertNotPrints("ZeroDivisionError"),
        tt.AssertPrints("ValueError", suppress=False),
    ):
        ip.run_cell("%xmode Plain")
        ip.run_cell(_SUPPRESS_CHAINING_CODE)
        ip.run_cell("%xmode Verbose")


_RECURSION_DEFINITIONS = """
def non_recurs():
    1/0

def r1():
    r1()

def r3a():
    r3b()

def r3b():
    r3c()

def r3c():
    r3a()

def r3o1():
    r3a()

def r3o2():
    r3o1()
"""


@pytest.fixture
def recursion_setup():
    ip.run_cell(_RECURSION_DEFINITIONS)


def test_no_recursion(recursion_setup):
    with tt.AssertNotPrints("skipping similar frames"):
        ip.run_cell("non_recurs()")


@recursionlimit(200)
def test_recursion_one_frame(recursion_setup):
    with tt.AssertPrints(
        re.compile(
            r"\[\.\.\. skipping similar frames: r1 at line 5 \(\d{2,3} times\)\]"
        )
    ):
        ip.run_cell("r1()")


@recursionlimit(160)
def test_recursion_three_frames(recursion_setup):
    with (
        tt.AssertPrints("[... skipping similar frames: "),
        tt.AssertPrints(
            re.compile(r"r3a at line 8 \(\d{2} times\)"), suppress=False
        ),
        tt.AssertPrints(
            re.compile(r"r3b at line 11 \(\d{2} times\)"), suppress=False
        ),
        tt.AssertPrints(
            re.compile(r"r3c at line 14 \(\d{2} times\)"), suppress=False
        ),
    ):
        ip.run_cell("r3o2()")


_ERROR_WITH_NOTE = """
try:
    raise AssertionError("Message")
except Exception as e:
    try:
        e.add_note("This is a PEP-678 note.")
    except AttributeError:  # Python <= 3.10
        e.__notes__ = ("This is a PEP-678 note.",)
    raise
    """


def test_verbose_reports_notes():
    with tt.AssertPrints(["AssertionError", "Message", "This is a PEP-678 note."]):
        ip.run_cell(_ERROR_WITH_NOTE)


def test_plain_reports_notes():
    with tt.AssertPrints(["AssertionError", "Message", "This is a PEP-678 note."]):
        ip.run_cell("%xmode Plain")
        ip.run_cell(_ERROR_WITH_NOTE)
        ip.run_cell("%xmode Verbose")


def test_jsondecodeerror_message():
    """Test that exception string repr is preferred over .msg for non-SyntaxError in %xmode plain."""
    cell = "import json;json.loads('{\"a\": }')"
    if platform.python_implementation() == "PyPy":
        expected = "JSONDecodeError: Unexpected '}': line 1 column 7 (char 6)"
    else:
        expected = "JSONDecodeError: Expecting value: line 1 column 7 (char 6)"
    ip.run_cell("%xmode plain")
    with tt.AssertPrints(expected):
        ip.run_cell(cell)
    ip.run_cell("%xmode context")


# ----------------------------------------------------------------------------


# module testing (minimal)
def test_handlers():
    def spam(c, d_e):
        (d, e) = d_e
        x = c + d
        y = c * d
        foo(x, y)

    def foo(a, b, bar=1):
        eggs(a, b + bar)

    def eggs(f, g, z=globals()):
        h = f + g
        i = f - g
        return h / i

    buff = io.StringIO()

    buff.write("")
    buff.write("*** Before ***")
    try:
        buff.write(spam(1, (2, 3)))
    except:
        traceback.print_exc(file=buff)

    handler = FormattedTB(ostream=buff)
    buff.write("*** FormattedTB ***")
    try:
        buff.write(spam(1, (2, 3)))
    except:
        handler(*sys.exc_info())
    buff.write("")

    handler = VerboseTB(ostream=buff)
    buff.write("*** VerboseTB ***")
    try:
        buff.write(spam(1, (2, 3)))
    except:
        handler(*sys.exc_info())
    buff.write("")


def testSyntaxError():
    cell = "raise SyntaxError()"
    expected = "SyntaxError\n"
    with tt.AssertPrints(expected):
        ip.run_cell(cell)

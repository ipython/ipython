"""Tests for debugging machinery."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import builtins
import io
import os
import re as re_module
import sys
import platform
from pathlib import Path

from tempfile import NamedTemporaryFile, TemporaryDirectory
from textwrap import dedent
from unittest.mock import patch

from IPython.core import debugger
from IPython.testing import IPYTHON_TESTING_TIMEOUT_SCALE
from IPython.testing.decorators import skip_win32
from IPython.utils import PyColorize
import pytest

# Helper for executing files with proper debugger frame marking
def execfile(fname, glob, loc=None, compiler=None):
    __tracebackhide__ = "__ipython_bottom__"
    loc = loc if (loc is not None) else glob
    with open(fname, "rb") as f:
        compiler_fn = compiler or compile
        exec(compiler_fn(f.read(), fname, "exec"), glob, loc)


# Helper classes, from CPython's Pdb test suite
#


class _FakeInput(object):
    """
    A fake input stream for pdb's interactive debugger.  Whenever a
    line is read, print it (to simulate the user typing it), and then
    return it.  The set of lines to return is specified in the
    constructor; they should not have trailing newlines.
    """

    def __init__(self, lines):
        self.lines = iter(lines)

    def readline(self):
        line = next(self.lines)
        print(line)
        return line + "\n"


class PdbTestInput(object):
    """Context manager that makes testing Pdb in doctests easier."""

    def __init__(self, input):
        self.input = input

    def __enter__(self):
        self.real_stdin = sys.stdin
        sys.stdin = _FakeInput(self.input)

    def __exit__(self, *exc):
        sys.stdin = self.real_stdin


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_ipdb_magics():
    '''Test calling some IPython magics from ipdb.

    First, set up some test functions and classes which we can inspect.

    In [1]: class ExampleClass(object):
       ...:    """Docstring for ExampleClass."""
       ...:    def __init__(self):
       ...:        """Docstring for ExampleClass.__init__"""
       ...:        pass
       ...:    def __str__(self):
       ...:        return "ExampleClass()"

    In [2]: def example_function(x, y, z="hello"):
       ...:     """Docstring for example_function."""
       ...:     pass

    In [3]: old_trace = sys.gettrace()

    Create a function which triggers ipdb.

    In [4]: def trigger_ipdb():
       ...:    a = ExampleClass()
       ...:    debugger.Pdb().set_trace()

    Run ipdb with faked input & check output. Because of a difference between
    Python 3.13 & older versions, the first bit of the output is inconsistent.
    We need to use ... to accommodate that, so the examples have to use IPython
    prompts so that ... is distinct from the Python PS2 prompt.

    In [5]: with PdbTestInput([
       ...:    'pdef example_function',
       ...:    'pdoc ExampleClass',
       ...:    'up',
       ...:    'down',
       ...:    'list',
       ...:    'pinfo a',
       ...:    'll',
       ...:    'continue',
       ...: ]):
       ...:     trigger_ipdb()
    ...> <doctest ...>(3)trigger_ipdb()
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> pdef example_function
     example_function(x, y, z='hello')
     ipdb> pdoc ExampleClass
    Class docstring:
        Docstring for ExampleClass.
    Init docstring:
        Docstring for ExampleClass.__init__
    ipdb> up
    > <doctest ...>(11)<module>()
          7    'pinfo a',
          8    'll',
          9    'continue',
         10 ]):
    ---> 11     trigger_ipdb()
    <BLANKLINE>
    ipdb> down...
    > <doctest ...>(3)trigger_ipdb()
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> list
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> pinfo a
    Type:           ExampleClass
    String form:    ExampleClass()
    Namespace:      Local...
    Docstring:      Docstring for ExampleClass.
    Init docstring: Docstring for ExampleClass.__init__
    ipdb> ll
          1 def trigger_ipdb():
          2    a = ExampleClass()
    ----> 3    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> continue

    Restore previous trace function, e.g. for coverage.py

    In [6]: sys.settrace(old_trace)
    '''


def test_ipdb_closure():
    """Test evaluation of expressions which depend on closure.

    In [1]: old_trace = sys.gettrace()

    Create a function which triggers ipdb.

    In [2]: def trigger_ipdb():
       ...:    debugger.Pdb().set_trace()

    In [3]: with PdbTestInput([
       ...:    'x = 1; sum(x * i for i in range(5))',
       ...:    'continue',
       ...: ]):
       ...:     trigger_ipdb()
    ...> <doctest ...>(2)trigger_ipdb()
          1 def trigger_ipdb():
    ----> 2    debugger.Pdb().set_trace()
    <BLANKLINE>
    ipdb> x = 1; sum(x * i for i in range(5))
    ipdb> continue

    Restore previous trace function, e.g. for coverage.py

    In [4]: sys.settrace(old_trace)
    """


def test_ipdb_magics2():
    """Test ipdb with a very short function.

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    Run ipdb.

    >>> with PdbTestInput([
    ...    'continue',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
          1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> continue

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    """


def can_quit():
    """Test that quit work in ipydb

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    >>> with PdbTestInput([
    ...    'quit',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
            1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> quit

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    """


def can_exit():
    """Test that quit work in ipydb

    >>> old_trace = sys.gettrace()

    >>> def bar():
    ...     pass

    >>> with PdbTestInput([
    ...    'exit',
    ... ]):
    ...     debugger.Pdb().runcall(bar)
    > <doctest ...>(2)bar()
            1 def bar():
    ----> 2    pass
    <BLANKLINE>
    ipdb> exit

    Restore previous trace function, e.g. for coverage.py

    >>> sys.settrace(old_trace)
    """


def test_interruptible_core_debugger():
    """The debugger can be interrupted.

    The presumption is there is some mechanism that causes a KeyboardInterrupt
    (this is implemented in ipykernel).  We want to ensure the
    KeyboardInterrupt cause debugging to cease.
    """

    def raising_input(msg="", called=[0]):
        called[0] += 1
        assert called[0] == 1, "input() should only be called once!"
        raise KeyboardInterrupt()

    tracer_orig = sys.gettrace()
    try:
        with patch.object(builtins, "input", raising_input):
            debugger.InterruptiblePdb().set_trace()
            # The way this test will fail is by set_trace() never exiting,
            # resulting in a timeout by the test runner. The alternative
            # implementation would involve a subprocess, but that adds issues
            # with interrupting subprocesses that are rather complex, so it's
            # simpler just to do it this way.
    finally:
        # restore the original trace function
        sys.settrace(tracer_orig)


@pytest.mark.skipif(
    not debugger.CHAIN_EXCEPTIONS,
    reason="chained exception navigation is not available",
)
def test_exception_command_aliases_exceptions():
    ipdb = debugger.Pdb()

    with patch.object(ipdb, "do_exceptions", return_value=True) as do_exceptions:
        assert ipdb.onecmd("exception 0") is True

    do_exceptions.assert_called_once_with("0")


def test_execfile_marks_debugger_internal_frames_hidden():
    with TemporaryDirectory() as td:
        script = Path(td) / "fails.py"
        script.write_text(
            "def user_frame():\n"
            "    raise RuntimeError('boom')\n"
            "user_frame()\n",
            encoding="utf-8",
        )

        with pytest.raises(RuntimeError) as exc_info:
            execfile(script, {})

    ipdb = debugger.Pdb()
    stack, _ = ipdb.get_stack(None, exc_info.value.__traceback__)
    hidden_frames = ipdb.hidden_frames(stack)
    frame_names = [frame.f_code.co_name for frame, _ in stack]
    execfile_index = frame_names.index("execfile")

    assert (
        stack[execfile_index][0].f_locals["__tracebackhide__"]
        == "__ipython_bottom__"
    )
    assert hidden_frames[execfile_index] is True
    assert all(hidden_frames[:execfile_index])
    assert hidden_frames[execfile_index + 1 :] == [False, False]


@skip_win32
def test_xmode_skip():
    """that xmode skip frames

    Not as a doctest as pytest does not run doctests.
    """
    import pexpect

    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"

    child = pexpect.spawn(
        sys.executable, ["-m", "IPython", "--colors=nocolor"], env=env
    )
    child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE

    child.expect("IPython")
    child.expect("\n")
    child.expect_exact("In [1]")

    block = dedent(
        """
    def f():
        __tracebackhide__ = True
        g()

    def g():
        raise ValueError

    f()
    """
    )

    for line in block.splitlines():
        child.sendline(line)
        child.expect_exact(line)
    child.expect_exact("skipping")

    block = dedent(
        """
    def f():
        __tracebackhide__ = True
        g()

    def g():
        from IPython.core.debugger import set_trace
        set_trace()

    f()
    """
    )

    for line in block.splitlines():
        child.sendline(line)
        child.expect_exact(line)

    child.expect("ipdb>")
    child.sendline("w")
    child.expect("hidden")
    child.expect("ipdb>")
    child.sendline("skip_hidden false")
    child.sendline("w")
    child.expect("__traceba")
    child.expect("ipdb>")

    child.close()


skip_decorators_blocks = (
    """
    def helpers_helper():
        pass # should not stop here except breakpoint
    """,
    """
    def helper_1():
        helpers_helper() # should not stop here
    """,
    """
    def helper_2():
        pass # should not stop here
    """,
    """
    def pdb_skipped_decorator2(function):
        def wrapped_fn(*args, **kwargs):
            __debuggerskip__ = True
            helper_2()
            __debuggerskip__ = False
            result = function(*args, **kwargs)
            __debuggerskip__ = True
            helper_2()
            return result
        return wrapped_fn
    """,
    """
    def pdb_skipped_decorator(function):
        def wrapped_fn(*args, **kwargs):
            __debuggerskip__ = True
            helper_1()
            __debuggerskip__ = False
            result = function(*args, **kwargs)
            __debuggerskip__ = True
            helper_2()
            return result
        return wrapped_fn
    """,
    """
    @pdb_skipped_decorator
    @pdb_skipped_decorator2
    def bar(x, y):
        return x * y
    """,
    """import IPython.terminal.debugger as ipdb""",
    """
    def f():
        ipdb.set_trace()
        bar(3, 4)
    """,
    """
    f()
    """,
)


def _decorator_skip_setup():
    import pexpect

    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"
    env["PROMPT_TOOLKIT_NO_CPR"] = "1"

    child = pexpect.spawn(
        sys.executable, ["-m", "IPython", "--colors=nocolor"], env=env
    )
    child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE

    child.expect("IPython")
    child.expect("\n")

    child.timeout = 5 * IPYTHON_TESTING_TIMEOUT_SCALE
    child.str_last_chars = 500

    dedented_blocks = [dedent(b).strip() for b in skip_decorators_blocks]
    in_prompt_number = 1
    for cblock in dedented_blocks:
        child.expect_exact(f"In [{in_prompt_number}]:")
        in_prompt_number += 1
        for line in cblock.splitlines():
            child.sendline(line)
            child.expect_exact(line)
        child.sendline("")
    return child


@pytest.mark.skip(reason="recently fail for unknown reason on CI")
@skip_win32
def test_decorator_skip():
    """test that decorator frames can be skipped."""

    child = _decorator_skip_setup()

    child.expect_exact("ipython-input-8")
    child.expect_exact("3     bar(3, 4)")
    child.expect("ipdb>")

    child.expect("ipdb>")
    child.sendline("step")
    child.expect_exact("step")
    child.expect_exact("--Call--")
    child.expect_exact("ipython-input-6")

    child.expect_exact("1 @pdb_skipped_decorator")

    child.sendline("s")
    child.expect_exact("return x * y")

    child.close()


@pytest.mark.skip(reason="recently fail for unknown reason on CI")
@pytest.mark.skipif(platform.python_implementation() == "PyPy", reason="issues on PyPy")
@skip_win32
def test_decorator_skip_disabled():
    """test that decorator frame skipping can be disabled"""

    child = _decorator_skip_setup()

    child.expect_exact("3     bar(3, 4)")

    for input_, expected in [
        ("skip_predicates debuggerskip False", ""),
        ("skip_predicates", "debuggerskip : False"),
        ("step", "---> 2     def wrapped_fn"),
        ("step", "----> 3         __debuggerskip__"),
        ("step", "----> 4         helper_1()"),
        ("step", "---> 1 def helper_1():"),
        ("next", "----> 2     helpers_helper()"),
        ("next", "--Return--"),
        ("next", "----> 5         __debuggerskip__ = False"),
    ]:
        child.expect("ipdb>")
        child.sendline(input_)
        child.expect_exact(input_)
        child.expect_exact(expected)

    child.close()


@pytest.mark.skip(reason="recently fail for unknown reason on CI")
@pytest.mark.skipif(platform.python_implementation() == "PyPy", reason="issues on PyPy")
@skip_win32
def test_decorator_skip_with_breakpoint():
    """test that decorator frame skipping can be disabled"""

    import pexpect

    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"
    env["PROMPT_TOOLKIT_NO_CPR"] = "1"

    child = pexpect.spawn(
        sys.executable, ["-m", "IPython", "--colors=nocolor"], env=env
    )
    child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
    child.str_last_chars = 500

    child.expect("IPython")
    child.expect("\n")

    child.timeout = 5 * IPYTHON_TESTING_TIMEOUT_SCALE

    ### we need a filename, so we need to exec the full block with a filename
    with NamedTemporaryFile(suffix=".py", dir=".", delete=True) as tf:
        name = tf.name[:-3].split("/")[-1]
        tf.write("\n".join([dedent(x) for x in skip_decorators_blocks[:-1]]).encode())
        tf.flush()
        codeblock = f"from {name} import f"

        dedented_blocks = [
            codeblock,
            "f()",
        ]

        in_prompt_number = 1
        for cblock in dedented_blocks:
            child.expect_exact(f"In [{in_prompt_number}]:")
            in_prompt_number += 1
            for line in cblock.splitlines():
                child.sendline(line)
                child.expect_exact(line)
            child.sendline("")

        # From 3.13, set_trace()/breakpoint() stop on the line where they're
        # called, instead of the next line.
        if sys.version_info >= (3, 14):
            child.expect_exact("     46     ipdb.set_trace()")
            extra_step = [("step", "--> 47     bar(3, 4)")]
        elif sys.version_info >= (3, 13):
            child.expect_exact("--> 46     ipdb.set_trace()")
            extra_step = [("step", "--> 47     bar(3, 4)")]
        else:
            child.expect_exact("--> 47     bar(3, 4)")
            extra_step = []

        for input_, expected in (
            [
                (f"b {name}.py:3", ""),
            ]
            + extra_step
            + [
                ("step", "1---> 3     pass # should not stop here except"),
                ("step", "---> 38 @pdb_skipped_decorator"),
                ("continue", ""),
            ]
        ):
            child.expect("ipdb>")
            child.sendline(input_)
            child.expect_exact(input_)
            child.expect_exact(expected)

    child.close()


@skip_win32
def test_where_erase_value():
    """Test that `where` does not access f_locals and erase values."""
    import pexpect

    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"

    child = pexpect.spawn(
        sys.executable, ["-m", "IPython", "--colors=nocolor"], env=env
    )
    child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE

    child.expect("IPython")
    child.expect("\n")
    child.expect_exact("In [1]")

    block = dedent(
        """
    def simple_f():
         myvar = 1
         print(myvar)
         1/0
         print(myvar)
    simple_f()    """
    )

    for line in block.splitlines():
        child.sendline(line)
        child.expect_exact(line)
    child.expect_exact("ZeroDivisionError")
    child.expect_exact("In [2]:")

    child.sendline("%debug")

    ##
    child.expect("ipdb>")

    child.sendline("myvar")
    child.expect("1")

    ##
    child.expect("ipdb>")

    child.sendline("myvar = 2")

    ##
    child.expect_exact("ipdb>")

    child.sendline("myvar")

    child.expect_exact("2")

    ##
    child.expect("ipdb>")
    child.sendline("where")

    ##
    child.expect("ipdb>")
    child.sendline("myvar")

    child.expect_exact("2")
    child.expect("ipdb>")

    child.close()


@skip_win32
def test_ignore_module_basic_functionality():
    """Test basic ignore/unignore functionality and error handling."""
    import pexpect

    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"

    with TemporaryDirectory() as temp_dir:
        main_path = create_test_modules(temp_dir)

        child = pexpect.spawn(sys.executable, [main_path], env=env, cwd=temp_dir)
        child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
        child.expect("ipdb>")

        # Test listing modules when none are ignored
        child.sendline("ignore_module")
        child.expect_exact("No modules are currently ignored.")
        child.expect("ipdb>")

        # Test ignoring a module
        child.sendline("ignore_module level2_module")
        child.expect("ipdb>")

        # Test listing ignored modules
        child.sendline("ignore_module")
        child.expect_exact("Currently ignored modules: ['level2_module']")
        child.expect("ipdb>")

        # Test wildcard pattern
        child.sendline("ignore_module testpkg.*")
        child.expect("ipdb>")

        child.sendline("ignore_module")
        child.expect_exact("Currently ignored modules: ['level2_module', 'testpkg.*']")
        child.expect("ipdb>")

        # Test error handling - removing non-existent module
        child.sendline("unignore_module nonexistent")
        child.expect_exact("Module nonexistent is not currently ignored")
        child.expect("ipdb>")

        # Test successful removal
        child.sendline("unignore_module level2_module")
        child.expect("ipdb>")

        child.sendline("ignore_module")
        child.expect_exact("Currently ignored modules: ['testpkg.*']")
        child.expect("ipdb>")

        # Test removing already removed module
        child.sendline("unignore_module level2_module")
        child.expect_exact("Module level2_module is not currently ignored")
        child.expect("ipdb>")

        # Remove wildcard pattern
        child.sendline("unignore_module testpkg.*")
        child.expect("ipdb>")

        child.sendline("ignore_module")
        child.expect_exact("No modules are currently ignored.")
        child.expect("ipdb>")

        child.sendline("continue")
        child.close()


# Helper function for creating temporary modules
def create_test_modules(temp_dir):
    """Create a comprehensive module hierarchy for testing all debugger commands."""

    temp_path = Path(temp_dir)

    # Create package structure for wildcard testing
    package_dir = temp_path / "testpkg"
    package_dir.mkdir()

    # Package __init__.py
    (package_dir / "__init__.py").write_text("# Test package")

    # testpkg/submod1.py
    (package_dir / "submod1.py").write_text(
        dedent(
            """
        def submod1_func():
            x = 1
            y = 2
            return x + y
        """
        )
    )

    # testpkg/submod2.py
    (package_dir / "submod2.py").write_text(
        dedent(
            """
        def submod2_func():
            z = 10
            return z * 2
        """
        )
    )

    # Level 1 (top level module)
    (temp_path / "level1_module.py").write_text(
        dedent(
            """
        from level2_module import level2_func

        def level1_func():
            return level2_func()
        """
        )
    )

    # Level 2 (middle level module)
    (temp_path / "level2_module.py").write_text(
        dedent(
            """
        from level3_module import level3_func
        from testpkg.submod1 import submod1_func
        from testpkg.submod2 import submod2_func

        def level2_func():
            # Call package functions for step/next testing
            result1 = submod1_func()
            result2 = submod2_func()
            return level3_func() + result1 + result2
        """
        )
    )

    # Level 3 (bottom level with debugger)
    (temp_path / "level3_module.py").write_text(
        dedent(
            """
        from level4_module import level4_func

        from IPython.core.debugger import set_trace

        def level3_func():
            set_trace()
            pass
            result = level4_func()
            return result
        """
        )
    )

    # Level 4 (bottom level with debugger)
    (temp_path / "level4_module.py").write_text(
        dedent(
            """
        def level4_func():
            a = 70
            b = 30
            return a + b
        """
        )
    )

    # Main runner
    main_path = temp_path / "main_runner.py"
    main_path.write_text(
        dedent(
            """
        import sys
        sys.path.insert(0, '.')
        from level1_module import level1_func

        if __name__ == "__main__":
            result = level1_func()
            print(f"Final result: {result}")
        """
        )
    )

    return str(main_path)


@skip_win32
def test_ignore_module_all_commands():
    """Comprehensive test for all debugger commands (up/down/step/next) with ignore functionality."""
    import pexpect

    env = os.environ.copy()
    env["IPY_TEST_SIMPLE_PROMPT"] = "1"

    with TemporaryDirectory() as temp_dir:
        main_path = create_test_modules(temp_dir)

        # Test UP and DOWN commands
        child = pexpect.spawn(sys.executable, [main_path], env=env, cwd=temp_dir)
        child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
        child.expect("ipdb>")

        # Test up without ignores (baseline)
        child.sendline("up")
        child.expect("ipdb>")
        child.sendline("__name__")
        child.expect_exact("level2_module")
        child.expect("ipdb>")

        # Reset position
        child.sendline("down")
        child.expect("ipdb>")

        # Test up with single module ignore
        child.sendline("ignore_module level2_module")
        child.expect("ipdb>")
        child.sendline("up")
        child.expect_exact(
            "[... skipped 1 frame(s): 0 hidden frames + 1 ignored modules]"
        )
        child.expect("ipdb>")
        child.sendline("__name__")
        child.expect_exact("level1_module")
        child.expect("ipdb>")

        # Test up with wildcard ignore
        child.sendline("down")
        child.expect_exact(
            "[... skipped 1 frame(s): 0 hidden frames + 1 ignored modules]"
        )
        child.expect("ipdb>")
        child.sendline("unignore_module level2_module")
        child.expect("ipdb>")
        child.sendline("ignore_module level*")
        child.expect("ipdb>")
        child.sendline("up")
        child.expect_exact(
            "[... skipped 2 frame(s): 0 hidden frames + 2 ignored modules]"
        )
        child.expect("ipdb>")
        child.sendline("__name__")
        child.expect_exact("__main__")
        child.expect("ipdb>")

        child.sendline("continue")
        child.close()

        # Test STEP command
        child = pexpect.spawn(sys.executable, [main_path], env=env, cwd=temp_dir)
        child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
        child.expect("ipdb>")

        # Test step without ignores (should step into module)
        child.sendline("until 9")
        child.expect("ipdb>")
        child.sendline("step")
        child.expect("ipdb>")
        child.sendline("__name__")
        child.expect_exact("level4_module")
        child.expect("ipdb>")

        child.sendline("continue")
        child.close()

        # Test step with single module ignore
        child = pexpect.spawn(sys.executable, [main_path], env=env, cwd=temp_dir)
        child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
        child.expect("ipdb>")

        child.sendline("ignore_module level4_module")
        child.expect("ipdb>")
        child.sendline("until 9")
        child.expect("ipdb>")
        child.sendline("step")
        child.expect_exact("[... skipped 1 ignored module(s)]")
        child.expect("ipdb>")
        child.sendline("__name__")
        child.expect_exact("level3_module")
        child.expect("ipdb>")

        child.sendline("continue")
        child.close()

        # Test NEXT command
        child = pexpect.spawn(sys.executable, [main_path], env=env, cwd=temp_dir)
        child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
        child.expect("ipdb>")

        # Test next without ignores
        child.sendline("until 9")
        child.expect("ipdb>")
        child.sendline("next")
        child.expect("ipdb>")
        child.sendline("__name__")
        child.expect_exact("level3_module")
        child.expect("ipdb>")

        child.sendline("continue")
        child.close()

        # Test next with module ignore
        child = pexpect.spawn(sys.executable, [main_path], env=env, cwd=temp_dir)
        child.timeout = 15 * IPYTHON_TESTING_TIMEOUT_SCALE
        child.expect("ipdb>")

        child.sendline("ignore_module level2_module")
        child.expect("ipdb>")
        child.sendline("return")
        child.expect("ipdb>")
        child.sendline("next")
        child.expect_exact("[... skipped 1 ignored module(s)]")
        child.expect("ipdb>")

        child.sendline("continue")
        child.close()


# -----------------------------------------------------------------------------
# Signature compatibility with stdlib's ``pdb.Pdb``
# -----------------------------------------------------------------------------

import inspect
import pdb as _stdlib_pdb

from IPython.terminal.debugger import TerminalPdb

_PDB_SUBCLASSES = [debugger.Pdb, debugger.InterruptiblePdb, TerminalPdb]

# TerminalPdb instantiates a prompt_toolkit session, which needs a real
# console and cannot be created on Windows CI (NoConsoleScreenBufferError),
# so we skip instantiating it there.
_PDB_SUBCLASSES_INSTANTIABLE = [
    debugger.Pdb,
    debugger.InterruptiblePdb,
    pytest.param(TerminalPdb, marks=skip_win32),
]


@pytest.mark.parametrize(
    "cls", _PDB_SUBCLASSES, ids=lambda c: c.__name__
)
def test_pdb_subclass_signature_compatible(cls):
    """IPython debuggers derived from ``pdb.Pdb`` should be drop-in
    replacements, i.e. accept every keyword argument that the stdlib
    ``pdb.Pdb`` accepts (directly or via ``**kwargs``)."""
    assert issubclass(cls, _stdlib_pdb.Pdb)

    stdlib_params = inspect.signature(_stdlib_pdb.Pdb.__init__).parameters
    ip_params = inspect.signature(cls.__init__).parameters
    accepts_var_keyword = any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in ip_params.values()
    )

    for name, param in stdlib_params.items():
        if name == "self":
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        assert accepts_var_keyword or name in ip_params, (
            f"{cls.__name__} does not accept the {name!r} argument "
            "supported by stdlib pdb.Pdb"
        )


@pytest.mark.parametrize(
    "cls", _PDB_SUBCLASSES_INSTANTIABLE, ids=lambda c: c.__name__
)
@pytest.mark.parametrize("mode", [None, "inline", "cli"])
def test_pdb_subclass_accepts_mode(cls, mode):
    """The ``mode`` argument (added to ``pdb.Pdb`` in Python 3.14) should be
    accepted on every supported Python version and stored on the instance."""
    inst = cls(mode=mode)
    assert inst.mode == mode


# -----------------------------------------------------------------------------
# In-process Pdb tests.
#
# These drive the debugger post-mortem style: the Pdb instance is set up on a
# traceback and commands are dispatched with ``onecmd`` (or a full
# ``interaction`` with a fake stdin).  No trace function is installed for most
# tests, which keeps them fast and deterministic.  Sessions that end with
# quit/continue call ``sys.settrace(None)``, so those tests save and restore
# the original trace function (e.g. for coverage.py).
# -----------------------------------------------------------------------------

_ANSI_ESCAPE_RE = re_module.compile(r"\x1b\[[0-9;]*m")


def _uncolor(text):
    """Remove ANSI color escapes from ``text``."""
    return _ANSI_ESCAPE_RE.sub("", text)


def _make_pdb(**kwargs):
    """Create a Pdb instance writing to a StringIO, with colors disabled."""
    kwargs.setdefault("readrc", False)
    p = debugger.Pdb(stdout=io.StringIO(), **kwargs)
    p.set_theme_name("nocolor")
    return p


def _post_mortem_pdb(tb_or_exc, cls=debugger.Pdb, **kwargs):
    """Create a Pdb instance set up post-mortem on a traceback/exception."""
    kwargs.setdefault("readrc", False)
    p = cls(stdout=io.StringIO(), **kwargs)
    p.set_theme_name("nocolor")
    p.reset()
    tb = (
        tb_or_exc.__traceback__
        if isinstance(tb_or_exc, BaseException)
        else tb_or_exc
    )
    p.setup(None, tb)
    return p


def _run_pdb_session(commands, tb_or_exc, cls=debugger.Pdb, **kwargs):
    """Run a full interactive post-mortem session, feeding ``commands``.

    Quitting the debugger calls ``sys.settrace(None)``, so the original trace
    function is restored afterwards (e.g. for coverage.py).
    """
    kwargs.setdefault("readrc", False)
    stdout = io.StringIO()
    p = cls(stdin=_FakeInput(list(commands)), stdout=stdout, **kwargs)
    p.set_theme_name("nocolor")
    p.reset()
    old_trace = sys.gettrace()
    try:
        p.interaction(None, tb_or_exc)
    finally:
        sys.settrace(old_trace)
    return p, stdout.getvalue()


def _simple_exc():
    """Return a ValueError whose traceback contains a frame with locals."""

    def fail():
        myvar = 42
        raise ValueError("simple-boom %s" % myvar)

    try:
        fail()
    except ValueError as exc:
        return exc


def _mixed_hidden_exc():
    """Exception with both hidden and visible frames in its traceback."""

    def raiser():
        __tracebackhide__ = True
        raise ValueError("mixed-boom")

    def hidden_mid():
        __tracebackhide__ = True
        return raiser()

    def visible_top():
        return hidden_mid()

    try:
        visible_top()
    except ValueError as exc:
        return exc


def _chained_exc():
    try:
        try:
            1 / 0
        except ZeroDivisionError as inner:
            raise ValueError("chained-boom") from inner
    except ValueError as exc:
        return exc


_FAKE_MODULE_SOURCE = '''\
"""Fake module for debugger tests."""


class ExampleClass:
    """Docstring for ExampleClass."""


def example_function(x, y=3):
    """Docstring for example_function."""
    return x + y


def fail():
    value = example_function(1)
    raise ValueError("failing-module %s" % value)


fail()
'''


def _exec_failing_module(tmp_path, name="pdb_fake_mod"):
    """Execute a small failing module from a real file, return (exc, path)."""
    path = tmp_path / (name + ".py")
    path.write_text(_FAKE_MODULE_SOURCE, encoding="utf-8")
    ns = {"__name__": name, "__file__": str(path)}
    try:
        exec(compile(_FAKE_MODULE_SOURCE, str(path), "exec"), ns)
    except ValueError as exc:
        return exc, str(path)
    raise AssertionError("fake module should have raised")


@pytest.fixture
def restore_pdb_predicates():
    """``Pdb._predicates`` aliases the class-level ``default_predicates``
    dict, so tests toggling predicates must restore its contents."""
    saved = dict(debugger.Pdb.default_predicates)
    yield
    debugger.Pdb.default_predicates.clear()
    debugger.Pdb.default_predicates.update(saved)


def test_bdbquit_excepthook_is_deprecated():
    with pytest.raises(ValueError, match="deprecated"):
        debugger.BdbQuit_excepthook(None, None, None)


def test_strip_indentation_and_doc_decoration():
    assert debugger.strip_indentation("hello\n    world") == "hello\nworld"
    # do_quit is decorated with the stripped stdlib docstring
    assert debugger.Pdb.do_quit.__doc__.startswith("q(uit)")
    assert debugger.Pdb.do_q.__doc__ == debugger.Pdb.do_quit.__doc__


def test_pdb_context_argument():
    assert _make_pdb(context=None).context == 5
    assert _make_pdb(context="7").context == 7
    p = _make_pdb(context=3)
    assert p.context == 3
    p.context = "9"
    assert p.context == 9
    with pytest.raises(ValueError):
        _make_pdb(context="not-a-number")
    with pytest.raises(AssertionError):
        p.context = -1


def test_do_context_command():
    p = _post_mortem_pdb(_simple_exc())
    p.onecmd("context 11")
    assert p.context == 11
    p.onecmd("context 0")
    assert "positive integer" in p.stdout.getvalue()
    assert p.context == 11
    p.onecmd("context banana")
    assert p.context == 11


def test_set_colors_is_deprecated():
    p = _make_pdb()
    with pytest.warns(DeprecationWarning, match="set_theme_name"):
        p.set_colors("nocolor")
    assert p._theme_name == "nocolor"
    assert p.theme is PyColorize.theme_table["nocolor"]


def test_get_stack_hides_bdb_internal_frames():
    src = (
        "def runcall():\n"
        "    def inner():\n"
        "        raise ValueError('fake bdb error')\n"
        "    try:\n"
        "        inner()\n"
        "    except ValueError as exc:\n"
        "        holder.append(exc)\n"
        "runcall()\n"
    )
    holder = []
    exec(compile(src, "bdb.py", "exec"), {"holder": holder})
    exc = holder[0]
    tb = exc.__traceback__

    p = _make_pdb()
    # 'runcall' in a file named bdb.py is considered internal ...
    assert p._is_internal_frame(tb.tb_frame) is True
    # ... but other functions in it are not, nor are frames of other files
    assert p._is_internal_frame(tb.tb_next.tb_frame) is False
    assert p._is_internal_frame(sys._getframe()) is False

    stack, pos = p.get_stack(None, tb)
    assert [f.f_code.co_name for f, _ in stack] == ["inner"]
    assert pos == 0


def test_hidden_predicate_readonly_files(restore_pdb_predicates):
    p = _make_pdb()
    frame = sys._getframe()
    # no __tracebackhide__ local, not read-only: not hidden
    assert p._hidden_predicate(frame) is False
    p._predicates["readonly"] = True
    with patch("IPython.core.debugger.os.access", return_value=False):
        assert p._hidden_predicate(frame) is True
    p._predicates["readonly"] = False
    # with the tbhide predicate disabled nothing is ever hidden
    p._predicates["tbhide"] = False
    assert p._hidden_predicate(_hidden_frame_capture()) is False


def test_do_skip_predicates_command(restore_pdb_predicates, capsys):
    p = _make_pdb()

    p.do_skip_predicates("")
    out = capsys.readouterr().out
    assert "current predicates:" in out
    assert "tbhide" in out

    p.do_skip_predicates("tbhide")  # wrong number of arguments
    assert "Usage: skip_predicates" in capsys.readouterr().out

    p.do_skip_predicates("nonsense true")
    assert "not in" in capsys.readouterr().out

    p.do_skip_predicates("tbhide banana")
    assert "is invalid" in capsys.readouterr().out

    p.do_skip_predicates("tbhide false")
    assert p._predicates["tbhide"] is False

    for key in list(p._predicates):
        p.do_skip_predicates(f"{key} false")
    assert "may not have any effects" in capsys.readouterr().out


def test_do_skip_hidden_command(restore_pdb_predicates, capsys):
    p = _make_pdb()
    p.do_skip_hidden("")
    assert "skip_hidden = True" in capsys.readouterr().out
    p.do_skip_hidden("false")
    assert p.skip_hidden is False
    p.do_skip_hidden("yes")
    assert p.skip_hidden is True
    for key in list(p._predicates):
        p._predicates[key] = False
    p.do_skip_hidden("true")
    assert "may not have any effects" in capsys.readouterr().out


def test_where_and_navigation_with_hidden_frames(capsys):
    p = _post_mortem_pdb(_mixed_hidden_exc())
    names = [f.f_code.co_name for f, _ in p.stack]
    assert names[-3:] == ["visible_top", "hidden_mid", "raiser"]
    assert p.curindex == len(p.stack) - 1

    # hidden_mid is skipped; raiser is the current frame so it is shown
    p.onecmd("where")
    out = _uncolor(p.stdout.getvalue())
    assert "[... skipping 1 hidden frame(s)]" in out
    assert "raiser" in out

    p.onecmd("up")
    assert p.curframe.f_code.co_name == "visible_top"
    assert "1 hidden frames + 0 ignored modules" in _uncolor(
        capsys.readouterr().out
    )

    # now both hidden_mid and raiser are hidden, at the end of the stack
    p.onecmd("where")
    assert "[... skipping 2 hidden frame(s)]" in _uncolor(p.stdout.getvalue())

    # every frame below the current one is hidden
    p.onecmd("down")
    assert "all frames below skipped" in p.stdout.getvalue()

    p.onecmd("skip_hidden false")
    p.onecmd("down")
    assert p.curframe.f_code.co_name == "hidden_mid"
    # not at the newest frame: an unparsable count is reported
    p.onecmd("down banana")
    assert "Invalid frame count" in p.stdout.getvalue()
    p.onecmd("down")
    assert p.curframe.f_code.co_name == "raiser"
    p.onecmd("down")
    assert "Newest frame" in p.stdout.getvalue()

    p.onecmd("up -1")
    assert p.curindex == 0
    p.onecmd("up")
    assert "Oldest frame" in p.stdout.getvalue()
    p.onecmd("down -1")
    assert p.curindex == len(p.stack) - 1

    p.onecmd("up banana")
    assert "Invalid frame count" in p.stdout.getvalue()

    p.onecmd("up 99")
    assert "all frames above skipped" in p.stdout.getvalue()

    p.onecmd("w 1")
    p.onecmd("where banana")
    assert "***" in p.stdout.getvalue()


def test_navigation_with_ignored_modules(tmp_path, capsys):
    exc, path = _exec_failing_module(tmp_path, name="pdb_ignored_mod")
    p = _post_mortem_pdb(exc)
    assert p.curframe.f_code.co_name == "fail"

    p.onecmd("ignore_module")
    assert "No modules are currently ignored." in capsys.readouterr().out

    p.onecmd("ignore_module pdb_ignored_mod")
    p.onecmd("ignore_module")
    assert "pdb_ignored_mod" in capsys.readouterr().out

    # the module-level frame of the fake module is skipped when going up
    p.onecmd("up")
    assert p.curframe.f_code.co_name == "_exec_failing_module"
    assert "0 hidden frames + 1 ignored modules" in _uncolor(
        capsys.readouterr().out
    )

    # going down is impossible: every frame below is in the ignored module
    p.onecmd("down")
    assert "all frames below skipped" in p.stdout.getvalue()

    p.onecmd("unignore_module nonexistent")
    assert "Module nonexistent is not currently ignored" in capsys.readouterr().out

    p.onecmd("unignore_module pdb_ignored_mod")
    p.onecmd("ignore_module")
    assert "No modules are currently ignored." in capsys.readouterr().out

    p.onecmd("down")
    assert p.curframe.f_code.co_name == "<module>"


def test_down_reports_skipped_hidden_frames(capsys):
    def raiser():
        raise ValueError("down-boom")

    def hidden_mid():
        __tracebackhide__ = True
        return raiser()

    try:
        hidden_mid()
    except ValueError as e:
        exc = e

    p = _post_mortem_pdb(exc)
    p.onecmd("up")  # skips hidden_mid on the way up
    capsys.readouterr()
    p.onecmd("down")  # ... and again on the way down
    assert p.curframe.f_code.co_name == "raiser"
    assert "1 hidden frames + 0 ignored modules" in _uncolor(
        capsys.readouterr().out
    )


def test_unignore_module_with_no_ignore_list(capsys):
    p = _make_pdb()
    assert p.skip is None
    p.onecmd("unignore_module")
    assert "No modules are currently ignored." in capsys.readouterr().out
    assert p.skip == set()


def test_do_list_and_longlist(tmp_path):
    exc, path = _exec_failing_module(tmp_path)
    p = _post_mortem_pdb(exc)

    p.onecmd("list")
    out = _uncolor(p.stdout.getvalue())
    assert "raise ValueError" in out
    p.onecmd("list")  # continue from the last listed position
    p.onecmd("list .")  # jump back to the current frame
    p.onecmd("list 1,5")
    assert "Fake module for debugger tests" in _uncolor(p.stdout.getvalue())
    p.onecmd("list 8,2")  # last < first is treated as a count
    p.onecmd("list 4")
    p.onecmd("l 1,3")
    # evaluates but cannot be converted to an int
    p.onecmd("list 'banana'")
    assert "*** Error in argument:" in p.stdout.getvalue()

    p.onecmd("longlist")
    assert "def fail():" in _uncolor(p.stdout.getvalue())

    # 'll' on a module-level frame prints the whole module
    p.onecmd("up")
    assert p.curframe.f_code.co_name == "<module>"
    p.onecmd("ll")
    assert "class ExampleClass" in _uncolor(p.stdout.getvalue())


def test_longlist_error_and_exec_filename(tmp_path):
    src = "def fail():\n    raise ValueError('nofile-boom')\n\nfail()\n"
    try:
        exec(compile(src, "<string>", "exec"), {})
    except ValueError as e:
        exc = e

    p = _post_mortem_pdb(exc)
    # the source of a '<string>' frame is not available
    p.onecmd("longlist")
    assert "***" in p.stdout.getvalue()

    # ... unless _exec_filename points at a real file
    path = tmp_path / "exec_source.py"
    path.write_text(src, encoding="utf-8")
    p._exec_filename = str(path)
    p.onecmd("list 1,4")
    assert "nofile-boom" in _uncolor(p.stdout.getvalue())


def test_list_shows_breakpoint_markers(tmp_path):
    exc, path = _exec_failing_module(tmp_path)
    p = _post_mortem_pdb(exc)
    try:
        p.onecmd(f"break {path}:10")
        breaks = p.get_breaks(path, 10)
        assert len(breaks) == 1
        bp = breaks[-1]

        p.onecmd("list 8,11")
        assert str(bp.number) in _uncolor(p.stdout.getvalue())

        # disabled breakpoints are rendered with a different token
        p.onecmd(f"disable {bp.number}")
        p.onecmd("list 8,11")
        p.onecmd(f"enable {bp.number}")
        p.onecmd("longlist")
    finally:
        p.clear_all_breaks()


def test_format_stack_entry_return_and_args(tmp_path):
    exc, path = _exec_failing_module(tmp_path)
    p = _post_mortem_pdb(exc)
    p.curframe_locals["__return__"] = "some-return-value"
    p.curframe_locals["__args__"] = (1, 2, 3)
    out = _uncolor(p.format_stack_entry(p.stack[p.curindex]))
    assert "some-return-value" in out
    assert "(1, 2, 3)" in out
    assert "fail" in out

    # formatting of a frame which is not the current one
    out2 = _uncolor(p.format_stack_entry(p.stack[p.curindex - 1]))
    assert "<module>" in out2

    # a context of 0 is reported as invalid
    p.context = 0
    p.format_stack_entry(p.stack[p.curindex])
    assert "Context must be a positive integer" in p.stdout.getvalue()


@pytest.mark.skipif(
    not debugger.CHAIN_EXCEPTIONS,
    reason="chained exception navigation is not available",
)
def test_do_exceptions_navigation():
    exc = _chained_exc()
    p = _make_pdb()
    p.reset()
    exceptions, tb = p._get_tb_and_exceptions(exc)
    assert [type(e) for e in exceptions] == [ZeroDivisionError, ValueError]
    p.setup(None, tb)
    with p._hold_exceptions(exceptions):
        p.onecmd("exceptions")
        out = p.stdout.getvalue()
        assert "ZeroDivisionError" in out
        assert "chained-boom" in out

        p.onecmd("exceptions 0")
        assert p.curframe.f_code.co_name == "_chained_exc"
        assert "1 / 0" in _uncolor(p.stdout.getvalue())

        p.onecmd("exceptions not-a-number")
        assert "Argument must be an integer" in p.stdout.getvalue()

        p.onecmd("exceptions 99")
        assert "No exception with that number" in p.stdout.getvalue()

        p.onecmd("exception 1")  # alias, switch back to the ValueError
        assert "raise ValueError" in _uncolor(p.stdout.getvalue())

    # _hold_exceptions cleans up the exception references
    assert p._chained_exceptions == tuple()
    assert p._chained_exception_index == 0


@pytest.mark.skipif(
    not debugger.CHAIN_EXCEPTIONS,
    reason="chained exception navigation is not available",
)
def test_do_exceptions_without_traceback():
    try:
        raise ValueError("outer-boom") from KeyError("never-raised")
    except ValueError as e:
        exc = e

    p = _make_pdb()
    p.reset()
    exceptions, tb = p._get_tb_and_exceptions(exc)
    p.setup(None, tb)
    with p._hold_exceptions(exceptions):
        p.onecmd("exceptions")
        assert "never-raised" in p.stdout.getvalue()
        # the cause was never raised, so it cannot be selected
        p.onecmd("exceptions 0")
        assert "does not have a traceback" in p.stdout.getvalue()


@pytest.mark.skipif(
    not debugger.CHAIN_EXCEPTIONS,
    reason="chained exception navigation is not available",
)
def test_do_exceptions_without_chain():
    p = _post_mortem_pdb(_simple_exc().__traceback__)
    p.onecmd("exceptions")
    assert "Did not find chained exceptions" in p.stdout.getvalue()


@pytest.mark.skipif(
    not debugger.CHAIN_EXCEPTIONS,
    reason="chained exception navigation is not available",
)
def test_do_exceptions_truncates_long_reprs():
    try:
        raise ValueError("x" * 200)
    except ValueError as e:
        exc = e
    p = _make_pdb()
    p.reset()
    exceptions, tb = p._get_tb_and_exceptions(exc)
    p.setup(None, tb)
    with p._hold_exceptions(exceptions):
        p.onecmd("exceptions")
    out = p.stdout.getvalue()
    assert "..." in out
    assert "x" * 200 not in out


@pytest.mark.skipif(
    not debugger.CHAIN_EXCEPTIONS,
    reason="chained exception navigation is not available",
)
def test_get_tb_and_exceptions_edge_cases():
    p = _make_pdb()

    # a plain traceback is passed through unchanged
    exc = _simple_exc()
    exceptions, tb = p._get_tb_and_exceptions(exc.__traceback__)
    assert exceptions == tuple()
    assert tb is exc.__traceback__

    # cycles in the exception chain do not cause an infinite loop
    e1, e2 = ValueError("one"), KeyError("two")
    e1.__context__ = e2
    e2.__context__ = e1
    exceptions, _ = p._get_tb_and_exceptions(e1)
    assert exceptions == (e2, e1)

    # overly long chains are truncated with a message
    p.MAX_CHAINED_EXCEPTION_DEPTH = 2
    a, b, c = ValueError("a"), KeyError("b"), TypeError("c")
    a.__context__ = b
    b.__context__ = c
    exceptions, _ = p._get_tb_and_exceptions(a)
    assert len(exceptions) == 2
    assert "More than 2 chained exceptions found" in p.stdout.getvalue()


def test_pinfo_family_commands(tmp_path, capsys):
    exc, path = _exec_failing_module(tmp_path)
    p = _post_mortem_pdb(exc)

    p.onecmd("pdef example_function")
    assert "example_function(x, y=3)" in _uncolor(capsys.readouterr().out)

    p.onecmd("pdoc ExampleClass")
    assert "Docstring for ExampleClass" in _uncolor(capsys.readouterr().out)

    p.onecmd("pinfo value")
    assert "int" in _uncolor(capsys.readouterr().out)

    p.onecmd("pinfo2 example_function")
    assert "Docstring for example_function" in _uncolor(capsys.readouterr().out)

    p.onecmd("psource example_function")
    assert "return x + y" in _uncolor(capsys.readouterr().out)

    p.onecmd("pfile example_function")
    assert "Fake module for debugger tests" in _uncolor(capsys.readouterr().out)


def test_precmd_question_mark_rewriting():
    p = _make_pdb()
    assert p.precmd("foo?") == "pinfo foo"
    assert p.precmd("foo??") == "pinfo2 foo"
    assert p.precmd("list") == "list"


def test_interaction_session_with_exception():
    exc = _simple_exc()
    p, out = _run_pdb_session(["myvar + 1", "q"], exc)
    assert "ipdb>" in out
    assert "43" in out


def test_interaction_session_with_traceback_object():
    exc = _simple_exc()
    p, out = _run_pdb_session(["myvar", "quit"], exc.__traceback__)
    assert "42" in out


def test_cmdloop_resumes_after_keyboard_interrupt():
    exc = _simple_exc()
    p, out = _run_pdb_session(
        ["raise KeyboardInterrupt()", "myvar", "q"], exc
    )
    # '--KeyboardInterrupt--' from cmdloop up to Python 3.12,
    # '*** KeyboardInterrupt' from onecmd's error handling on 3.13+
    assert "KeyboardInterrupt" in out
    assert "42" in out


def test_interruptible_pdb_aborts_session_on_keyboard_interrupt():
    exc = _simple_exc()
    # on Python <= 3.12 the KeyboardInterrupt aborts the session and the
    # trailing 'q' is never consumed; on 3.13+ onecmd reports the exception
    # ('*** KeyboardInterrupt') and the session needs the 'q' to end
    p, out = _run_pdb_session(
        ["raise KeyboardInterrupt()", "q"], exc, cls=debugger.InterruptiblePdb
    )
    assert "KeyboardInterrupt" in out


@pytest.mark.skipif(
    sys.version_info >= (3, 15),
    reason="the recursive debugger reads from real stdin on Python 3.15",
)
def test_do_debug_runs_recursive_debugger():
    exc = _simple_exc()
    p = _post_mortem_pdb(exc)
    p.stdin = _FakeInput(["c"])
    old_trace = sys.gettrace()
    try:
        p.onecmd("debug myvar + 1")
    finally:
        sys.settrace(old_trace)
    out = p.stdout.getvalue()
    assert "ENTERING RECURSIVE DEBUGGER" in out
    assert "LEAVING RECURSIVE DEBUGGER" in out


def _frame_tagged_with_debuggerskip():
    __debuggerskip__ = True
    return sys._getframe()


def _plain_frame_capture():
    return sys._getframe()


def _frame_with_skipping_parent():
    __debuggerskip__ = True
    return _plain_frame_capture()


def test_break_anywhere_and_debuggerskip(restore_pdb_predicates):
    p = _make_pdb()
    tagged = _frame_tagged_with_debuggerskip()
    child = _frame_with_skipping_parent()
    plain = _plain_frame_capture()

    assert p.break_anywhere(tagged) is True
    assert p.break_anywhere(child) is True
    assert p.break_anywhere(plain) is False

    # a breakpoint in the frame's file short-circuits the predicates
    assert p.set_break(p.canonic(plain.f_code.co_filename), plain.f_lineno) is None
    try:
        assert p.break_anywhere(plain)
    finally:
        p.clear_all_breaks()

    assert p._is_in_decorator_internal_and_should_skip(tagged) is True
    assert p._cachable_skip(child) is True
    assert p._cached_one_parent_frame_debuggerskip(plain) is None

    p._predicates["debuggerskip"] = False
    assert p.break_anywhere(plain) is False
    assert p._is_in_decorator_internal_and_should_skip(tagged) is False


def _hidden_frame_capture():
    __tracebackhide__ = True
    return sys._getframe()


def test_stop_here_reports_hidden_and_ignored_frames(capsys):
    p = _make_pdb()
    p.reset()

    # frames in decorator internals tagged with __debuggerskip__ never stop
    assert p.stop_here(_frame_tagged_with_debuggerskip()) is False

    hidden = _hidden_frame_capture()
    assert p.stop_here(hidden) is True
    assert "[... skipped 1 hidden frame(s)]" in _uncolor(capsys.readouterr().out)

    src = "def capture():\n    holder.append(sys._getframe())\ncapture()\n"
    holder = []
    exec(
        compile(src, "<pdb_skip_mod>", "exec"),
        {"holder": holder, "sys": sys, "__name__": "pdb_skip_mod"},
    )
    mod_frame = holder[0]
    p.skip = {"pdb_skip_mod"}
    assert p.stop_here(mod_frame) is False
    assert "[... skipped 1 ignored module(s)]" in _uncolor(capsys.readouterr().out)


def test_getsourcelines_module_object():
    p = _make_pdb()
    lines, lineno = p.getsourcelines(debugger)
    assert lineno == 1
    assert any("class Pdb" in line for line in lines)


def test_pdb_creates_shell_when_no_ipython(monkeypatch):
    # when there is no IPython instance a terminal shell is created
    monkeypatch.setattr(debugger, "get_ipython", lambda: None)
    main_before = sys.modules["__main__"]
    p = _make_pdb()
    assert p.shell is not None
    assert sys.modules["__main__"] is main_before


def test_set_trace_function_with_header(capsys):
    old_trace = sys.gettrace()
    try:
        with PdbTestInput(["continue"]):
            debugger.set_trace(header="custom-pdb-header")
    finally:
        sys.settrace(old_trace)
    out = capsys.readouterr().out
    assert "custom-pdb-header" in out


# -----------------------------------------------------------------------------
# TerminalPdb tests
# -----------------------------------------------------------------------------


def _cleanup_terminal_pdb(p):
    p.thread_executor.shutdown(wait=False)
    loop = getattr(p, "pt_loop", None)
    if loop is not None:
        loop.close()


@skip_win32
@pytest.mark.skipif(
    sys.version_info >= (3, 15),
    reason="pdb internals changed in Python 3.15",
)
def test_terminal_pdb_cmdloop_requires_rawinput():
    p = TerminalPdb(stdout=io.StringIO(), readrc=False)
    try:
        with pytest.raises(ValueError, match="use_rawinput"):
            p.cmdloop()
    finally:
        _cleanup_terminal_pdb(p)


@skip_win32
def test_terminal_pdb_cmdqueue_session(capsys):
    exc = _simple_exc()
    p = TerminalPdb(readrc=False)
    try:
        p.set_theme_name("nocolor")
        p.cmdqueue = ["where 1", "myvar", "q"]
        p.reset()
        p.setup(None, exc.__traceback__)
        old_trace = sys.gettrace()
        try:
            p.cmdloop(intro="TERMINAL-PDB-INTRO")
        finally:
            sys.settrace(old_trace)
        out = _uncolor(capsys.readouterr().out)
        assert "TERMINAL-PDB-INTRO" in out
        assert "42" in out

        # the completer offers the debugger command names
        matches = p._ptcomp.ipy_completer.custom_matchers[0]("whe")
        assert "where" in matches
    finally:
        _cleanup_terminal_pdb(p)


@skip_win32
def test_terminal_pdb_reuses_shell_history(monkeypatch):
    from prompt_toolkit.history import InMemoryHistory

    shell = _make_pdb().shell
    hist = InMemoryHistory()
    monkeypatch.setattr(shell, "debugger_history", hist)
    p = TerminalPdb(readrc=False)
    try:
        assert p.debugger_history is hist
    finally:
        _cleanup_terminal_pdb(p)


@skip_win32
def test_terminal_pdb_simple_prompt_input(monkeypatch, capsys):
    import IPython.terminal.debugger as tdebugger

    monkeypatch.setattr(tdebugger, "_use_simple_prompt", True)
    exc = _simple_exc()
    p = TerminalPdb(readrc=False)
    try:
        p.set_theme_name("nocolor")
        answers = iter(["myvar * 2", "q"])
        monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
        p.reset()
        old_trace = sys.gettrace()
        try:
            p.interaction(None, exc)
        finally:
            sys.settrace(old_trace)
        assert "84" in capsys.readouterr().out
    finally:
        _cleanup_terminal_pdb(p)


@skip_win32
def test_terminal_pdb_prompt_eof_quits(monkeypatch):
    exc = _simple_exc()
    p = TerminalPdb(readrc=False)
    try:
        p.set_theme_name("nocolor")

        def raise_eof():
            raise EOFError

        monkeypatch.setattr(p, "_prompt", raise_eof)
        p.reset()
        old_trace = sys.gettrace()
        try:
            p.interaction(None, exc)
        finally:
            sys.settrace(old_trace)
    finally:
        _cleanup_terminal_pdb(p)


@skip_win32
def test_terminal_pdb_do_interact(monkeypatch):
    import IPython.terminal.debugger as tdebugger

    calls = {}

    class FakeEmbeddedShell:
        def __init__(self, **kwargs):
            calls["init"] = kwargs

        def __call__(self, module=None, local_ns=None):
            calls["module"] = module
            calls["local_ns"] = local_ns

    monkeypatch.setattr(tdebugger.embed, "InteractiveShellEmbed", FakeEmbeddedShell)
    exc = _simple_exc()
    p = TerminalPdb(readrc=False)
    try:
        p.reset()
        p.setup(None, exc.__traceback__)
        p.do_interact("")
        assert calls["init"]["banner1"] == "*interactive*"
        assert calls["local_ns"]["myvar"] == 42
    finally:
        _cleanup_terminal_pdb(p)


@skip_win32
def test_terminal_debugger_set_trace_uses_caller_frame(monkeypatch):
    import IPython.terminal.debugger as tdebugger

    recorded = {}

    def fake_set_trace(self, frame=None):
        recorded["frame"] = frame
        recorded["self"] = self

    monkeypatch.setattr(TerminalPdb, "set_trace", fake_set_trace)
    tdebugger.set_trace()
    try:
        assert (
            recorded["frame"].f_code.co_name
            == "test_terminal_debugger_set_trace_uses_caller_frame"
        )
    finally:
        _cleanup_terminal_pdb(recorded["self"])

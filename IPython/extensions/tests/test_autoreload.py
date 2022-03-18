"""Tests for autoreload extension.
"""
# -----------------------------------------------------------------------------
#  Copyright (c) 2012 IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import os
import platform
import pytest
import sys
import tempfile
import textwrap
import shutil
import random
import time
from io import StringIO

import IPython.testing.tools as tt

from unittest import TestCase

from IPython.extensions.autoreload import AutoreloadMagics
from IPython.core.events import EventManager, pre_run_cell
from IPython.testing.decorators import skipif_not_numpy

if platform.python_implementation() == "PyPy":
    pytest.skip(
        "Current autoreload implementation is extremely slow on PyPy",
        allow_module_level=True,
    )

# -----------------------------------------------------------------------------
# Test fixture
# -----------------------------------------------------------------------------

noop = lambda *a, **kw: None


class FakeShell:
    def __init__(self):
        self.ns = {}
        self.user_ns = self.ns
        self.user_ns_hidden = {}
        self.events = EventManager(self, {"pre_run_cell", pre_run_cell})
        self.auto_magics = AutoreloadMagics(shell=self)
        self.events.register("pre_run_cell", self.auto_magics.pre_run_cell)

    register_magics = set_hook = noop

    def run_code(self, code):
        self.events.trigger("pre_run_cell")
        exec(code, self.user_ns)
        self.auto_magics.post_execute_hook()

    def push(self, items):
        self.ns.update(items)

    def magic_autoreload(self, parameter):
        self.auto_magics.autoreload(parameter)

    def magic_aimport(self, parameter, stream=None):
        self.auto_magics.aimport(parameter, stream=stream)
        self.auto_magics.post_execute_hook()


class RewritableFile:
    def __init__(self, path):
        self.path = path

        # start mtime at a year ago. this assumes the file isn't
        # going to be rewritten millions of times, but given that
        # would make the test take an "unreasonably long time" it
        # seems like a reasonable assumption
        self.utime = int(time.time()) - (60 * 60 * 24 * 365)

    def __str__(self):
        return self.path

    def write(self, content):
        """
        Write a file, and force a timestamp difference of at least one second

        Notes
        -----
        Python's .pyc files record the timestamp of their compilation
        with a time resolution of one second.

        Therefore, we need to force a timestamp difference between .py
        and .pyc, without having the .py file be timestamped in the
        future, and without changing the timestamp of the .pyc file
        (because that is stored in the file).  This method assumes
        that each file isn't going to be rewritten more than a million
        times.
        """

        with open(self.path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(content))

        # monotonically increment times
        self.utime += 1
        os.utime(self.path, (self.utime, self.utime))


class Fixture(TestCase):
    """Fixture for creating test module files"""

    test_dir = None
    old_sys_path = None
    filename_chars = "abcdefghijklmopqrstuvwxyz0123456789"

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_sys_path = list(sys.path)
        sys.path.insert(0, self.test_dir)
        self.shell = FakeShell()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        sys.path = self.old_sys_path

        self.test_dir = None
        self.old_sys_path = None
        self.shell = None

    def get_module(self):
        module_name = "tmpmod_" + "".join(random.sample(self.filename_chars, 20))
        if module_name in sys.modules:
            del sys.modules[module_name]
        file_name = os.path.join(self.test_dir, module_name + ".py")
        return module_name, file_name

    def new_module(self, code):
        mod_name, path = self.get_module()

        mod = RewritableFile(path)
        mod.write(code)

        return mod_name, mod


# -----------------------------------------------------------------------------
# Test automatic reloading
# -----------------------------------------------------------------------------


def pickle_get_current_class(obj):
    """
    Original issue comes from pickle; hence the name.
    """
    name = obj.__class__.__name__
    module_name = getattr(obj, "__module__", None)
    obj2 = sys.modules[module_name]
    for subpath in name.split("."):
        obj2 = getattr(obj2, subpath)
    return obj2


class TestAutoreload(Fixture):
    def test_reload_enums(self):
        code1 = """
        from enum import Enum
        class MyEnum(Enum):
            A = 'A'
            B = 'B'
        """
        code2 = """
        from enum import Enum
        class MyEnum(Enum):
            A = 'A'
            B = 'B'
            C = 'C'
        """
        mod_name, mod = self.new_module(code1)
        self.shell.magic_autoreload("2")
        self.shell.magic_aimport(mod_name)
        mod.write(code2)
        with tt.AssertNotPrints(
            ("[autoreload of %s failed:" % mod_name), channel="stderr"
        ):
            self.shell.run_code("pass")  # trigger another reload

    def test_reload_class_type(self):
        code1 = """
        class Test():
            def meth(self):
                return "old"
        """
        code2 = """
        class Test():
            def meth(self):
                return "new"
        """

        self.shell.magic_autoreload("2")
        mod_name, mod = self.new_module(code1)
        assert "test" not in self.shell.ns
        assert "result" not in self.shell.ns

        self.shell.run_code("from %s import Test" % mod_name)
        self.shell.run_code("test = Test()")

        mod.write(code2)
        test_object = self.shell.ns["test"]

        # important to trigger autoreload logic !
        self.shell.run_code("pass")

        test_class = pickle_get_current_class(test_object)
        assert isinstance(test_object, test_class)

        # extra check.
        self.shell.run_code("import pickle")
        self.shell.run_code("p = pickle.dumps(test)")

    def test_reload_class_attributes(self):
        code1 = """
        class MyClass:
            def __init__(self, a=10):
                self.a = a
                self.b = 22
            def square(self):
                print('compute square')
                return self.a*self.a
        """
        code2 = """
        class MyClass:
            def __init__(self, a=10):
                self.a = a
                self.b = 11
            def power(self, p):
                print('compute power '+str(p))
                return self.a**p
        """
        self.shell.magic_autoreload("2")
        mod_name, mod = self.new_module(code1)

        self.shell.run_code("from %s import MyClass" % mod_name)
        self.shell.run_code("first = MyClass(5)")
        self.shell.run_code("first.square()")
        with self.assertRaises(AttributeError):
            self.shell.run_code("first.cube()")
        with self.assertRaises(AttributeError):
            self.shell.run_code("first.power(5)")
        self.shell.run_code("first.b")
        with self.assertRaises(AttributeError):
            self.shell.run_code("first.toto")

        # remove square, add power
        mod.write(code2)

        self.shell.run_code("second = MyClass(5)")

        for object_name in {"first", "second"}:
            self.shell.run_code(f"{object_name}.power(5)")
            with self.assertRaises(AttributeError):
                self.shell.run_code(f"{object_name}.cube()")
            with self.assertRaises(AttributeError):
                self.shell.run_code(f"{object_name}.square()")
            self.shell.run_code(f"{object_name}.b")
            self.shell.run_code(f"{object_name}.a")
            with self.assertRaises(AttributeError):
                self.shell.run_code(f"{object_name}.toto")

    @skipif_not_numpy
    def test_comparing_numpy_structures(self):
        code1 = """
        import numpy as np
        class MyClass:
            a = (np.array((.1, .2)),
                 np.array((.2, .3)))
        """
        code2 = """
        import numpy as np
        class MyClass:
            a = (np.array((.3, .4)),
                 np.array((.5, .6)))
        """

        self.shell.magic_autoreload("2")
        mod_name, mod = self.new_module(code1)

        self.shell.run_code("from %s import MyClass" % mod_name)
        self.shell.run_code("first = MyClass()")

        # change property `a`
        mod.write(code2)

        with tt.AssertNotPrints(
            ("[autoreload of %s failed:" % mod_name), channel="stderr"
        ):
            self.shell.run_code("pass")  # trigger another reload

    def test_autoload_newly_added_objects(self):
        code1 = """
        def func1(): pass
        """
        code2 = """
        def func1(): pass
        def func2(): pass
        class Test: pass
        number = 0
        from enum import Enum
        class TestEnum(Enum):
            A = 'a'
        """
        code3 = """
        def func1(): return 'changed'
        def func2(): return 'changed'
        class Test:
            def new_func(self):
                return 'changed'
        number = 1
        from enum import Enum
        class TestEnum(Enum):
            A = 'a'
            B = 'added'
        """

        self.shell.magic_autoreload("3")
        mod_name, mod = self.new_module(code1)
        self.shell.run_code(f"from {mod_name} import *")
        self.shell.run_code("func1()")
        with self.assertRaises(NameError):
            self.shell.run_code("func2()")
        with self.assertRaises(NameError):
            self.shell.run_code("t = Test()")
        with self.assertRaises(NameError):
            self.shell.run_code("number")

        # ----------- TEST NEW OBJ LOADED --------------------------
        mod.write(code2)

        # test function now exists in shell's namespace namespace
        self.shell.run_code("func2()")
        # test function now exists in module's dict
        self.shell.run_code(f"import sys; sys.modules['{mod_name}'].func2()")
        # test class now exists
        self.shell.run_code("t = Test()")
        # test global built-in var now exists
        self.shell.run_code("number")
        # test the enumerations gets loaded successfully
        self.shell.run_code("TestEnum.A")

        # ----------- TEST NEW OBJ CAN BE CHANGED --------------------

        mod.write(code3)
        self.shell.run_code("assert func1() == 'changed'")
        self.shell.run_code("assert func2() == 'changed'")
        self.shell.run_code("t = Test(); assert t.new_func() == 'changed'")
        self.shell.run_code("assert number == 1")
        self.shell.run_code("assert TestEnum.B.value == 'added'")

        # ----------- TEST IMPORT FROM MODULE --------------------------
        code1 = """
        from enum import Enum
        class Ext(Enum):
            A = 'ext'
        def ext_func():
            return 'ext'
        class ExtTest:
            def meth(self):
                return 'ext'
        ext_int = 2
        """
        new_mod_name, _ = self.new_module(code1)
        code2 = f"""
        from {new_mod_name} import *
        """
        mod.write(code2)
        self.shell.run_code("assert Ext.A.value == 'ext'")
        self.shell.run_code("assert ext_func() == 'ext'")
        self.shell.run_code("t = ExtTest(); assert t.meth() == 'ext'")
        self.shell.run_code("assert ext_int == 2")

    def _check_smoketest(self, use_aimport=True):
        """
        Functional test for the automatic reloader using either
        '%autoreload 1' or '%autoreload 2'
        """
        code1 = """
        x = 9
        z = 123  # this item will be deleted
        def foo(y):
            return y + 3
        class Baz(object):
            def __init__(self, x):
                self.x = x
            def bar(self, y):
                return self.x + y
            @property
            def quux(self):
                return 42
            def zzz(self):
                '''This method will be deleted below'''
                return 99
        class Bar:    # old-style class: weakref doesn't work for it on Python < 2.7
            def foo(self):
                return 1
        """
        code2 = """
        x = 10
        def foo(y):
            return y + 4
        class Baz(object):
            def __init__(self, x):
                self.x = x
            def bar(self, y):
                return self.x + y + 1
            @property
            def quux(self):
                return 43
        class Bar:    # old-style class
            def foo(self):
                return 2
        """

        mod_name, mod = self.new_module(code1)

        #
        # Import module, and mark for reloading
        #
        if use_aimport:
            self.shell.magic_autoreload("1")
            self.shell.magic_aimport(mod_name)
            stream = StringIO()
            self.shell.magic_aimport("", stream=stream)
            self.assertIn(f"Modules to reload:\n  {mod_name}", stream.getvalue())

            with self.assertRaises(ImportError):
                self.shell.magic_aimport("tmpmod_as318989e89ds")
        else:
            self.shell.magic_autoreload("2")
            self.shell.run_code("import %s" % mod_name)
            stream = StringIO()
            self.shell.magic_aimport("", stream=stream)
            self.assertTrue(
                "Modules to reload:\nall-except-skipped" in stream.getvalue()
            )
        self.assertIn(mod_name, self.shell.ns)

        module = sys.modules[mod_name]

        #
        # Test module contents
        #
        old_foo = module.foo
        old_obj = module.Baz(9)
        old_obj2 = module.Bar()

        def check_module_contents():
            self.assertEqual(module.x, 9)
            self.assertEqual(module.z, 123)

            self.assertEqual(old_foo(0), 3)
            self.assertEqual(module.foo(0), 3)

            obj = module.Baz(9)
            self.assertEqual(old_obj.bar(1), 10)
            self.assertEqual(obj.bar(1), 10)
            self.assertEqual(obj.quux, 42)
            self.assertEqual(obj.zzz(), 99)

            obj2 = module.Bar()
            self.assertEqual(old_obj2.foo(), 1)
            self.assertEqual(obj2.foo(), 1)

        check_module_contents()

        #
        # Simulate a failed reload: no reload should occur and exactly
        # one error message should be printed
        #
        mod.write("a syntax error\n")

        with tt.AssertPrints(f"[autoreload of {mod_name} failed:", channel="stderr"):
            self.shell.run_code("pass")  # trigger reload
        with tt.AssertNotPrints(f"[autoreload of {mod_name} failed:", channel="stderr"):
            self.shell.run_code("pass")  # trigger another reload
        check_module_contents()

        #
        # Rewrite module (this time reload should succeed)
        #
        mod.write(code2)

        def check_module_contents():
            self.assertEqual(module.x, 10)
            self.assertFalse(hasattr(module, "z"))

            self.assertEqual(old_foo(0), 4)  # superreload magic!
            self.assertEqual(module.foo(0), 4)

            obj = module.Baz(9)
            self.assertEqual(old_obj.bar(1), 11)  # superreload magic!
            self.assertEqual(obj.bar(1), 11)

            self.assertEqual(old_obj.quux, 43)
            self.assertEqual(obj.quux, 43)

            self.assertFalse(hasattr(old_obj, "zzz"))
            self.assertFalse(hasattr(obj, "zzz"))

            obj2 = module.Bar()
            self.assertEqual(old_obj2.foo(), 2)
            self.assertEqual(obj2.foo(), 2)

        self.shell.run_code("pass")  # trigger reload
        check_module_contents()

        #
        # Another failure case: deleted file (shouldn't reload)
        #
        os.unlink(mod.path)

        self.shell.run_code("pass")  # trigger reload
        check_module_contents()

        #
        # Disable autoreload and rewrite module: no reload should occur
        #
        if use_aimport:
            self.shell.magic_aimport("-" + mod_name)
            stream = StringIO()
            self.shell.magic_aimport("", stream=stream)
            self.assertTrue(f"Modules to skip:\n  {mod_name}" in stream.getvalue())

            # This should succeed, although no such module exists
            self.shell.magic_aimport("-tmpmod_as318989e89ds")
        else:
            self.shell.magic_autoreload("0")

        mod.write("x = -99\n")

        self.shell.run_code("pass")  # trigger reload
        self.shell.run_code("pass")
        check_module_contents()

        #
        # Re-enable autoreload: reload should now occur
        #
        if use_aimport:
            self.shell.magic_aimport(mod_name)
        else:
            self.shell.magic_autoreload("")

        self.shell.run_code("pass")  # trigger reload
        self.assertEqual(module.x, -99)

    def test_smoketest_aimport(self):
        self._check_smoketest(use_aimport=True)

    def test_smoketest_autoreload(self):
        self._check_smoketest(use_aimport=False)

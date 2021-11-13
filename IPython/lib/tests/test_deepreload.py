# -*- coding: utf-8 -*-
"""Test suite for the deepreload module."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest
import types

from pathlib import Path

from IPython.utils.syspathcontext import prepended_to_syspath
from IPython.utils.tempdir import TemporaryDirectory
from IPython.lib.deepreload import reload as dreload, modules_reloading


def test_deepreload():
    "Test that dreload does deep reloads and skips excluded modules."
    with TemporaryDirectory() as tmpdir:
        with prepended_to_syspath(tmpdir):
            tmpdirpath = Path(tmpdir)
            with open(tmpdirpath / "A.py", "w") as f:
                f.write("class Object:\n    pass\nok = True\n")
            with open(tmpdirpath / "B.py", "w") as f:
                f.write("import A\nassert A.ok, 'we are fine'\n")
            import A
            import B

            # Test that A is not reloaded.
            obj = A.Object()
            dreload(B, exclude=["A"])
            assert isinstance(obj, A.Object) is True

            # Test that an import failure will not blow-up us.
            A.ok = False
            with pytest.raises(AssertionError, match="we are fine"):
                dreload(B, exclude=["A"])
            assert len(modules_reloading) == 0
            assert not A.ok

            # Test that A is reloaded.
            obj = A.Object()
            A.ok = False
            dreload(B)
            assert A.ok
            assert isinstance(obj, A.Object) is False


def test_not_module():
    pytest.raises(TypeError, dreload, "modulename")


def test_not_in_sys_modules():
    fake_module = types.ModuleType("fake_module")
    with pytest.raises(ImportError, match="not in sys.modules"):
        dreload(fake_module)

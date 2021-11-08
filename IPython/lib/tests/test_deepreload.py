# -*- coding: utf-8 -*-
"""Test suite for the deepreload module."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from pathlib import Path

from IPython.utils.syspathcontext import prepended_to_syspath
from IPython.utils.tempdir import TemporaryDirectory
from IPython.lib.deepreload import reload as dreload


def test_deepreload():
    "Test that dreload does deep reloads and skips excluded modules."
    with TemporaryDirectory() as tmpdir:
        with prepended_to_syspath(tmpdir):
            tmpdirpathA = Path(tmpdir / "A.py")
            tmpdirpathB = Path(tmpdir / "B.py")
            tmpdirpathA.write_text("class Object(object):\n    pass\n")
            tmpdirpathB.write_text("import A\n")
            import A
            import B

            # Test that A is not reloaded.
            obj = A.Object()
            dreload(B, exclude=["A"])
            assert isinstance(obj, A.Object) is True

            # Test that A is reloaded.
            obj = A.Object()
            dreload(B)
            assert isinstance(obj, A.Object) is False

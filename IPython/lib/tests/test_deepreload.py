# -*- coding: utf-8 -*-
"""Test suite for the deepreload module."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os

import nose.tools as nt

from IPython.testing import decorators as dec
from IPython.utils.py3compat import builtin_mod_name, PY3
from IPython.utils.syspathcontext import prepended_to_syspath
from IPython.utils.tempdir import TemporaryDirectory
from IPython.lib.deepreload import reload as dreload

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------

@dec.skipif_not_numpy
def test_deepreload_numpy():
    "Test that NumPy can be deep reloaded."
    import numpy
    # TODO: Find a way to exclude all standard library modules from reloading.
    exclude = [
        # Standard exclusions:
        'sys', 'os.path', builtin_mod_name, '__main__',
        # Test-related exclusions:
        'unittest', 'UserDict', '_collections_abc', 'tokenize',
        'collections', 'collections.abc',
        'importlib', 'importlib.machinery', '_imp',
        'importlib._bootstrap', 'importlib._bootstrap_external',
        '_frozen_importlib', '_frozen_importlib_external',
        ]

    dreload(numpy, exclude=exclude)

def test_deepreload():
    "Test that dreload does deep reloads and skips excluded modules."
    with TemporaryDirectory() as tmpdir:
        with prepended_to_syspath(tmpdir):
            with open(os.path.join(tmpdir, 'A.py'), 'w') as f:
                f.write("class Object(object):\n    pass\n")
            with open(os.path.join(tmpdir, 'B.py'), 'w') as f:
                f.write("import A\n")
            import A
            import B

            # Test that A is not reloaded.
            obj = A.Object()
            dreload(B, exclude=['A'])
            nt.assert_true(isinstance(obj, A.Object))

            # Test that A is reloaded.
            obj = A.Object()
            dreload(B)
            nt.assert_false(isinstance(obj, A.Object))

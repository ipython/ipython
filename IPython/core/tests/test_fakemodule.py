"""Tests for the FakeModule objects.
"""

import nose.tools as nt

from IPython.core.fakemodule import FakeModule

# Make a fakemod and check a few properties
def test_mk_fakemod():
    fm = FakeModule()
    yield nt.assert_true,fm
    yield nt.assert_true,lambda : hasattr(fm,'__file__')

def test_mk_fakemod_fromdict():
    """Test making a FakeModule object with initial data"""
    fm = FakeModule(dict(hello=True))
    nt.assert_true(fm.hello)

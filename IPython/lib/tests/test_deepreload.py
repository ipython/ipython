# -*- coding: utf-8 -*-
"""Test suite for the deepreload module."""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.testing import decorators as dec
from IPython.lib.deepreload import reload as dreload

#-----------------------------------------------------------------------------
# Test functions begin
#-----------------------------------------------------------------------------

@dec.skipif_not_numpy
def test_deepreload_numpy():
    import numpy
    exclude = [
        # Standard exclusions:
        'sys', 'os.path', '__builtin__', '__main__',
        # Test-related exclusions:
        'unittest',
        ]
    dreload(numpy, exclude=exclude)

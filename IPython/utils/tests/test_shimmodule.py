import pytest
import sys

from IPython.utils.shimmodule import ShimWarning


def test_shim_warning():
    sys.modules.pop('IPython.config', None)
    with pytest.warns(ShimWarning):
        import IPython.config

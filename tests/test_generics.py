"""Tests for IPython.utils.generics."""

import warnings

import pytest

from IPython.core.error import TryNext
from IPython.utils import generics


def test_inspect_object_deprecated():
    with pytest.warns(DeprecationWarning, match="inspect_object is deprecated"):
        func = generics.inspect_object
    # The returned object still behaves as before.
    with pytest.raises(TryNext):
        func(object())


def test_complete_object_not_deprecated():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert callable(generics.complete_object)

"""Tests for IPython.utils.generics (singledispatch hooks)"""

import warnings

import pytest

from IPython.core.error import TryNext
from IPython.utils import generics
from IPython.utils.generics import complete_object, inspect_object


def test_inspect_object_deprecated():
    with pytest.warns(DeprecationWarning, match="inspect_object is deprecated"):
        func = generics.inspect_object
    with pytest.raises(TryNext):
        func(object())


def test_complete_object_not_deprecated():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert callable(generics.complete_object)


def test_inspect_object_default_raises_trynext():
    with pytest.raises(TryNext):
        inspect_object(object())


def test_complete_object_default_raises_trynext():
    with pytest.raises(TryNext):
        complete_object(object(), [])


def test_inspect_object_custom_dispatch():
    class MyType:
        pass

    called_with = []

    @inspect_object.register(MyType)
    def _(obj):
        called_with.append(obj)

    obj = MyType()
    inspect_object(obj)
    assert called_with == [obj]


def test_complete_object_custom_dispatch():
    class MyType:
        pass

    @complete_object.register(MyType)
    def _(obj, prev):
        return prev + ["custom"]

    result = complete_object(MyType(), ["existing"])
    assert result == ["existing", "custom"]

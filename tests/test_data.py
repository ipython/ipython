"""Tests for IPython.utils.data."""

import warnings

import pytest

from IPython.utils.data import chop, uniq_stable


# ---------------------------------------------------------------------------
# chop
# ---------------------------------------------------------------------------


def test_chop_even_division():
    assert chop([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]


def test_chop_uneven_division():
    result = chop([1, 2, 3, 4, 5], 2)
    assert result == [[1, 2], [3, 4], [5]]


def test_chop_size_larger_than_seq():
    assert chop([1, 2], 10) == [[1, 2]]


def test_chop_size_1():
    assert chop([1, 2, 3], 1) == [[1], [2], [3]]


def test_chop_empty_sequence():
    assert chop([], 2) == []


def test_chop_string():
    result = chop("abcdef", 2)
    assert result == ["ab", "cd", "ef"]


@pytest.mark.parametrize("seq,size,expected", [
    ([1, 2, 3, 4, 5, 6], 3, [[1, 2, 3], [4, 5, 6]]),
    ([1, 2, 3, 4, 5, 6], 2, [[1, 2], [3, 4], [5, 6]]),
    ([1, 2, 3, 4, 5, 6], 6, [[1, 2, 3, 4, 5, 6]]),
])
def test_chop_parametrized(seq, size, expected):
    assert chop(seq, size) == expected


# ---------------------------------------------------------------------------
# uniq_stable (deprecated)
# ---------------------------------------------------------------------------


def test_uniq_stable_raises_deprecation_warning():
    with pytest.warns(DeprecationWarning, match="uniq_stable is deprecated"):
        uniq_stable([1, 2, 1])


def test_uniq_stable_preserves_order():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = uniq_stable([3, 1, 2, 1, 3])
    assert result == [3, 1, 2]


def test_uniq_stable_empty():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert uniq_stable([]) == []


def test_uniq_stable_all_unique():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert uniq_stable([1, 2, 3]) == [1, 2, 3]

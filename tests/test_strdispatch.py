"""Tests for IPython.utils.strdispatch."""

import pytest

from IPython.utils.strdispatch import StrDispatch


def test_s_matches_exact_string():
    dis = StrDispatch()
    dis.add_s("hello", "value1")
    matches = list(dis.s_matches("hello"))
    assert "value1" in matches


def test_s_matches_no_match_returns_empty():
    dis = StrDispatch()
    dis.add_s("hello", "value1")
    assert list(dis.s_matches("world")) == []


def test_add_re_matches_pattern():
    dis = StrDispatch()
    dis.add_re(r"h.i", "matched")
    matches = list(dis.flat_matches("hei"))
    assert "matched" in matches


def test_add_re_no_match():
    dis = StrDispatch()
    dis.add_re(r"h.i", "matched")
    matches = list(dis.flat_matches("world"))
    assert "matched" not in matches


def test_flat_matches_combines_string_and_regex():
    dis = StrDispatch()
    dis.add_s("hei", "exact")
    dis.add_re(r"h.i", "regex")
    matches = list(dis.flat_matches("hei"))
    assert "exact" in matches
    assert "regex" in matches


def test_priority_lower_number_comes_first():
    dis = StrDispatch()
    dis.add_s("key", "high_priority", priority=2)
    dis.add_s("key", "low_priority", priority=10)
    matches = list(dis.s_matches("key"))
    assert matches.index("high_priority") < matches.index("low_priority")


def test_dispatch_yields_chains():
    dis = StrDispatch()
    dis.add_s("test", "val")
    chains = list(dis.dispatch("test"))
    assert len(chains) == 1


def test_dispatch_empty_for_no_match():
    dis = StrDispatch()
    dis.add_s("test", "val")
    chains = list(dis.dispatch("other"))
    assert chains == []


def test_repr_contains_class_name():
    dis = StrDispatch()
    assert "Strdispatch" in repr(dis) or "StrDispatch" in repr(dis).lower()


def test_multiple_values_for_same_key():
    dis = StrDispatch()
    dis.add_s("key", "first", priority=1)
    dis.add_s("key", "second", priority=2)
    matches = list(dis.s_matches("key"))
    assert len(matches) == 2
    assert "first" in matches
    assert "second" in matches


def test_docstring_example():
    dis = StrDispatch()
    dis.add_s("hei", 34, priority=4)
    dis.add_s("hei", 123, priority=2)
    dis.add_re("h.i", 686)
    result = list(dis.flat_matches("hei"))
    assert result == [123, 34, 686]

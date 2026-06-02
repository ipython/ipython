"""Tests for IPython.terminal.ptutils elision helpers."""
import os
import pytest
from IPython.terminal.ptutils import _elide_point, _elide_typed


ELLIPSIS = "\N{HORIZONTAL ELLIPSIS}"

# ---------------------------------------------------------------------------
# _elide_point
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("min_elide", [0, -1, -10])
def test_elide_point_disabled_for_nonpositive_min_elide(min_elide):
    """min_elide <= 0 must return the string completely unchanged."""
    s = "a.very.long.dotted.module.path.that.would.normally.be.elided"
    assert _elide_point(s, min_elide=min_elide) == s


@pytest.mark.parametrize("s", [
    "short.path",        # fewer than 4 dot-segments
    "a.b.c",            # exactly 3 segments (no elision)
    "tiny",             # no dots at all
])
def test_elide_point_short_strings_unchanged(s):
    """Strings that don't meet elision criteria are returned as-is."""
    assert _elide_point(s, min_elide=5) == s


@pytest.mark.parametrize("s", [
    "module.submodule.component.function",
    "IPython.core.interactiveshell.InteractiveShell",
])
def test_elide_point_long_dotted_path_is_elided(s):
    result = _elide_point(s, min_elide=10)
    assert ELLIPSIS in result
    assert len(result) < len(s)


def test_elide_point_long_file_path_is_elided():
    parts = ["home", "user", "projects", "myapp", "src", "module.py"]
    s = os.sep.join(parts)
    result = _elide_point(s, min_elide=10)
    assert ELLIPSIS in result
    assert len(result) < len(s)


# ---------------------------------------------------------------------------
# _elide_typed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("min_elide", [0, -1, -10])
def test_elide_typed_disabled_for_nonpositive_min_elide(min_elide):
    """min_elide <= 0 must return the string completely unchanged."""
    s = "very_long_completion_string_that_would_normally_be_elided"
    assert _elide_typed(s, "very", min_elide=min_elide) == s


@pytest.mark.parametrize("s,typed", [
    ("short", "sh"),
    ("abc", "a"),
])
def test_elide_typed_short_strings_unchanged(s, typed):
    """Strings shorter than min_elide are returned unchanged."""
    assert _elide_typed(s, typed, min_elide=30) == s


def test_elide_typed_long_string_not_starting_with_typed_unchanged():
    s = "completion_that_doesnt_start_with_prefix_at_all"
    assert _elide_typed(s, "different_prefix_xx", min_elide=10) == s


def test_elide_typed_typed_too_short_unchanged():
    # cut_how_much = len(typed) - 3; elision only fires when cut_how_much >= 7,
    # i.e. len(typed) >= 10.  A shorter typed prefix must leave the string alone.
    s = "longstringthatstartswithtiny"
    assert _elide_typed(s, "tiny", min_elide=10) == s


def test_elide_typed_long_string_is_elided():
    # typed is 20 chars → cut_how_much = 17 ≥ 7; string starts with typed
    typed = "completion_that_is_r"
    s = typed + "eally_long_suffix_here"
    result = _elide_typed(s, typed, min_elide=10)
    assert ELLIPSIS in result
    assert len(result) < len(s)

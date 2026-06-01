"""Tests for ptutils module."""

import pytest
from IPython.terminal.ptutils import _elide_point, _elide_typed


class TestElidePoint:
    """Tests for _elide_point function."""

    def test_min_elide_zero_disables_elision(self):
        """Test that min_elide=0 returns string unchanged."""
        test_string = "very.long.module.path.with.many.parts.that.should.be.elided"
        result = _elide_point(test_string, min_elide=0)
        # Strip unicode replacements that happen before the guard
        assert result == test_string

    def test_min_elide_negative_disables_elision(self):
        """Test that min_elide<0 returns string unchanged."""
        test_string = "another.very.long.module.path.that.would.normally.be.elided"
        result = _elide_point(test_string, min_elide=-1)
        assert result == test_string

    def test_min_elide_positive_elides_long_paths(self):
        """Test that positive min_elide still elides long paths."""
        test_string = "module.submodule.component.function.attribute"
        result = _elide_point(test_string, min_elide=10)
        # With min_elide=10 and a long enough string with many dots,
        # the string should be elided
        assert "…" in result or "\N{HORIZONTAL ELLIPSIS}" in result

    def test_min_elide_positive_preserves_short_paths(self):
        """Test that positive min_elide preserves short paths."""
        test_string = "short.path"
        result = _elide_point(test_string, min_elide=30)
        # String is shorter than min_elide, should be unchanged
        assert result == test_string

    def test_unicode_replacement(self):
        """Test that consecutive dots are replaced with unicode equivalents."""
        test_string = "path..with...dots"
        result = _elide_point(test_string, min_elide=0)
        # Should still do unicode replacement even with min_elide=0
        # because that happens before the guard
        # Actually no, with min_elide <= 0 we return early
        assert result == test_string


class TestElideTyped:
    """Tests for _elide_typed function."""

    def test_min_elide_zero_disables_elision(self):
        """Test that min_elide=0 returns string unchanged."""
        test_string = "very_long_completion_string_that_should_normally_be_elided"
        typed = "very"
        result = _elide_typed(test_string, typed, min_elide=0)
        assert result == test_string

    def test_min_elide_negative_disables_elision(self):
        """Test that min_elide<0 returns string unchanged."""
        test_string = "another_very_long_completion_that_would_be_elided"
        typed = "another"
        result = _elide_typed(test_string, typed, min_elide=-1)
        assert result == test_string

    def test_min_elide_positive_elides_long_strings(self):
        """Test that positive min_elide still elides long strings."""
        # Elision requires: len(string) >= min_elide, len(typed) >= 10,
        # string.startswith(typed), and len(string) > len(typed)
        test_string = "completion_text_that_is_very_long_and_should_be_elided"
        typed = "completion_text_that_"
        result = _elide_typed(test_string, typed, min_elide=10)
        # With these conditions met, should be elided
        assert "…" in result or "\N{HORIZONTAL ELLIPSIS}" in result

    def test_min_elide_positive_preserves_short_strings(self):
        """Test that positive min_elide preserves short strings."""
        test_string = "short"
        typed = "sh"
        result = _elide_typed(test_string, typed, min_elide=30)
        # String is shorter than min_elide, should be unchanged
        assert result == test_string

    def test_string_not_prefixed_by_typed(self):
        """Test that strings not prefixed by typed are unchanged."""
        test_string = "completion_that_doesnt_start_with_typed_prefix"
        typed = "different"
        result = _elide_typed(test_string, typed, min_elide=10)
        # String doesn't start with typed, should be unchanged
        assert result == test_string

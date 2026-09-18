"""Tests for the JSON-backed theme table."""

import json
import os
import sys
import unicodedata
from types import SimpleNamespace

import pytest
from pygments.token import Token

from IPython.utils.PyColorize import (
    _BUILTIN_THEMES,
    _FORBIDDEN_SYMBOL_CATEGORIES,
    MAX_SYMBOL_LENGTH,
    _THEME_DIR,
    _theme_filename,
    Theme,
    ThemeTable,
    theme_table,
    token_from_str,
)

# Written as escapes rather than literally: these are invisible or private use
# characters, which editors and other tooling silently mangle. See
# test_the_unicode_fixtures_are_what_they_claim.
ESCAPE = "\x1b]0;pwned\x07"  # OSC, sets the window title
BIDI_OVERRIDE = "\u202e"  # RIGHT-TO-LEFT OVERRIDE, reverses the text after it
PRIVATE_USE = "\ue0b0"  # a Powerline separator
NERD_FONT = "\uf120"  # a Nerd Font glyph, also private use

#: The two places a theme that IPython does not ship can come from.
SOURCES = ["user", "installed"]


@pytest.fixture(autouse=True)
def ipython_dir(tmp_path, monkeypatch):
    """Keep the real ~/.ipython/themes out of every test in this file."""
    directory = tmp_path / "ipythondir"
    (directory / "themes").mkdir(parents=True)
    monkeypatch.setattr("IPython.paths.get_ipython_dir", lambda: str(directory))
    return directory / "themes"


class _FakeEntryPoint:
    """Stands in for an `importlib.metadata.EntryPoint`."""

    def __init__(self, name, module, attr=None):
        self.name, self.module, self.attr = name, module, attr
        self.value = f"{module}:{attr}" if attr else module


@pytest.fixture
def themes(ipython_dir, tmp_path, monkeypatch):
    """A fresh table, and an `add` to put a theme where a source looks for it.

    `add("user", ...)` writes into the IPython directory, `add("installed",
    ...)` writes into a package and registers an entry point for it. Passing no
    `data` registers the theme without leaving a file behind.
    """
    package = tmp_path / "fake_themes"
    package.mkdir()
    (package / "__init__.py").write_text("")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "fake_themes", raising=False)

    table = ThemeTable()
    table._entry_points = {}

    def add(source, name, data=None, *, raw=None, subdir=None, module="fake_themes"):
        directory = ipython_dir if source == "user" else package
        if subdir:
            directory = directory.joinpath(*subdir.split("."))
            directory.mkdir(parents=True, exist_ok=True)
        if source == "installed":
            table._entry_points[name] = _FakeEntryPoint(name, module, subdir)
        if data is not None or raw is not None:
            path = directory / _theme_filename(name)
            path.write_text(json.dumps(data) if raw is None else raw, encoding="utf-8")

    return SimpleNamespace(table=table, add=add, package=package)


def _assert_refused(table, name, match):
    """A theme that cannot be loaded warns, and behaves as if absent."""
    with pytest.warns(UserWarning, match=match):
        with pytest.raises(KeyError):
            table[name]
    assert name not in table._by_name


# --------------------------------------------------------------------------
# the themes IPython ships
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(_BUILTIN_THEMES))
def test_builtin_themes_load(name):
    theme = theme_table[name]
    assert set(theme.symbols) == {"top_line", "arrow_body", "arrow_head"}
    for tok in theme.extra_style:
        # real pygments tokens, not the dotted strings from the file
        assert isinstance(tok, type(Token.Prompt))
    for symbol in theme.symbols.values():
        assert len(symbol) <= MAX_SYMBOL_LENGTH
        categories = {unicodedata.category(c) for c in symbol}
        assert not categories & _FORBIDDEN_SYMBOL_CATEGORIES


@pytest.mark.parametrize("name", sorted(set(_BUILTIN_THEMES.values())))
def test_builtin_theme_files_are_self_describing(name):
    """Every shipped file must name itself after the file it lives in."""
    data = json.loads((_THEME_DIR / _theme_filename(name)).read_text(encoding="utf-8"))
    assert data["name"] == name
    assert set(data) <= {"name", "base", "extra_style", "symbols"}
    assert Theme.from_dict(data).extra_style == theme_table[name].extra_style


def test_neutral_aliases_the_platform_theme():
    platform_theme = theme_table["neutral:nt" if os.name == "nt" else "neutral:posix"]
    assert theme_table["neutral"].extra_style == platform_theme.extra_style


def test_lookup_is_cached_and_unknown_names_raise():
    assert theme_table["linux"] is theme_table["linux"]
    with pytest.raises(KeyError):
        theme_table["no-such-theme"]


# --------------------------------------------------------------------------
# building a Theme from data
# --------------------------------------------------------------------------


def test_token_path_resolution():
    assert token_from_str("Prompt.Continuation.L1") is Token.Prompt.Continuation.L1
    # a leading `Token.` is tolerated, and the empty path is the root token
    assert token_from_str("Token.Name.Function") is Token.Name.Function
    assert token_from_str("") is Token


@pytest.mark.parametrize(
    "path",
    [
        "__class__",
        "__class__.__base__",
        "split.__globals__",  # would reach the pygments module globals
        "Prompt.count",
        "Prompt.subtypes",
        "Prompt.__class__",
        "prompt",
    ],
)
def test_non_token_paths_are_rejected(path):
    """A theme file must not be able to walk off the token graph."""
    with pytest.raises(ValueError, match="does not name a pygments token"):
        token_from_str(path)
    with pytest.raises(ValueError, match="does not name a pygments token"):
        Theme.from_dict({"name": "evil", "extra_style": {path: "ansired"}})


def test_from_dict_defaults():
    theme = Theme.from_dict({"name": "minimal"})
    assert (theme.base, theme.extra_style) == (None, {})
    assert theme.symbols["arrow_head"] == ">"


def test_from_file(tmp_path):
    path = tmp_path / "custom.json"
    path.write_text(
        json.dumps(
            {
                "name": "custom",
                "base": "default",
                "extra_style": {"Prompt": "ansigreen"},
                "symbols": {"arrow_head": "!"},
            }
        )
    )
    theme = Theme.from_file(path)
    assert theme.base == "default"
    assert theme.extra_style == {Token.Prompt: "ansigreen"}
    assert theme.symbols["arrow_head"] == "!"
    # unspecified symbols still fall back to the defaults
    assert theme.symbols["top_line"] == "-"


# --------------------------------------------------------------------------
# symbols are written to the terminal, so they must be inert
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "symbol",
    [
        ESCAPE,  # OSC, sets the window title
        "\x1b[2J",  # CSI, clears the screen
        "\x1b]52;c;cHduZWQ=\x07",  # OSC 52, writes the clipboard
        "\a",  # BEL
        "\n",
        "\r",
        "\t",
        BIDI_OVERRIDE,
        "\u200e",  # LEFT-TO-RIGHT MARK, invisible
        "x" * (MAX_SYMBOL_LENGTH + 1),
        5,  # not a string at all
    ],
)
def test_unsafe_symbols_are_refused(symbol):
    with pytest.raises(ValueError, match="symbol 'arrow_head' of theme 'evil'"):
        Theme("evil", None, {}, symbols={"arrow_head": symbol})


@pytest.mark.parametrize(
    "symbol",
    [
        "\u25b6",  # BLACK RIGHT-POINTING TRIANGLE, the shipped arrow head
        "\u2500",  # BOX DRAWINGS LIGHT HORIZONTAL, the shipped top line
        PRIVATE_USE,
        NERD_FONT,
        ">",
        " ",
        "",  # no symbol at all
        "e\u0301",  # a combining acute, so two code points for one glyph
        "x" * MAX_SYMBOL_LENGTH,
    ],
)
def test_printable_symbols_are_accepted(symbol):
    assert (
        Theme("ok", None, {}, symbols={"arrow_head": symbol}).symbols["arrow_head"]
        == symbol
    )


def test_the_unicode_fixtures_are_what_they_claim():
    """The characters above are invisible, so assert they survived being typed.

    They have been silently stripped by tooling before now, which left the
    cases using them passing while testing nothing.
    """
    assert unicodedata.category(BIDI_OVERRIDE) == "Cf"
    assert unicodedata.category(PRIVATE_USE) == "Co"
    assert unicodedata.category(NERD_FONT) == "Co"
    # and the private use ones are exactly why `str.isprintable()` is not the
    # check `_validate_symbols` uses: it would reject them
    assert not PRIVATE_USE.isprintable()
    assert not NERD_FONT.isprintable()


def test_symbols_are_checked_whatever_key_they_arrive_under():
    with pytest.raises(ValueError, match="symbol 'future_symbol'"):
        Theme("evil", None, {}, symbols={"future_symbol": ESCAPE})


# --------------------------------------------------------------------------
# themes IPython does not ship: the IPython directory and entry points
# --------------------------------------------------------------------------


@pytest.mark.parametrize("source", SOURCES)
def test_theme_is_found_and_named_after_its_file(themes, source):
    themes.add(source, "my-theme", {"name": "ignored", "base": "default"})
    theme = themes.table["my-theme"]
    # the name it is looked up by wins over whatever the file calls itself
    assert (theme.name, theme.base) == ("my-theme", "default")
    assert "my-theme" in list(themes.table)
    assert themes.table["my-theme"] is theme


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize(
    "data, raw, match",
    [
        (None, "{not json", "could not read theme 'bad'"),
        ({"extra_style": {"__class__": "ansired"}}, None, "not name a pygments token"),
        ({"symbols": {"arrow_head": ESCAPE}}, None, "symbol 'arrow_head'"),
        ({"symbols": {"arrow_head": "x" * 21}}, None, f"at most {MAX_SYMBOL_LENGTH}"),
    ],
    ids=["invalid-json", "bad-token", "escape-sequence", "over-long-symbol"],
)
def test_bad_theme_is_refused_with_a_warning(themes, source, data, raw, match):
    themes.add(source, "bad", data, raw=raw)
    _assert_refused(themes.table, "bad", match)


def test_bundled_themes_cannot_be_shadowed(themes):
    for source in SOURCES:
        themes.add(source, "linux", {"base": "default"})
    assert themes.table["linux"].base == "monokai"


def test_user_theme_wins_over_an_installed_one(themes):
    themes.add("user", "both", {"base": "default"})
    themes.add("installed", "both", {"base": "pastie"})
    assert themes.table["both"].base == "default"


# entry points ------------------------------------------------------------


@pytest.mark.parametrize("subdir", [None, "data", "data.deep"])
def test_entry_point_chooses_where_the_themes_live(themes, subdir):
    """`pkg:sub.dir` puts the themes in `pkg/sub/dir/`, package or not."""
    themes.add("installed", "ep", {"base": "default"}, subdir=subdir)
    assert themes.table["ep"].base == "default"


def test_entry_point_theme_name_may_contain_a_colon(themes):
    """`:` in a theme name maps to `-` in the file name, as for built-ins."""
    themes.add("installed", "solarized:light", {"base": "default"})
    assert themes.table["solarized:light"].base == "default"


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({}, "fake_themes/ep.json"),
        ({"subdir": "nowhere"}, "fake_themes/nowhere/ep.json"),
        ({"module": "no_such_package"}, "could not read theme 'ep'"),
    ],
    ids=["missing-file", "missing-subdirectory", "unimportable-package"],
)
def test_unreadable_entry_point_is_refused(themes, kwargs, match):
    themes.add("installed", "ep", **kwargs)
    _assert_refused(themes.table, "ep", match)


# the IPython directory ---------------------------------------------------


def test_user_theme_added_during_a_session_is_found(themes):
    with pytest.raises(KeyError):
        themes.table["late"]
    themes.add("user", "late", {"base": "default"})
    assert themes.table["late"].base == "default"


def _unlocatable():
    raise RuntimeError("no home directory")


@pytest.mark.parametrize(
    "get_ipython_dir",
    [lambda: "/nonexistent-ipython-dir", _unlocatable],
    ids=["missing-directory", "unlocatable-directory"],
)
def test_a_useless_ipython_dir_is_not_an_error(monkeypatch, get_ipython_dir):
    monkeypatch.setattr("IPython.paths.get_ipython_dir", get_ipython_dir)
    table = ThemeTable()
    assert table._get_user_themes() == {}
    assert table["linux"].base == "monokai"


def test_the_ipython_dir_is_resolved_only_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "IPython.paths.get_ipython_dir",
        lambda: (calls.append(1), "/nonexistent-ipython-dir")[1],
    )
    table = ThemeTable()
    for _ in range(3):
        table._get_user_themes()
    assert len(calls) == 1


# --------------------------------------------------------------------------
# laziness and confinement
# --------------------------------------------------------------------------


def test_listing_does_not_load_themes():
    table = ThemeTable()
    table._entry_points = {}
    assert list(table) == list(_BUILTIN_THEMES)
    assert table._by_name == {}


def test_a_builtin_lookup_scans_nothing(monkeypatch):
    monkeypatch.setattr("IPython.paths.get_ipython_dir", pytest.fail)
    table = ThemeTable()
    assert table["linux"].base == "monokai"
    assert table._entry_points is None


@pytest.mark.parametrize(
    "name", ["../../../etc/passwd", "..", ".", "a/b", "a\\b", ".hidden", ""]
)
def test_theme_names_cannot_escape_their_package(name, themes):
    """A theme name becomes a file name, so it must not name a directory."""
    with pytest.raises(ValueError, match="not a usable theme name"):
        _theme_filename(name)
    themes.table._entry_points = {name: _FakeEntryPoint(name, "fake_themes")}
    _assert_refused(themes.table, name, "not a usable theme name")


@pytest.mark.parametrize(
    "stem",
    [
        "my theme",
        "..",
        ".hidden",
        # `:` is legal in a theme name but maps to `-` in the file name, so a
        # file that keeps the `:` is not a theme. Windows cannot name such a
        # file in the first place.
        pytest.param(
            "a:b",
            marks=pytest.mark.skipif(
                os.name == "nt", reason="cannot create a file with ':' in the name"
            ),
        ),
    ],
)
def test_user_files_that_cannot_be_theme_names_are_ignored(themes, stem, ipython_dir):
    """A theme in the IPython directory is named by its file, so the file name
    has to be a name a theme could have."""
    (ipython_dir / f"{stem}.json").write_text("{}", encoding="utf-8")
    assert stem not in list(themes.table)
    with pytest.raises(KeyError):
        themes.table[stem]

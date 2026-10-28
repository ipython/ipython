import json
import keyword
import os
import re
import sys
import token
import tokenize
import warnings
from collections.abc import Iterator, Mapping
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

import pygments
from pygments.style import Style
from pygments.token import Token, _TokenType

from typing import TypedDict

if TYPE_CHECKING:
    # importing this drags in the whole `pygments.formatters` package, which
    # is only needed once something is actually formatted -- see
    # Theme._get_formatter below.
    from pygments.formatters.terminal256 import Terminal256Formatter


TokenStream: TypeAlias = list[tuple[_TokenType, str]]


__all__ = ["Parser", "Theme", "theme_table"]


# Pygments spells every token name with a leading capital, and uses that to
# decide whether an attribute access means "give me this subtoken"; see
# `pygments.token._TokenType.__getattr__`. Requiring the same of every segment
# we resolve means a theme file can only ever name a token: a segment that
# would instead reach a real attribute of the token object -- `split`,
# `subtypes`, `__class__`, ... -- and from there walk off into unrelated
# objects is rejected before `getattr` sees it.
_TOKEN_PART_RE = re.compile(r"[A-Z]\w*\Z")


def token_from_str(dotted: str) -> _TokenType:
    """Resolve a dotted token path to a pygments token.

    ``"Prompt.Continuation.L1"`` gives ``Token.Prompt.Continuation.L1``. A
    leading ``Token.`` is accepted but not required, and the empty string maps
    to ``Token`` itself.

    Raises ValueError if `dotted` does not name a token.
    """
    tok = Token
    for part in dotted.split("."):
        if not part or part == "Token":
            continue
        if not _TOKEN_PART_RE.match(part):
            raise ValueError(
                f"{dotted!r} does not name a pygments token: {part!r} is not a "
                "token name, those start with a capital letter."
            )
        tok = getattr(tok, part)
    assert isinstance(tok, _TokenType)
    return tok


# Which ``pygments/styles/*.py`` module (and class in it) defines each of the
# builtin pygments styles the themes IPython ships use as a `Theme.base`.
#
# This is only a shortcut, never the source of truth: any name missing from
# here, and any entry that no longer resolves, falls back to pygments' own
# `get_style_by_name`, plugins and all. See `_pygments_base_styles`.
_BUILTIN_PYGMENTS_STYLES: dict[str, tuple[str, str]] = {
    "default": ("default", "DefaultStyle"),
    "gruvbox-dark": ("gruvbox", "GruvboxDarkStyle"),
    "monokai": ("monokai", "MonokaiStyle"),
    "pastie": ("pastie", "PastieStyle"),
}


def _exec_pygments_style_module(module: str, class_name: str) -> Any | None:
    """Read one style's ``styles`` mapping out of ``pygments/styles/<module>.py``.

    Returns None if pygments is not laid out as expected, leaving it to the
    caller to fall back to `pygments.styles.get_style_by_name`.

    The module is executed in isolation and deliberately *not* registered in
    `sys.modules`: registering a submodule of a package that is not itself
    imported breaks later ``import pygments.styles.<module>`` statements, and
    keeping `pygments.styles` unimported is the entire point. Style modules
    are pure data, so executing one twice is harmless, and nothing but the
    ``styles`` dict escapes this function.
    """
    from importlib.machinery import PathFinder
    from importlib.util import module_from_spec

    package = PathFinder.find_spec("pygments.styles", list(pygments.__path__))
    if package is None or package.submodule_search_locations is None:
        return None
    spec = PathFinder.find_spec(
        f"pygments.styles.{module}", list(package.submodule_search_locations)
    )
    if spec is None or spec.loader is None:
        return None
    style_module = module_from_spec(spec)
    try:
        spec.loader.exec_module(style_module)
        return getattr(style_module, class_name).styles
    except Exception:
        return None


def _pygments_base_styles(name: str) -> Any:
    """Return the token -> style-string mapping of a pygments style, by name.

    Equivalent to ``pygments.styles.get_style_by_name(name).styles``, which is
    all IPython ever wants from a base style, but able to answer for the
    handful of builtin styles IPython's own themes are based on without
    importing `pygments.styles`.

    Importing that package -- which importing any of its submodules does too --
    runs `pygments.plugin`, and with it `importlib.metadata` and `email`:
    roughly 10ms whose only purpose is to make third party *style plugins*
    findable by name. No theme IPython ships needs that, and this is on the
    startup path.
    """
    target = _BUILTIN_PYGMENTS_STYLES.get(name)
    if target is not None:
        styles = _exec_pygments_style_module(*target)
        if styles is not None:
            return styles

    from pygments.styles import get_style_by_name

    return get_style_by_name(name).styles


class Symbols(TypedDict):
    top_line: str
    arrow_body: str
    arrow_head: str


_default_symbols: Symbols = Symbols(
    top_line="-",
    arrow_body="-",
    arrow_head=">",
)

#: Longest a symbol may be. They are a single glyph in practice; the slack
#: leaves room for combining marks and multi code point emoji.
MAX_SYMBOL_LENGTH = 20

# Symbols are written straight to the terminal, and `make_arrow` repeats
# `arrow_body` besides, so nothing in them may be able to drive a terminal
# capability: an `ESC` would let a theme move the cursor, set the window title,
# or read back the clipboard. Reject the character categories an escape
# sequence is built from, plus the bidi overrides that can make a symbol
# misrepresent the text around it.
#
# `str.isprintable()` looks like the check to use here but is too strict: it
# also rejects the private use area, which is where Powerline separators and
# Nerd Font glyphs live, and those are exactly what a theme wants an arrow head
# to be.
_FORBIDDEN_SYMBOL_CATEGORIES = frozenset(
    {
        # The "other" categories, minus Co (private use, where Powerline and
        # Nerd Font glyphs live) and Cn (unassigned), which would make a
        # symbol's acceptance depend on how old the running Python's unicode
        # database is -- a new emoji is Cn until Python catches up:
        "Cc",  # control -- the C0 and C1 controls: ESC, BEL, CR, LF, ...
        "Cf",  # format -- invisible, affects how its neighbours are laid out:
        #                  the bidi overrides, zero width joiner, soft hyphen
        "Cs",  # surrogate -- half a code point; encoding one raises
        # The separators, minus Zs (space) which is allowed:
        "Zl",  # line separator -- U+2028
        "Zp",  # paragraph separator -- U+2029
    }
)


def _validate_symbols(theme_name: str, symbols: Mapping[str, Any]) -> None:
    """Check that symbols are inert text.

    Raises ValueError describing the offending symbol if they are not.
    """
    import unicodedata

    for key, value in symbols.items():
        problem = None
        if not isinstance(value, str):
            problem = f"is {type(value).__name__}, not a string"
        elif len(value) > MAX_SYMBOL_LENGTH:
            problem = (
                f"is {len(value)} characters long, "
                f"at most {MAX_SYMBOL_LENGTH} are allowed"
            )
        else:
            for char in value:
                if unicodedata.category(char) in _FORBIDDEN_SYMBOL_CATEGORIES:
                    problem = (
                        f"contains U+{ord(char):04X}, a "
                        f"{unicodedata.category(char)} character; symbols must "
                        "be printable so that they cannot drive the terminal"
                    )
                    break
        if problem is not None:
            raise ValueError(
                f"symbol {key!r} of theme {theme_name!r} {problem}: {value!r}"
            )


class Theme:
    name: str
    base: str | None
    extra_style: dict[_TokenType, str]
    symbols: Symbols

    def __init__(
        self,
        name: str,
        base: str | None,
        extra_style: dict[_TokenType, str],
        *,
        symbols: Symbols | None = None,
    ) -> None:
        self.name = name
        self.base = base
        self.extra_style = extra_style
        s: Symbols = symbols if symbols is not None else _default_symbols
        _validate_symbols(name, s)
        self.symbols = {**_default_symbols, **s}
        self._pygments_style: type[Style] | None = None
        self._formatter: Terminal256Formatter | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Theme":
        """Build a Theme from plain, JSON-compatible data.

        ``extra_style`` keys are dotted token paths (see
        :func:`token_from_str`) rather than pygments token objects, so a theme
        can be written as a data file instead of Python.
        """
        return cls(
            data["name"],
            data.get("base"),
            {
                token_from_str(key): value
                for key, value in data.get("extra_style", {}).items()
            },
            symbols=data.get("symbols"),
        )

    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "Theme":
        """Build a Theme from a JSON file."""
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def as_pygments_style(self) -> type[Style]:
        # Cached on the instance rather than with `functools.cache`, which
        # would key on `self` and so keep every Theme ever built alive.
        if self._pygments_style is not None:
            return self._pygments_style
        if self.base is not None:
            base_styles = _pygments_base_styles(self.base)
        else:
            base_styles = {}

        class MyStyle(Style):
            styles = {**base_styles, **self.extra_style}

        self._pygments_style = MyStyle
        return MyStyle

    def _get_formatter(self) -> "Terminal256Formatter":
        if self._formatter is None:
            from pygments.formatters.terminal256 import Terminal256Formatter

            self._formatter = Terminal256Formatter(style=self.as_pygments_style())
        return self._formatter

    def format(self, stream: TokenStream) -> str:
        return pygments.format(stream, self._get_formatter())

    def make_arrow(self, width: int) -> str:
        """generate the leading arrow in front of traceback or debugger"""
        if width >= 2:
            return (
                self.symbols["arrow_body"] * (width - 2)
                + self.symbols["arrow_head"]
                + " "
            )
        elif width == 1:
            return self.symbols["arrow_head"]
        return ""


generate_tokens = tokenize.generate_tokens


#############################################################################
### Python Source Parser (does Highlighting)
#############################################################################

_KEYWORD = token.NT_OFFSET + 1
_TEXT = token.NT_OFFSET + 2

# ****************************************************************************

_pygment_token_mapping: dict[int, _TokenType] = {
    token.NUMBER: Token.Literal.Number,
    token.OP: Token.Operator,
    token.STRING: Token.Literal.String,
    token.COMMENT: Token.Comment,
    token.NAME: Token.Name,
    token.ERRORTOKEN: Token.Error,
    _KEYWORD: Token.Keyword,
    _TEXT: Token.Text,
}

_THEME_DIR = Path(__file__).parent / "themes"

#: Entry point group third-party packages advertise extra themes in. The entry
#: point is named after the theme it provides, and its value says where the
#: theme's JSON file lives::
#:
#:     [project.entry-points."ipython.themes"]
#:     solarized-dark = "my_themes"            # my_themes/solarized-dark.json
#:     solarized-light = "my_themes:data"      # my_themes/data/solarized-light.json
#:
#: An entry point value may only match ``[\w.]+(:[\w.]+)?``, so neither half can
#: be a file path; the part before the ``:`` is the package, the part after is a
#: ``.``-separated subdirectory within it, and the file name comes from the
#: entry point name via `_theme_filename`.
THEME_ENTRY_POINT_GROUP = "ipython.themes"

#: Directory, inside the IPython directory, a user can drop theme JSON files in
#: to have them picked up by name. `~/.ipython/themes/my-theme.json` becomes the
#: `my-theme` theme.
USER_THEME_DIRNAME = "themes"


# A theme name becomes a file name, so it must not be able to name a directory
# or a parent of one: `..` and `/` in a name would otherwise let an entry point
# read a file from outside the package it claims to ship.
_SAFE_THEME_NAME_RE = re.compile(r"\w[\w.:-]*\Z")


def _theme_filename(name: str) -> str:
    """File name a theme called `name` is stored under.

    ``:`` is not usable in file names on all platforms, so it is spelled ``-``
    on disk: the ``neutral:posix`` theme lives in ``neutral-posix.json``.

    Raises ValueError if `name` cannot safely be used as a file name.
    """
    if not _SAFE_THEME_NAME_RE.match(name):
        raise ValueError(
            f"{name!r} is not a usable theme name: a theme name becomes a file "
            "name, so it may contain only letters, digits, '_', '-', '.' and "
            "':', and may not start with '.'"
        )
    return name.replace(":", "-") + ".json"


# Name a theme can be looked up by -> name of the theme actually loaded, which
# is also the file it is loaded from. All of these are aliases for themselves
# except `neutral`.
#
# Hack: the 'neutral' colours are not very visible on a dark background on
# Windows. Since Windows command prompts have a dark background by default, and
# relatively few users are likely to alter that, we will use the 'Linux' colours,
# designed for a dark background, as the default on Windows. Changing it here
# avoids affecting the prompt colours rendered by prompt_toolkit, where the
# neutral defaults do work OK.
_BUILTIN_THEMES: dict[str, str] = {
    # technically BW is not nocolor, we should have a no-style, style
    "nocolor": "nocolor",
    "linux": "linux",
    "neutral": "neutral:nt" if os.name == "nt" else "neutral:posix",
    "neutral:nt": "neutral:nt",
    "neutral:posix": "neutral:posix",
    "lightbg": "lightbg",
    "pride": "pride",
    "pride:l": "pride:l",
    "gruvbox-dark": "gruvbox-dark",
}


class ThemeTable(Mapping[str, Theme]):
    """Lazy, extensible mapping of theme name to :class:`Theme`.

    Built-in themes live as JSON next to this module and are only read and
    turned into pygments tokens the first time they are looked up.

    Beyond those, a theme can come from a JSON file dropped in ``themes/``
    inside the IPython directory, named after the file, or from a package
    advertising it in the ``ipython.themes`` entry point group.

    Built-in names win, so neither a stray file nor an installed package can
    silently redefine a shipped theme; a file in the IPython directory in turn
    wins over an installed package, being the more local of the two.
    """

    def __init__(self) -> None:
        self._by_name: dict[str, Theme] = {}
        self._entry_points: dict[str, Any] | None = None
        self._user_theme_dir: Path | None = None

    def _get_user_theme_dir(self) -> Path | None:
        """`themes/` inside the IPython directory, if it can be located."""
        if self._user_theme_dir is None:
            try:
                # Remembered once found: `get_ipython_dir` creates the IPython
                # directory, and falls back to a fresh temporary one when it
                # cannot, neither of which is worth repeating. Failing to find
                # it at all is rare enough to be worth simply retrying.
                from IPython.paths import get_ipython_dir

                self._user_theme_dir = Path(get_ipython_dir()) / USER_THEME_DIRNAME
            except Exception:
                return None
        return self._user_theme_dir

    def _get_user_themes(self) -> dict[str, Path]:
        """Theme name -> file, for themes dropped in the IPython directory.

        Listed afresh on each lookup rather than cached, so that a theme file
        added during a session is picked up without restarting.
        """
        directory = self._get_user_theme_dir()
        if directory is None:
            return {}
        try:
            paths = sorted(directory.glob("*.json"))
        except OSError:
            return {}
        # A theme is always stored as `_theme_filename` of its name, so a file
        # that is not is not a theme -- which keeps the name a theme is looked
        # up by and the file it lives in agreeing whichever way round they are
        # worked out.
        themes = {}
        for path in paths:
            try:
                if _theme_filename(path.stem) == path.name:
                    themes[path.stem] = path
            except ValueError:
                continue
        return themes

    @staticmethod
    def _from_user_file(name: str, path: Path) -> Theme:
        """Read a theme the user dropped in their IPython directory."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"could not read theme {name!r} from {path} ({e})") from e
        # The file name is what the theme is looked up by, so it wins over
        # whatever the file happens to call itself.
        return Theme.from_dict({**data, "name": name})

    def _get_entry_points(self) -> dict[str, Any]:
        # `importlib.metadata` has to walk `sys.path` to answer this, which
        # costs more than everything else in this module put together; only do
        # it once, and only once a lookup has actually missed the built-ins.
        if self._entry_points is None:
            from importlib.metadata import entry_points

            self._entry_points = {
                ep.name: ep for ep in entry_points(group=THEME_ENTRY_POINT_GROUP)
            }
        return self._entry_points

    @staticmethod
    def _from_entry_point(name: str, entry_point: Any) -> Theme:
        """Read the JSON file an entry point points at.

        The entry point value says where in which package the file lives;
        nothing from that package is executed, only its data is read.
        """
        from importlib.resources import files

        # `pkg:sub.dir` puts the themes in `pkg/sub/dir/`. Both halves of an
        # entry point value may only match `[\w.]+`, so neither can contain a
        # path separator or `..`, and the file name is checked by
        # `_theme_filename`; a theme can only ever name a file inside its own
        # package.
        subdirectories = entry_point.attr.split(".") if entry_point.attr else []
        relative = "/".join([*subdirectories, _theme_filename(name)])
        try:
            resource = files(entry_point.module)
            for part in subdirectories:
                resource = resource / part
            resource = resource / _theme_filename(name)
            data = json.loads(resource.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(
                f"could not read theme {name!r} from the "
                f"{THEME_ENTRY_POINT_GROUP} entry point {entry_point.value!r}: "
                f"expected {entry_point.module}/{relative} to be a "
                f"JSON theme file ({e})"
            ) from e
        # The entry point name is what the theme is looked up by, so it wins
        # over whatever the file happens to call itself.
        return Theme.from_dict({**data, "name": name})

    def __getitem__(self, name: str) -> Theme:
        if name in self._by_name:
            return self._by_name[name]
        if name in _BUILTIN_THEMES:
            filename = _theme_filename(_BUILTIN_THEMES[name])
            theme = Theme.from_file(_THEME_DIR / filename)
        else:
            user_themes = self._get_user_themes()
            entry_points = {} if name in user_themes else self._get_entry_points()
            if name not in user_themes and name not in entry_points:
                raise KeyError(name)
            try:
                if name in user_themes:
                    theme = self._from_user_file(name, user_themes[name])
                else:
                    theme = self._from_entry_point(name, entry_points[name])
            except ValueError as e:
                # These themes are data IPython did not ship; refuse the broken
                # or hostile ones rather than letting them fail somewhere far
                # from here, but say why, since the user did put them there.
                warnings.warn(f"Refusing to load theme {name!r}: {e}", stacklevel=2)
                raise KeyError(name) from e
        self._by_name[name] = theme
        return theme

    def __iter__(self) -> Iterator[str]:
        seen: set[str] = set()
        for name in (
            *_BUILTIN_THEMES,
            *self._get_user_themes(),
            *self._get_entry_points(),
        ):
            if name not in seen:
                seen.add(name)
                yield name

    def __len__(self) -> int:
        return sum(1 for _ in self)


theme_table = ThemeTable()


class Parser:
    """Format colored Python source."""

    _theme_name: str
    out: Any
    pos: int
    lines: list[int]
    raw: str

    def __init__(self, out: Any = sys.stdout, *, theme_name: str | None = None) -> None:
        """Create a parser with a specified color table and output channel.

        Call format() to process code.
        """

        assert theme_name is not None

        self.out = out
        self.pos = 0
        self.lines = []
        self.raw = ""
        if theme_name is not None:
            if theme_name in ["Linux", "LightBG", "Neutral", "NoColor"]:
                warnings.warn(
                    f"Theme names and color schemes are lowercase in IPython 9.0 use {theme_name.lower()} instead",
                    DeprecationWarning,
                    stacklevel=2,
                )
                theme_name = theme_name.lower()
        if not theme_name:
            self.theme_name = "nocolor"
        else:
            self.theme_name = theme_name

    @property
    def theme_name(self) -> str:
        return self._theme_name

    @theme_name.setter
    def theme_name(self, value: str) -> None:
        assert value == value.lower()
        self._theme_name = value

    @property
    def style(self) -> str:
        # `style` was renamed `theme_name`; this always raises to catch
        # leftover callers of the old name. Body kept only to satisfy the -> str
        # return type.
        assert False
        return self._theme_name  # type: ignore[unreachable]

    @style.setter
    def style(self, val: str) -> None:
        assert False
        assert val == val.lower()  # type: ignore[unreachable]
        self._theme_name = val

    def format(self, raw: str, out: Any = None) -> str | None:
        return self.format2(raw, out)[0]

    def format2(self, raw: str, out: Any = None) -> tuple[str | None, bool]:
        """Parse and send the colored source.

        If out is not specified, the defaults (given to constructor) are used.

        out should be a file-type object. Optionally, out can be given as the
        string 'str' and the parser will automatically return the output in a
        string."""

        string_output = 0
        if out == "str" or self.out == "str" or isinstance(self.out, StringIO):
            # XXX - I don't really like this state handling logic, but at this
            # point I don't want to make major changes, so adding the
            # isinstance() check is the simplest I can do to ensure correct
            # behavior.
            out_old = self.out
            self.out = StringIO()
            string_output = 1
        elif out is not None:
            self.out = out
        else:
            raise ValueError(
                '`out` or `self.out` should be file-like or the value `"str"`'
            )

        # Fast return of the unmodified input for nocolor scheme
        # TODO:
        if self.theme_name == "nocolor":
            error = False
            self.out.write(raw)
            if string_output:
                return raw, error
            return None, error

        # local shorthands

        # Remove trailing whitespace and normalize tabs
        self.raw = raw.expandtabs().rstrip()

        # store line offsets in self.lines
        self.lines = [0, 0]
        pos = 0
        raw_find = self.raw.find
        lines_append = self.lines.append
        while True:
            pos = raw_find("\n", pos) + 1
            if not pos:
                break
            lines_append(pos)
        lines_append(len(self.raw))

        # parse the source and write it
        self.pos = 0
        text = StringIO(self.raw)

        error = False
        try:
            for atoken in generate_tokens(text.readline):
                self(*atoken)
        except tokenize.TokenError as ex:
            msg = ex.args[0]
            line = ex.args[1][0]
            self.out.write(
                theme_table[self.theme_name].format(
                    [
                        (Token, "\n\n"),
                        (
                            Token.Error,
                            f"*** ERROR: {msg}{self.raw[self.lines[line] :]}",
                        ),
                        (Token, "\n"),
                    ]
                )
            )
            error = True
        self.out.write(
            theme_table[self.theme_name].format(
                [
                    (Token, "\n"),
                ]
            )
        )

        if string_output:
            output = self.out.getvalue()
            self.out = out_old
            return (output, error)
        return (None, error)

    def _inner_call_(
        self, toktype: int, toktext: str, start_pos: tuple[int, int]
    ) -> str:
        """like call but write to a temporary buffer"""
        srow, scol = start_pos

        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)

        # send the original whitespace, if needed
        if newpos > oldpos:
            acc = self.raw[oldpos:newpos]
        else:
            acc = ""

        # skip indenting tokens
        if toktype in [token.INDENT, token.DEDENT]:
            self.pos = newpos
            return acc

        # map token type to a color group
        if token.LPAR <= toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        pyg_tok_type = _pygment_token_mapping.get(toktype, Token.Text)

        # send text, pygments should take care of splitting on newline and resending
        # the correct self.colors after the new line, which is necessary for pagers
        acc += theme_table[self.theme_name].format([(pyg_tok_type, toktext)])
        return acc

    def __call__(
        self,
        toktype: int,
        toktext: str,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        line: str,
    ) -> None:
        """Token handler, with syntax highlighting."""
        self.out.write(self._inner_call_(toktype, toktext, start_pos))

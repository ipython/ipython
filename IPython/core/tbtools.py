from typing import Any, Optional, Tuple

from types import TracebackType

_sentinel = object()


class TBTools:
    """Basic tools used by all traceback printer classes."""

    # Number of frames to skip when reporting tracebacks
    tb_offset = 0
    _theme_name: str
    _old_theme_name: str

    def __init__(
        self,
        color_scheme: Any = _sentinel,
        call_pdb: bool = False,
        ostream: Any = None,
        *,
        debugger_cls: type | None = None,
        theme_name: str = "nocolor",
    ):
        if color_scheme is not _sentinel:
            assert isinstance(color_scheme, str), color_scheme
            warnings.warn(
                "color_scheme is deprecated since IPython 9.0, use theme_name instead, all lowercase",
                DeprecationWarning,
                stacklevel=2,
            )
            theme_name = color_scheme
        assert theme_name.lower() == theme_name, theme_name
        # Whether to call the interactive pdb debugger after printing
        # tracebacks or not
        super().__init__()
        self.call_pdb = call_pdb

        # Output stream to write to.  Note that we store the original value in
        # a private attribute and then make the public ostream a property, so
        # that we can delay accessing sys.stdout until runtime.  The way
        # things are written now, the sys.stdout object is dynamically managed
        # so a reference to it should NEVER be stored statically.  This
        # property approach confines this detail to a single location, and all
        # subclasses can simply access self.ostream for writing.
        self._ostream = ostream

        # Create color table
        self.set_theme_name(theme_name)
        self.debugger_cls = debugger_cls or debugger.Pdb

        if call_pdb:
            self.pdb = self.debugger_cls()
        else:
            self.pdb = None

    def _get_ostream(self) -> Any:
        """Output stream that exceptions are written to.

        Valid values are:

        - None: the default, which means that IPython will dynamically resolve
          to sys.stdout.  This ensures compatibility with most tools, including
          Windows (where plain stdout doesn't recognize ANSI escapes).

        - Any object with 'write' and 'flush' attributes.
        """
        return sys.stdout if self._ostream is None else self._ostream

    def _set_ostream(self, val) -> None:  # type:ignore[no-untyped-def]
        assert val is None or (hasattr(val, "write") and hasattr(val, "flush"))
        self._ostream = val

    ostream = property(_get_ostream, _set_ostream)

    @staticmethod
    def _get_chained_exception(exception_value: Any) -> Any:
        cause = getattr(exception_value, "__cause__", None)
        if cause:
            return cause
        if getattr(exception_value, "__suppress_context__", False):
            return None
        return getattr(exception_value, "__context__", None)

    def get_parts_of_chained_exception(
        self, evalue: BaseException | None
    ) -> Optional[Tuple[type, BaseException, TracebackType]]:
        chained_evalue = self._get_chained_exception(evalue)

        if chained_evalue:
            return (
                chained_evalue.__class__,
                chained_evalue,
                chained_evalue.__traceback__,
            )
        return None

    def prepare_chained_exception_message(
        self, cause: BaseException | None
    ) -> list[list[str]]:
        direct_cause = (
            "\nThe above exception was the direct cause of the following exception:\n"
        )
        exception_during_handling = (
            "\nDuring handling of the above exception, another exception occurred:\n"
        )

        if cause:
            message = [[direct_cause]]
        else:
            message = [[exception_during_handling]]
        return message

    @property
    def has_colors(self) -> bool:
        assert self._theme_name == self._theme_name.lower()
        return self._theme_name != "nocolor"

    def set_theme_name(self, name: str) -> None:
        assert name in theme_table
        assert name.lower() == name
        self._theme_name = name
        # Also set colors of debugger
        if hasattr(self, "pdb") and self.pdb is not None:
            self.pdb.set_theme_name(name)

    def set_colors(self, name: str) -> None:
        """Shorthand access to the color table scheme selector method."""

        # todo emit deprecation
        warnings.warn(
            "set_colors is deprecated since IPython 9.0, use set_theme_name instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.set_theme_name(name)

    def color_toggle(self) -> None:
        """Toggle between the currently active color scheme and nocolor."""
        if self._theme_name == "nocolor":
            self._theme_name = self._old_theme_name
        else:
            self._old_theme_name = self._theme_name
            self._theme_name = "nocolor"

    def stb2text(self, stb: list[str]) -> str:
        """Convert a structured traceback (a list) to a string."""
        return "\n".join(stb)

    def text(
        self,
        etype: type,
        value: BaseException | None,
        tb: TracebackType | None,
        tb_offset: Optional[int] = None,
        context: int = 5,
    ) -> str:
        """Return formatted traceback.

        Subclasses may override this if they add extra arguments.
        """
        tb_list = self.structured_traceback(etype, value, tb, tb_offset, context)
        return self.stb2text(tb_list)

    def structured_traceback(
        self,
        etype: type,
        evalue: BaseException | None,
        etb: Optional[TracebackType] = None,
        tb_offset: Optional[int] = None,
        context: int = 5,
    ) -> list[str]:
        """Return a list of traceback frames.

        Must be implemented by each class.
        """
        raise NotImplementedError()

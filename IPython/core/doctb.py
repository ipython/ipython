from .tbtools import TBTools, FrameInfo
from types import TracebackType

from typing import Any, Callable, Optional


class DocTB(TBTools):
    """

    A stripped down version of Verbose TB, simplified to not have too much information when
    running doctests

    """

    tb_highlight = "bg:ansiyellow"
    tb_highlight_style = "default"

    _mode: str

    def __init__(
        self,
        # TODO: no default ?
        theme_name: str = "linux",
        call_pdb: bool = False,
        ostream: Any = None,
        tb_offset: int = 0,
        long_header: bool = False,
        include_vars: bool = True,
        check_cache: Callable[[], None] | None = None,
        debugger_cls: type | None = None,
    ):
        """Specify traceback offset, headers and color scheme.

        Define how many frames to drop from the tracebacks. Calling it with
        tb_offset=1 allows use of this handler in interpreters which will have
        their own code at the top of the traceback (VerboseTB will first
        remove that frame before printing the traceback info)."""
        assert isinstance(theme_name, str)
        super().__init__(
            theme_name=theme_name,
            call_pdb=call_pdb,
            ostream=ostream,
            debugger_cls=debugger_cls,
        )
        self.tb_offset = tb_offset
        self.long_header = long_header
        self.include_vars = include_vars
        # By default we use linecache.checkcache, but the user can provide a
        # different check_cache implementation.  This was formerly used by the
        # IPython kernel for interactive code, but is no longer necessary.
        if check_cache is None:
            check_cache = linecache.checkcache
        self.check_cache = check_cache

        self.skip_hidden = True

    def format_record(self, frame_info: FrameInfo) -> str:
        """Format a single stack frame"""
        assert isinstance(frame_info, FrameInfo)

        if isinstance(frame_info._sd, stack_data.RepeatedFrames):
            return theme_table[self._theme_name].format(
                [
                    (Token, "    "),
                    (
                        Token.ExcName,
                        "[... skipping similar frames: %s]" % frame_info.description,
                    ),
                    (Token, "\n"),
                ]
            )

        indent: str = " " * INDENT_SIZE

        assert isinstance(frame_info.lineno, int)
        args, varargs, varkw, locals_ = inspect.getargvalues(frame_info.frame)
        if frame_info.executing is not None:
            func = frame_info.executing.code_qualname()
        else:
            func = "?"
        if func == "<module>":
            call = ""
        else:
            # Decide whether to include variable details or not
            var_repr = eqrepr if self.include_vars else nullrepr
            try:
                scope = inspect.formatargvalues(
                    args, varargs, varkw, locals_, formatvalue=var_repr
                )
                assert isinstance(scope, str)
                call = theme_table[self._theme_name].format(
                    [(Token, "in "), (Token.VName, func), (Token.ValEm, scope)]
                )
            except KeyError:
                # This happens in situations like errors inside generator
                # expressions, where local variables are listed in the
                # line, but can't be extracted from the frame.  I'm not
                # 100% sure this isn't actually a bug in inspect itself,
                # but since there's no info for us to compute with, the
                # best we can do is report the failure and move on.  Here
                # we must *not* call any traceback construction again,
                # because that would mess up use of %debug later on.  So we
                # simply report the failure and move on.  The only
                # limitation will be that this frame won't have locals
                # listed in the call signature.  Quite subtle problem...
                # I can't think of a good way to validate this in a unit
                # test, but running a script consisting of:
                #  dict( (k,v.strip()) for (k,v) in range(10) )
                # will illustrate the error, if this exception catch is
                # disabled.
                call = theme_table[self._theme_name].format(
                    [
                        (Token, "in "),
                        (Token.VName, func),
                        (Token.ValEm, "(***failed resolving arguments***)"),
                    ]
                )

        lvals_toks: list[TokenStream] = []
        if self.include_vars:
            try:
                # we likely want to fix stackdata at some point, but
                # still need a workaround.
                fibp = frame_info.variables_in_executing_piece
                for var in fibp:
                    lvals_toks.append(
                        [
                            (Token, var.name),
                            (Token, " "),
                            (Token.ValEm, "= "),
                            (Token.ValEm, repr(var.value)),
                        ]
                    )
            except Exception:
                lvals_toks.append(
                    [
                        (
                            Token,
                            "Exception trying to inspect frame. No more locals available.",
                        ),
                    ]
                )

        if frame_info._sd is None:
            # fast fallback if file is too long
            assert frame_info.filename is not None
            level_tokens = [
                (Token.FilenameEm, util_path.compress_user(frame_info.filename)),
                (Token, " "),
                (Token, call),
                (Token, "\n"),
            ]

            _line_format = Parser(theme_name=self._theme_name).format2
            assert isinstance(frame_info.code, types.CodeType)
            first_line: int = frame_info.code.co_firstlineno
            current_line: int = frame_info.lineno
            raw_lines: list[str] = frame_info.raw_lines
            index: int = current_line - first_line
            assert frame_info.context is not None
            if index >= frame_info.context:
                start = max(index - frame_info.context, 0)
                stop = index + frame_info.context
                index = frame_info.context
            else:
                start = 0
                stop = index + frame_info.context
            raw_lines = raw_lines[start:stop]

            # Jan 2025: may need _line_format(py3ompat.cast_unicode(s))
            raw_color_err = [(s, _line_format(s, "str")) for s in raw_lines]

            tb_tokens = _simple_format_traceback_lines(
                current_line,
                index,
                raw_color_err,
                lvals_toks,
                theme=theme_table[self._theme_name],
            )
            _tb_lines: str = theme_table[self._theme_name].format(tb_tokens)

            return theme_table[self._theme_name].format(level_tokens + tb_tokens)
        else:
            result = theme_table[self._theme_name].format(
                _tokens_filename(True, frame_info.filename, lineno=frame_info.lineno)
            )
            result += ", " if call else ""
            result += f"{call}\n"
            result += theme_table[self._theme_name].format(
                _format_traceback_lines(
                    frame_info.lines,
                    theme_table[self._theme_name],
                    self.has_colors,
                    lvals_toks,
                )
            )
            return result

    def prepare_header(self, etype: str, long_version: bool = False) -> str:
        width = min(75, get_terminal_size()[0])
        if long_version:
            # Header with the exception type, python version, and date
            pyver = "Python " + sys.version.split()[0] + ": " + sys.executable
            date = time.ctime(time.time())
            theme = theme_table[self._theme_name]
            head = theme.format(
                [
                    (Token.Topline, theme.symbols["top_line"] * width),
                    (Token, "\n"),
                    (Token.ExcName, etype),
                    (Token, " " * (width - len(etype) - len(pyver))),
                    (Token, pyver),
                    (Token, "\n"),
                    (Token, date.rjust(width)),
                ]
            )
            head += (
                "\nA problem occurred executing Python code.  Here is the sequence of function"
                "\ncalls leading up to the error, with the most recent (innermost) call last."
            )
        else:
            # Simplified header
            head = theme_table[self._theme_name].format(
                [
                    (Token.ExcName, etype),
                    (
                        Token,
                        "Traceback (most recent call last)".rjust(width - len(etype)),
                    ),
                ]
            )

        return head

    def format_exception(self, etype, evalue):
        # Get (safely) a string form of the exception info
        try:
            etype_str, evalue_str = map(str, (etype, evalue))
        except:
            # User exception is improperly defined.
            etype, evalue = str, sys.exc_info()[:2]
            etype_str, evalue_str = map(str, (etype, evalue))

        # PEP-678 notes
        notes = getattr(evalue, "__notes__", [])
        if not isinstance(notes, Sequence) or isinstance(notes, (str, bytes)):
            notes = [_safe_string(notes, "__notes__", func=repr)]

        # ... and format it
        return [
            theme_table[self._theme_name].format(
                [(Token.ExcName, etype_str), (Token, ": "), (Token, evalue_str)]
            ),
            *(
                theme_table[self._theme_name].format(
                    [(Token, _safe_string(py3compat.cast_unicode(n), "note"))]
                )
                for n in notes
            ),
        ]

    def format_exception_as_a_whole(
        self,
        etype: type,
        evalue: Optional[BaseException],
        etb: Optional[TracebackType],
        context: int,
        tb_offset: Optional[int],
    ) -> list[list[str]]:
        """Formats the header, traceback and exception message for a single exception.

        This may be called multiple times by Python 3 exception chaining
        (PEP 3134).
        """
        # some locals
        orig_etype = etype
        try:
            etype = etype.__name__  # type: ignore
        except AttributeError:
            pass

        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        assert isinstance(tb_offset, int)
        head = self.prepare_header(str(etype), self.long_header)
        records = self.get_records(etb, context, tb_offset) if etb else []

        frames = []
        skipped = 0
        lastrecord = len(records) - 1
        for i, record in enumerate(records):
            if (
                not isinstance(record._sd, stack_data.RepeatedFrames)
                and self.skip_hidden
            ):
                if (
                    record.frame.f_locals.get("__tracebackhide__", 0)
                    and i != lastrecord
                ):
                    skipped += 1
                    continue
            if skipped:
                frames.append(
                    theme_table[self._theme_name].format(
                        [
                            (Token, "    "),
                            (Token.ExcName, "[... skipping hidden %s frame]" % skipped),
                            (Token, "\n"),
                        ]
                    )
                )
                skipped = 0
            frames.append(self.format_record(record))
        if skipped:
            frames.append(
                theme_table[self._theme_name].format(
                    [
                        (Token, "    "),
                        (Token.ExcName, "[... skipping hidden %s frame]" % skipped),
                        (Token, "\n"),
                    ]
                )
            )

        formatted_exception = self.format_exception(etype, evalue)
        if records:
            frame_info = records[-1]
            ipinst = get_ipython()
            if ipinst is not None:
                ipinst.hooks.synchronize_with_editor(
                    frame_info.filename, frame_info.lineno, 0
                )

        return [[head] + frames + formatted_exception]

    def get_records(self, etb: TracebackType, context: int, tb_offset: int) -> Any:
        assert etb is not None
        context = context - 1
        after = context // 2
        before = context - after
        if self.has_colors:
            base_style = theme_table[self._theme_name].as_pygments_style()
            style = stack_data.style_with_executing_node(base_style, self.tb_highlight)
            formatter = Terminal256Formatter(style=style)
        else:
            formatter = None
        options = stack_data.Options(
            before=before,
            after=after,
            pygments_formatter=formatter,
        )

        # Let's estimate the amount of code we will have to parse/highlight.
        cf: Optional[TracebackType] = etb
        max_len = 0
        tbs = []
        while cf is not None:
            try:
                mod = inspect.getmodule(cf.tb_frame)
                if mod is not None:
                    mod_name = mod.__name__
                    root_name, *_ = mod_name.split(".")
                    if root_name == "IPython":
                        cf = cf.tb_next
                        continue
                max_len = get_line_number_of_frame(cf.tb_frame)

            except OSError:
                max_len = 0
            max_len = max(max_len, max_len)
            tbs.append(cf)
            cf = getattr(cf, "tb_next", None)

        if max_len > FAST_THRESHOLD:
            FIs: list[FrameInfo] = []
            for tb in tbs:
                frame = tb.tb_frame  # type: ignore
                lineno = frame.f_lineno
                code = frame.f_code
                filename = code.co_filename
                # TODO: Here we need to use before/after/
                FIs.append(
                    FrameInfo(
                        "Raw frame", filename, lineno, frame, code, context=context
                    )
                )
            return FIs
        res = list(stack_data.FrameInfo.stack_data(etb, options=options))[tb_offset:]
        res2 = [FrameInfo._from_stack_data_FrameInfo(r) for r in res]
        return res2

    def structured_traceback(
        self,
        etype: type,
        evalue: Optional[BaseException],
        etb: Optional[TracebackType] = None,
        tb_offset: Optional[int] = None,
        context: int = 5,
    ) -> list[str]:
        """Return a nice text document describing the traceback."""
        formatted_exceptions: list[list[str]] = self.format_exception_as_a_whole(
            etype, evalue, etb, context, tb_offset
        )

        termsize = min(75, get_terminal_size()[0])
        theme = theme_table[self._theme_name]
        head: str = theme.format(
            [
                (
                    Token.Topline,
                    theme.symbols["top_line"] * termsize,
                ),
            ]
        )
        structured_traceback_parts: list[str] = [head]
        chained_exceptions_tb_offset = 0
        lines_of_context = 3
        exception = self.get_parts_of_chained_exception(evalue)
        if exception:
            assert evalue is not None
            formatted_exceptions += self.prepare_chained_exception_message(
                evalue.__cause__
            )
            etype, evalue, etb = exception
        else:
            evalue = None
        chained_exc_ids = set()
        while evalue:
            formatted_exceptions += self.format_exception_as_a_whole(
                etype, evalue, etb, lines_of_context, chained_exceptions_tb_offset
            )
            exception = self.get_parts_of_chained_exception(evalue)

            if exception and id(exception[1]) not in chained_exc_ids:
                chained_exc_ids.add(
                    id(exception[1])
                )  # trace exception to avoid infinite 'cause' loop
                formatted_exceptions += self.prepare_chained_exception_message(
                    evalue.__cause__
                )
                etype, evalue, etb = exception
            else:
                evalue = None

        # we want to see exceptions in a reversed order:
        # the first exception should be on top
        for fx in reversed(formatted_exceptions):
            structured_traceback_parts += fx

        return structured_traceback_parts

    def debugger(self, force: bool = False) -> None:
        """Call up the pdb debugger if desired, always clean up the tb
        reference.

        Keywords:

          - force(False): by default, this routine checks the instance call_pdb
            flag and does not actually invoke the debugger if the flag is false.
            The 'force' option forces the debugger to activate even if the flag
            is false.

        If the call_pdb flag is set, the pdb interactive debugger is
        invoked. In all cases, the self.tb reference to the current traceback
        is deleted to prevent lingering references which hamper memory
        management.

        Note that each call to pdb() does an 'import readline', so if your app
        requires a special setup for the readline completers, you'll have to
        fix that by hand after invoking the exception handler."""

        if force or self.call_pdb:
            if self.pdb is None:
                self.pdb = self.debugger_cls()
            # the system displayhook may have changed, restore the original
            # for pdb
            display_trap = DisplayTrap(hook=sys.__displayhook__)
            with display_trap:
                self.pdb.reset()
                # Find the right frame so we don't pop up inside ipython itself
                if hasattr(self, "tb") and self.tb is not None:  # type: ignore[has-type]
                    etb = self.tb  # type: ignore[has-type]
                else:
                    etb = self.tb = sys.last_traceback
                while self.tb is not None and self.tb.tb_next is not None:
                    assert self.tb.tb_next is not None
                    self.tb = self.tb.tb_next
                if etb and etb.tb_next:
                    etb = etb.tb_next
                self.pdb.botframe = etb.tb_frame
                # last_value should be deprecated, but last-exc sometimme not set
                # please check why later and remove the getattr.
                exc = (
                    sys.last_value
                    if sys.version_info < (3, 12)
                    else getattr(sys, "last_exc", sys.last_value)
                )  # type: ignore[attr-defined]
                if exc:
                    self.pdb.interaction(None, exc)
                else:
                    self.pdb.interaction(None, etb)

        if hasattr(self, "tb"):
            del self.tb

    def handler(self, info=None):
        (etype, evalue, etb) = info or sys.exc_info()
        self.tb = etb
        ostream = self.ostream
        ostream.flush()
        ostream.write(self.text(etype, evalue, etb))  # type:ignore[arg-type]
        ostream.write("\n")
        ostream.flush()

    # Changed so an instance can just be called as VerboseTB_inst() and print
    # out the right info on its own.
    def __call__(self, etype=None, evalue=None, etb=None):
        """This hook can replace sys.excepthook (for Python 2.1 or higher)."""
        if etb is None:
            self.handler()
        else:
            self.handler((etype, evalue, etb))
        try:
            self.debugger()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")

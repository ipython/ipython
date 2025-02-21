"""
Verbose and colourful traceback formatting.

**ColorTB**

I've always found it a bit hard to visually parse tracebacks in Python.  The
ColorTB class is a solution to that problem.  It colors the different parts of a
traceback in a manner similar to what you would expect from a syntax-highlighting
text editor.

Installation instructions for ColorTB::

    import sys,ultratb
    sys.excepthook = ultratb.ColorTB()

**VerboseTB**

I've also included a port of Ka-Ping Yee's "cgitb.py" that produces all kinds
of useful info when a traceback occurs.  Ping originally had it spit out HTML
and intended it for CGI programmers, but why should they have all the fun?  I
altered it to spit out colored text to the terminal.  It's a bit overwhelming,
but kind of neat, and maybe useful for long-running programs that you believe
are bug-free.  If a crash *does* occur in that type of program you want details.
Give it a shot--you'll love it or you'll hate it.

.. note::

  The Verbose mode prints the variables currently visible where the exception
  happened (shortening their strings if too long). This can potentially be
  very slow, if you happen to have a huge data structure whose string
  representation is complex to compute. Your computer may appear to freeze for
  a while with cpu usage at 100%. If this occurs, you can cancel the traceback
  with Ctrl-C (maybe hitting it more than once).

  If you encounter this kind of situation often, you may want to use the
  Verbose_novars mode instead of the regular Verbose, which avoids formatting
  variables (but otherwise includes the information and context given by
  Verbose).

.. note::

  The verbose mode print all variables in the stack, which means it can
  potentially leak sensitive information like access keys, or unencrypted
  password.

Installation instructions for VerboseTB::

    import sys,ultratb
    sys.excepthook = ultratb.VerboseTB()

Note:  Much of the code in this module was lifted verbatim from the standard
library module 'traceback.py' and Ka-Ping Yee's 'cgitb.py'.


Inheritance diagram:

.. inheritance-diagram:: IPython.core.ultratb
   :parts: 3
"""

# *****************************************************************************
# Copyright (C) 2001 Nathaniel Gray <n8gray@caltech.edu>
# Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
# Distributed under the terms of the BSD License.  The full license is in
# the file COPYING, distributed as part of this software.
# *****************************************************************************

import functools
import inspect
import linecache
import sys
import time
import traceback
import types
import warnings
from collections.abc import Sequence
from types import TracebackType
from typing import Any, Callable, List, Optional, Tuple

import stack_data
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.token import Token

from IPython import get_ipython
from IPython.utils import path as util_path
from IPython.utils import py3compat
from IPython.utils.PyColorize import Parser, Theme, TokenStream, theme_table
from IPython.utils.terminal import get_terminal_size

from .display_trap import DisplayTrap
from .doctb import DocTB
from .tbtools import (
    FrameInfo,
    TBTools,
    _format_traceback_lines,
    _safe_string,
    _simple_format_traceback_lines,
    _tokens_filename,
    eqrepr,
    get_line_number_of_frame,
    nullrepr,
    text_repr,
)

# Globals
# amount of space to put line numbers before verbose tracebacks
INDENT_SIZE = 8

# When files are too long do not use stackdata to get frames.
# it is too long.
FAST_THRESHOLD = 10_000


# ---------------------------------------------------------------------------
class ListTB(TBTools):
    """Print traceback information from a traceback list, with optional color.

    Calling requires 3 arguments: (etype, evalue, elist)
    as would be obtained by::

      etype, evalue, tb = sys.exc_info()
      if tb:
        elist = traceback.extract_tb(tb)
      else:
        elist = None

    It can thus be used by programs which need to process the traceback before
    printing (such as console replacements based on the code module from the
    standard library).

    Because they are meant to be called without a full traceback (only a
    list), instances of this class can't call the interactive pdb debugger."""

    def __call__(
        self,
        etype: type[BaseException],
        evalue: BaseException | None,
        etb: TracebackType | None,
    ) -> None:
        self.ostream.flush()
        self.ostream.write(self.text(etype, evalue, etb))
        self.ostream.write("\n")

    def _extract_tb(self, tb: TracebackType | None) -> traceback.StackSummary | None:
        if tb:
            return traceback.extract_tb(tb)
        else:
            return None

    def structured_traceback(
        self,
        etype: type,
        evalue: Optional[BaseException],
        etb: Optional[TracebackType] = None,
        tb_offset: Optional[int] = None,
        context: int = 5,
    ) -> list[str]:
        """Return a color formatted string with the traceback info.

        Parameters
        ----------
        etype : exception type
            Type of the exception raised.
        evalue : object
            Data stored in the exception
        etb : list | TracebackType | None
            If list: List of frames, see class docstring for details.
            If Traceback: Traceback of the exception.
        tb_offset : int, optional
            Number of frames in the traceback to skip.  If not given, the
            instance evalue is used (set in constructor).
        context : int, optional
            Number of lines of context information to print.

        Returns
        -------
        String with formatted exception.
        """
        # This is a workaround to get chained_exc_ids in recursive calls
        # etb should not be a tuple if structured_traceback is not recursive
        if isinstance(etb, tuple):
            etb, chained_exc_ids = etb
        else:
            chained_exc_ids = set()
        elist: list[Any]
        if isinstance(etb, list):
            elist = etb
        elif etb is not None:
            elist = self._extract_tb(etb)  # type: ignore[assignment]
        else:
            elist = []
        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        assert isinstance(tb_offset, int)
        out_list: list[str] = []
        if elist:
            if tb_offset and len(elist) > tb_offset:
                elist = elist[tb_offset:]

            out_list.append(
                theme_table[self._theme_name].format(
                    [
                        (Token, "Traceback"),
                        (Token, " "),
                        (Token.NormalEm, "(most recent call last)"),
                        (Token, ":"),
                        (Token, "\n"),
                    ]
                ),
            )
            out_list.extend(self._format_list(elist))
        # The exception info should be a single entry in the list.
        lines = "".join(self._format_exception_only(etype, evalue))
        out_list.append(lines)

        # Find chained exceptions if we have a traceback (not for exception-only mode)
        if etb is not None:
            exception = self.get_parts_of_chained_exception(evalue)

            if exception and (id(exception[1]) not in chained_exc_ids):
                chained_exception_message: list[str] = (
                    self.prepare_chained_exception_message(evalue.__cause__)[0]
                    if evalue is not None
                    else [""]
                )
                etype, evalue, etb = exception
                # Trace exception to avoid infinite 'cause' loop
                chained_exc_ids.add(id(exception[1]))
                chained_exceptions_tb_offset = 0
                ol1 = self.structured_traceback(
                    etype,
                    evalue,
                    (etb, chained_exc_ids),  # type: ignore
                    chained_exceptions_tb_offset,
                    context,
                )
                ol2 = chained_exception_message

                out_list = ol1 + ol2 + out_list

        return out_list

    def _format_list(self, extracted_list: list[Any]) -> list[str]:
        """Format a list of traceback entry tuples for printing.

        Given a list of tuples as returned by extract_tb() or
        extract_stack(), return a list of strings ready for printing.
        Each string in the resulting list corresponds to the item with the
        same index in the argument list.  Each string ends in a newline;
        the strings may contain internal newlines as well, for those items
        whose source text line is not None.

        Lifted almost verbatim from traceback.py
        """

        output_list = []
        for ind, (filename, lineno, name, line) in enumerate(extracted_list):
            # Will emphasize the last entry
            em = True if ind == len(extracted_list) - 1 else False

            item = theme_table[self._theme_name].format(
                [(Token.NormalEm if em else Token.Normal, "  ")]
                + _tokens_filename(em, filename, lineno=lineno)
            )

            # This seem to be only in xmode plain (%run sinpleer), investigate why not share with verbose.
            # look at _tokens_filename in forma_record.
            if name != "<module>":
                item += theme_table[self._theme_name].format(
                    [
                        (Token.NormalEm if em else Token.Normal, " in "),
                        (Token.TB.NameEm if em else Token.TB.Name, name),
                    ]
                )
            item += theme_table[self._theme_name].format(
                [(Token.NormalEm if em else Token, "\n")]
            )
            if line:
                item += theme_table[self._theme_name].format(
                    [
                        (Token.Line if em else Token, "    "),
                        (Token.Line if em else Token, line.strip()),
                        (Token, "\n"),
                    ]
                )
            output_list.append(item)

        return output_list

    def _format_exception_only(
        self, etype: type[BaseException], value: BaseException | None
    ) -> list[str]:
        """Format the exception part of a traceback.

        The arguments are the exception type and value such as given by
        sys.exc_info()[:2]. The return value is a list of strings, each ending
        in a newline.  Normally, the list contains a single string; however,
        for SyntaxError exceptions, it contains several lines that (when
        printed) display detailed information about where the syntax error
        occurred.  The message indicating which exception occurred is the
        always last string in the list.

        Also lifted nearly verbatim from traceback.py
        """
        have_filedata = False
        output_list = []
        stype_tokens = [(Token.ExcName, etype.__name__)]
        stype: str = theme_table[self._theme_name].format(stype_tokens)
        if value is None:
            # Not sure if this can still happen in Python 2.6 and above
            output_list.append(stype + "\n")
        else:
            if issubclass(etype, SyntaxError):
                assert hasattr(value, "filename")
                assert hasattr(value, "lineno")
                assert hasattr(value, "text")
                assert hasattr(value, "offset")
                assert hasattr(value, "msg")
                have_filedata = True
                if not value.filename:
                    value.filename = "<string>"
                if value.lineno:
                    lineno = value.lineno
                    textline = linecache.getline(value.filename, value.lineno)
                else:
                    lineno = "unknown"
                    textline = ""
                output_list.append(
                    theme_table[self._theme_name].format(
                        [(Token, "  ")]
                        + _tokens_filename(
                            True,
                            value.filename,
                            lineno=(None if lineno == "unknown" else lineno),
                        )
                        + [(Token, "\n")]
                    )
                )
                if textline == "":
                    textline = py3compat.cast_unicode(value.text, "utf-8")

                if textline is not None:
                    i = 0
                    while i < len(textline) and textline[i].isspace():
                        i += 1
                    output_list.append(
                        theme_table[self._theme_name].format(
                            [
                                (Token.Line, "    "),
                                (Token.Line, textline.strip()),
                                (Token, "\n"),
                            ]
                        )
                    )
                    if value.offset is not None:
                        s = "    "
                        for c in textline[i : value.offset - 1]:
                            if c.isspace():
                                s += c
                            else:
                                s += " "
                        output_list.append(
                            theme_table[self._theme_name].format(
                                [(Token.Caret, s + "^"), (Token, "\n")]
                            )
                        )

            try:
                assert hasattr(value, "msg")
                s = value.msg
            except Exception:
                s = self._some_str(value)
            if s:
                output_list.append(
                    theme_table[self._theme_name].format(
                        stype_tokens
                        + [
                            (Token.ExcName, ":"),
                            (Token, " "),
                            (Token, s),
                            (Token, "\n"),
                        ]
                    )
                )
            else:
                output_list.append("%s\n" % stype)

            # PEP-678 notes
            output_list.extend(f"{x}\n" for x in getattr(value, "__notes__", []))

        # sync with user hooks
        if have_filedata:
            ipinst = get_ipython()
            if ipinst is not None:
                assert value is not None
                assert hasattr(value, "lineno")
                assert hasattr(value, "filename")
                ipinst.hooks.synchronize_with_editor(value.filename, value.lineno, 0)

        return output_list

    def get_exception_only(self, etype, value):
        """Only print the exception type and message, without a traceback.

        Parameters
        ----------
        etype : exception type
        value : exception value
        """
        return ListTB.structured_traceback(self, etype, value)

    def show_exception_only(
        self, etype: BaseException | None, evalue: TracebackType | None
    ) -> None:
        """Only print the exception type and message, without a traceback.

        Parameters
        ----------
        etype : exception type
        evalue : exception value
        """
        # This method needs to use __call__ from *this* class, not the one from
        # a subclass whose signature or behavior may be different
        ostream = self.ostream
        ostream.flush()
        ostream.write("\n".join(self.get_exception_only(etype, evalue)))
        ostream.flush()

    def _some_str(self, value: Any) -> str:
        # Lifted from traceback.py
        try:
            return py3compat.cast_unicode(str(value))
        except:
            return "<unprintable %s object>" % type(value).__name__


# ----------------------------------------------------------------------------
class VerboseTB(TBTools):
    """A port of Ka-Ping Yee's cgitb.py module that outputs color text instead
    of HTML.  Requires inspect and pydoc.  Crazy, man.

    Modified version which optionally strips the topmost entries from the
    traceback, to be used with alternate interpreters (because their own code
    would appear in the traceback)."""

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


# ----------------------------------------------------------------------------
class FormattedTB(VerboseTB, ListTB):
    """Subclass ListTB but allow calling with a traceback.

    It can thus be used as a sys.excepthook for Python > 2.1.

    Also adds 'Context' and 'Verbose' modes, not available in ListTB.

    Allows a tb_offset to be specified. This is useful for situations where
    one needs to remove a number of topmost frames from the traceback (such as
    occurs with python programs that themselves execute other python code,
    like Python shells)."""

    mode: str

    def __init__(
        self,
        mode="Plain",
        # TODO: no default
        theme_name="linux",
        call_pdb=False,
        ostream=None,
        tb_offset=0,
        long_header=False,
        include_vars=False,
        check_cache=None,
        debugger_cls=None,
    ):
        # NEVER change the order of this list. Put new modes at the end:
        self.valid_modes = ["Plain", "Context", "Verbose", "Minimal", "Docs"]
        self.verbose_modes = self.valid_modes[1:3]

        VerboseTB.__init__(
            self,
            theme_name=theme_name,
            call_pdb=call_pdb,
            ostream=ostream,
            tb_offset=tb_offset,
            long_header=long_header,
            include_vars=include_vars,
            check_cache=check_cache,
            debugger_cls=debugger_cls,
        )

        # Different types of tracebacks are joined with different separators to
        # form a single string.  They are taken from this dict
        self._join_chars = dict(
            Plain="", Context="\n", Verbose="\n", Minimal="", Docs=""
        )
        # set_mode also sets the tb_join_char attribute
        self.set_mode(mode)

    def structured_traceback(
        self,
        etype: type,
        evalue: BaseException | None,
        etb: TracebackType | None = None,
        tb_offset: int | None = None,
        context: int = 5,
    ) -> list[str]:
        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        mode = self.mode
        if mode in self.verbose_modes:
            # Verbose modes need a full traceback
            return VerboseTB.structured_traceback(
                self, etype, evalue, etb, tb_offset, context
            )
        elif mode == "Docs":
            # return DocTB
            return DocTB(
                theme_name=self._theme_name,
                call_pdb=self.call_pdb,
                ostream=self.ostream,
                tb_offset=tb_offset,
                long_header=self.long_header,
                include_vars=self.include_vars,
                check_cache=self.check_cache,
                debugger_cls=self.debugger_cls,
            ).structured_traceback(etype, evalue, etb, tb_offset, 1)  # type: ignore[arg-type]

        elif mode == "Minimal":
            return ListTB.get_exception_only(self, etype, evalue)
        else:
            # We must check the source cache because otherwise we can print
            # out-of-date source code.
            self.check_cache()
            # Now we can extract and format the exception
            return ListTB.structured_traceback(
                self, etype, evalue, etb, tb_offset, context
            )

    def stb2text(self, stb: list[str]) -> str:
        """Convert a structured traceback (a list) to a string."""
        return self.tb_join_char.join(stb)

    def set_mode(self, mode: Optional[str] = None) -> None:
        """Switch to the desired mode.

        If mode is not specified, cycles through the available modes."""

        if not mode:
            new_idx = (self.valid_modes.index(self.mode) + 1) % len(self.valid_modes)
            self.mode = self.valid_modes[new_idx]
        elif mode not in self.valid_modes:
            raise ValueError(
                "Unrecognized mode in FormattedTB: <" + mode + ">\n"
                "Valid modes: " + str(self.valid_modes)
            )
        else:
            assert isinstance(mode, str)
            self.mode = mode
        # include variable details only in 'Verbose' mode
        self.include_vars = self.mode == self.valid_modes[2]
        # Set the join character for generating text tracebacks
        self.tb_join_char = self._join_chars[self.mode]

    # some convenient shortcuts
    def plain(self) -> None:
        self.set_mode(self.valid_modes[0])

    def context(self) -> None:
        self.set_mode(self.valid_modes[1])

    def verbose(self) -> None:
        self.set_mode(self.valid_modes[2])

    def minimal(self) -> None:
        self.set_mode(self.valid_modes[3])


# ----------------------------------------------------------------------------
class AutoFormattedTB(FormattedTB):
    """A traceback printer which can be called on the fly.

    It will find out about exceptions by itself.

    A brief example::

        AutoTB = AutoFormattedTB(mode = 'Verbose', theme_name='linux')
        try:
          ...
        except:
          AutoTB()  # or AutoTB(out=logfile) where logfile is an open file object
    """

    def __call__(
        self,
        etype: type | None = None,
        evalue: BaseException | None = None,
        etb: TracebackType | None = None,
        out: Any = None,
        tb_offset: int | None = None,
    ) -> None:
        """Print out a formatted exception traceback.

        Optional arguments:
          - out: an open file-like object to direct output to.

          - tb_offset: the number of frames to skip over in the stack, on a
          per-call basis (this overrides temporarily the instance's tb_offset
          given at initialization time."""

        if out is None:
            out = self.ostream
        out.flush()
        out.write(self.text(etype, evalue, etb, tb_offset))  # type:ignore[arg-type]
        out.write("\n")
        out.flush()
        # FIXME: we should remove the auto pdb behavior from here and leave
        # that to the clients.
        try:
            self.debugger()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")

    def structured_traceback(
        self,
        etype: type,
        evalue: Optional[BaseException],
        etb: Optional[TracebackType] = None,
        tb_offset: Optional[int] = None,
        context: int = 5,
    ) -> list[str]:
        # tb: TracebackType or tupleof tb types ?
        if etype is None:
            etype, evalue, etb = sys.exc_info()
        if isinstance(etb, tuple):
            # tb is a tuple if this is a chained exception.
            self.tb = etb[0]
        else:
            self.tb = etb
        return FormattedTB.structured_traceback(
            self, etype, evalue, etb, tb_offset, context
        )


# ---------------------------------------------------------------------------


# A simple class to preserve Nathan's original functionality.
class ColorTB(FormattedTB):
    """Deprecated since IPython 9.0."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Deprecated since IPython 9.0 use FormattedTB directly ColorTB is just an alias",
            DeprecationWarning,
            stacklevel=2,
        )

        super().__init__(*args, **kwargs)


class SyntaxTB(ListTB):
    """Extension which holds some state: the last exception value"""

    last_syntax_error: BaseException | None

    def __init__(self, *, theme_name):
        super().__init__(theme_name=theme_name)
        self.last_syntax_error = None

    def __call__(self, etype, value, elist):
        self.last_syntax_error = value

        super().__call__(etype, value, elist)

    def structured_traceback(
        self,
        etype: type,
        evalue: BaseException | None,
        etb: TracebackType | None = None,
        tb_offset: int | None = None,
        context: int = 5,
    ) -> list[str]:
        value = evalue
        # If the source file has been edited, the line in the syntax error can
        # be wrong (retrieved from an outdated cache). This replaces it with
        # the current value.
        if (
            isinstance(value, SyntaxError)
            and isinstance(value.filename, str)
            and isinstance(value.lineno, int)
        ):
            linecache.checkcache(value.filename)
            newtext = linecache.getline(value.filename, value.lineno)
            if newtext:
                value.text = newtext
        self.last_syntax_error = value
        return super(SyntaxTB, self).structured_traceback(
            etype, value, etb, tb_offset=tb_offset, context=context
        )

    def clear_err_state(self) -> Any | None:
        """Return the current error state and clear it"""
        e = self.last_syntax_error
        self.last_syntax_error = None
        return e

    def stb2text(self, stb: list[str]) -> str:
        """Convert a structured traceback (a list) to a string."""
        return "".join(stb)

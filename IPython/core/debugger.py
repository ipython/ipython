# -*- coding: utf-8 -*-
"""
Pdb debugger class.

Modified from the standard pdb.Pdb class to avoid including readline, so that
the command line completion of other programs which include this isn't
damaged.

In the future, this class will be expanded with improvements over the standard
pdb.

The code in this file is mainly lifted out of cmd.py in Python 2.2, with minor
changes. Licensing should therefore be under the standard Python terms.  For
details on the PSF (Python Software Foundation) standard license, see:

https://docs.python.org/2/license.html
"""

#*****************************************************************************
#
#       This file is licensed under the PSF license.
#
#       Copyright (C) 2001 Python Software Foundation, www.python.org
#       Copyright (C) 2005-2006 Fernando Perez. <fperez@colorado.edu>
#
#
#*****************************************************************************

import bdb
import functools
import inspect
import linecache
import sys
import warnings
import re
import os

from IPython import get_ipython
from IPython.utils import PyColorize
from IPython.utils import coloransi, py3compat
from IPython.core.excolors import exception_colors
from IPython.testing.skipdoctest import skip_doctest


prompt = 'ipdb> '

# We have to check this directly from sys.argv, config struct not yet available
from pdb import Pdb as OldPdb

# Allow the set_trace code to operate outside of an ipython instance, even if
# it does so with some limitations.  The rest of this support is implemented in
# the Tracer constructor.


def make_arrow(pad):
    """generate the leading arrow in front of traceback or debugger"""
    if pad >= 2:
        return '-'*(pad-2) + '> '
    elif pad == 1:
        return '>'
    return ''


def BdbQuit_excepthook(et, ev, tb, excepthook=None):
    """Exception hook which handles `BdbQuit` exceptions.

    All other exceptions are processed using the `excepthook`
    parameter.
    """
    warnings.warn("`BdbQuit_excepthook` is deprecated since version 5.1",
                  DeprecationWarning, stacklevel=2)
    if et == bdb.BdbQuit:
        print('Exiting Debugger.')
    elif excepthook is not None:
        excepthook(et, ev, tb)
    else:
        # Backwards compatibility. Raise deprecation warning?
        BdbQuit_excepthook.excepthook_ori(et, ev, tb)


def BdbQuit_IPython_excepthook(self, et, ev, tb, tb_offset=None):
    warnings.warn(
        "`BdbQuit_IPython_excepthook` is deprecated since version 5.1",
        DeprecationWarning, stacklevel=2)
    print('Exiting Debugger.')


class Tracer(object):
    """
    DEPRECATED

    Class for local debugging, similar to pdb.set_trace.

    Instances of this class, when called, behave like pdb.set_trace, but
    providing IPython's enhanced capabilities.

    This is implemented as a class which must be initialized in your own code
    and not as a standalone function because we need to detect at runtime
    whether IPython is already active or not.  That detection is done in the
    constructor, ensuring that this code plays nicely with a running IPython,
    while functioning acceptably (though with limitations) if outside of it.
    """

    @skip_doctest
    def __init__(self, colors=None):
        """
        DEPRECATED

        Create a local debugger instance.

        Parameters
        ----------
        colors : str, optional
            The name of the color scheme to use, it must be one of IPython's
            valid color schemes.  If not given, the function will default to
            the current IPython scheme when running inside IPython, and to
            'NoColor' otherwise.

        Examples
        --------
        ::

            from IPython.core.debugger import Tracer; debug_here = Tracer()

        Later in your code::

            debug_here()  # -> will open up the debugger at that point.

        Once the debugger activates, you can use all of its regular commands to
        step through code, set breakpoints, etc.  See the pdb documentation
        from the Python standard library for usage details.
        """
        warnings.warn("`Tracer` is deprecated since version 5.1, directly use "
                      "`IPython.core.debugger.Pdb.set_trace()`",
                      DeprecationWarning, stacklevel=2)

        ip = get_ipython()
        if ip is None:
            # Outside of ipython, we set our own exception hook manually
            sys.excepthook = functools.partial(BdbQuit_excepthook,
                                               excepthook=sys.excepthook)
            def_colors = 'NoColor'
        else:
            # In ipython, we use its custom exception handler mechanism
            def_colors = ip.colors
            ip.set_custom_exc((bdb.BdbQuit,), BdbQuit_IPython_excepthook)

        if colors is None:
            colors = def_colors

        # The stdlib debugger internally uses a modified repr from the `repr`
        # module, that limits the length of printed strings to a hardcoded
        # limit of 30 characters.  That much trimming is too aggressive, let's
        # at least raise that limit to 80 chars, which should be enough for
        # most interactive uses.
        try:
            from reprlib import aRepr
            aRepr.maxstring = 80
        except:
            # This is only a user-facing convenience, so any error we encounter
            # here can be warned about but can be otherwise ignored.  These
            # printouts will tell us about problems if this API changes
            import traceback
            traceback.print_exc()

        self.debugger = Pdb(colors)

    def __call__(self):
        """Starts an interactive debugger at the point where called.

        This is similar to the pdb.set_trace() function from the std lib, but
        using IPython's enhanced debugger."""

        self.debugger.set_trace(sys._getframe().f_back)


RGX_EXTRA_INDENT = re.compile(r'(?<=\n)\s+')


def strip_indentation(multiline_string):
    return RGX_EXTRA_INDENT.sub('', multiline_string)


def decorate_fn_with_doc(new_fn, old_fn, additional_text=""):
    """Make new_fn have old_fn's doc string. This is particularly useful
    for the ``do_...`` commands that hook into the help system.
    Adapted from from a comp.lang.python posting
    by Duncan Booth."""
    def wrapper(*args, **kw):
        return new_fn(*args, **kw)
    if old_fn.__doc__:
        wrapper.__doc__ = strip_indentation(old_fn.__doc__) + additional_text
    return wrapper


class Pdb(OldPdb):
    """Modified Pdb class, does not load readline.

    for a standalone version that uses prompt_toolkit, see
    `IPython.terminal.debugger.TerminalPdb` and
    `IPython.terminal.debugger.set_trace()`


    This debugger can hide and skip frames that are tagged according to some predicates.
    See the `skip_predicates` commands.

    """

    default_predicates = {"tbhide": True, "readonly": False, "ipython_internal": True}

    def __init__(self, color_scheme=None, completekey=None,
                 stdin=None, stdout=None, context=5, **kwargs):
        """Create a new IPython debugger.

        Parameters
        ----------
        color_scheme : default None
            Deprecated, do not use.
        completekey : default None
            Passed to pdb.Pdb.
        stdin : default None
            Passed to pdb.Pdb.
        stdout : default None
            Passed to pdb.Pdb.
        context : int
            Number of lines of source code context to show when
            displaying stacktrace information.
        **kwargs
            Passed to pdb.Pdb.

        Notes
        -----
        The possibilities are python version dependent, see the python
        docs for more info.
        """

        # Parent constructor:
        try:
            self.context = int(context)
            if self.context <= 0:
                raise ValueError("Context must be a positive integer")
        except (TypeError, ValueError) as e:
                raise ValueError("Context must be a positive integer") from e

        # `kwargs` ensures full compatibility with stdlib's `pdb.Pdb`.
        OldPdb.__init__(self, completekey, stdin, stdout, **kwargs)

        # IPython changes...
        self.shell = get_ipython()

        if self.shell is None:
            save_main = sys.modules['__main__']
            # No IPython instance running, we must create one
            from IPython.terminal.interactiveshell import \
                TerminalInteractiveShell
            self.shell = TerminalInteractiveShell.instance()
            # needed by any code which calls __import__("__main__") after
            # the debugger was entered. See also #9941.
            sys.modules["__main__"] = save_main

        if color_scheme is not None:
            warnings.warn(
                "The `color_scheme` argument is deprecated since version 5.1",
                DeprecationWarning, stacklevel=2)
        else:
            color_scheme = self.shell.colors

        self.aliases = {}

        # Create color table: we copy the default one from the traceback
        # module and add a few attributes needed for debugging
        self.color_scheme_table = exception_colors()

        # shorthands
        C = coloransi.TermColors
        cst = self.color_scheme_table

        cst['NoColor'].colors.prompt = C.NoColor
        cst['NoColor'].colors.breakpoint_enabled = C.NoColor
        cst['NoColor'].colors.breakpoint_disabled = C.NoColor

        cst['Linux'].colors.prompt = C.Green
        cst['Linux'].colors.breakpoint_enabled = C.LightRed
        cst['Linux'].colors.breakpoint_disabled = C.Red

        cst['LightBG'].colors.prompt = C.Blue
        cst['LightBG'].colors.breakpoint_enabled = C.LightRed
        cst['LightBG'].colors.breakpoint_disabled = C.Red

        cst['Neutral'].colors.prompt = C.Blue
        cst['Neutral'].colors.breakpoint_enabled = C.LightRed
        cst['Neutral'].colors.breakpoint_disabled = C.Red

        # Add a python parser so we can syntax highlight source while
        # debugging.
        self.parser = PyColorize.Parser(style=color_scheme)
        self.set_colors(color_scheme)

        # Set the prompt - the default prompt is '(Pdb)'
        self.prompt = prompt
        self.skip_hidden = True
        self.report_skipped = True

        # list of predicates we use to skip frames
        self._predicates = self.default_predicates

        # To save frame locals so we can restore them on up/down
        self.frame_locals = []

    def set_colors(self, scheme):
        """Shorthand access to the color table scheme selector method."""
        self.color_scheme_table.set_active_scheme(scheme)
        self.parser.style = scheme

    def set_trace(self, frame=None):
        if frame is None:
            frame = sys._getframe().f_back
        self.initial_frame = frame
        return super().set_trace(frame)

    def _hidden_predicate(self, frame):
        """
        Given a frame return whether it it should be hidden or not by IPython.
        """

        if self._predicates["readonly"]:
            fname = frame.f_code.co_filename
            # we need to check for file existence and interactively define
            # function would otherwise appear as RO.
            if os.path.isfile(fname) and not os.access(fname, os.W_OK):
                return True

        if self._predicates["tbhide"]:
            if frame in (self.curframe, getattr(self, "initial_frame", None)):
                return False
            else:
                return self._get_frame_locals(frame).get("__tracebackhide__", False)

        return False

    def hidden_frames(self, stack):
        """
        Given an index in the stack return whether it should be skipped.

        This is used in up/down and where to skip frames.
        """
        # The f_locals dictionary is updated from the actual frame
        # locals whenever the .f_locals accessor is called, so we
        # avoid calling it here to preserve self.curframe_locals.
        # Futhermore, there is no good reason to hide the current frame.
        ip_hide = [self._hidden_predicate(s[0]) for s in stack]
        ip_start = [i for i, s in enumerate(ip_hide) if s == "__ipython_bottom__"]
        if ip_start and self._predicates["ipython_internal"]:
            ip_hide = [h if i > ip_start[0] else True for (i, h) in enumerate(ip_hide)]
        return ip_hide

    def preloop(self):
        """
        Save a copy of all frame locals so changes to them are not lost
        when going up/down in the stack frame.
        """
        self.frame_locals = [
            stack_entry[0].f_locals.copy() for stack_entry in self.stack
        ]
        self.curframe_locals = self.frame_locals[self.curindex]
        super().preloop()

    def interaction(self, frame, traceback):
        try:
            OldPdb.interaction(self, frame, traceback)
        except KeyboardInterrupt:
            self.stdout.write("\n" + self.shell.get_exception_only())

    def precmd(self, line):
        """Perform useful escapes on the command before it is executed."""

        if line.endswith("??"):
            line = "pinfo2 " + line[:-2]
        elif line.endswith("?"):
            line = "pinfo " + line[:-1]

        line = super().precmd(line)

        return line

    def postcmd(self, stop, line):
        """Set current frame locals using the ones we saved in preloop."""
        self.curframe_locals = self.frame_locals[self.curindex]
        return super().postcmd(stop, line)

    def new_do_frame(self, arg):
        OldPdb.do_frame(self, arg)

    def new_do_quit(self, arg):

        if hasattr(self, 'old_all_completions'):
            self.shell.Completer.all_completions = self.old_all_completions

        return OldPdb.do_quit(self, arg)

    do_q = do_quit = decorate_fn_with_doc(new_do_quit, OldPdb.do_quit)

    def new_do_restart(self, arg):
        """Restart command. In the context of ipython this is exactly the same
        thing as 'quit'."""
        self.msg("Restart doesn't make sense here. Using 'quit' instead.")
        return self.do_quit(arg)

    def print_stack_trace(self, context=None):
        Colors = self.color_scheme_table.active_colors
        ColorsNormal = Colors.Normal
        if context is None:
            context = self.context
        try:
            context = int(context)
            if context <= 0:
                raise ValueError("Context must be a positive integer")
        except (TypeError, ValueError) as e:
                raise ValueError("Context must be a positive integer") from e
        try:
            skipped = 0
            for hidden, frame_lineno in zip(self.hidden_frames(self.stack), self.stack):
                if hidden and self.skip_hidden:
                    skipped += 1
                    continue
                if skipped:
                    print(
                        f"{Colors.excName}    [... skipping {skipped} hidden frame(s)]{ColorsNormal}\n"
                    )
                    skipped = 0
                self.print_stack_entry(frame_lineno, context=context)
            if skipped:
                print(
                    f"{Colors.excName}    [... skipping {skipped} hidden frame(s)]{ColorsNormal}\n"
                )
        except KeyboardInterrupt:
            pass

    def print_stack_entry(self, frame_lineno, prompt_prefix='\n-> ',
                          context=None):
        if context is None:
            context = self.context
        try:
            context = int(context)
            if context <= 0:
                raise ValueError("Context must be a positive integer")
        except (TypeError, ValueError) as e:
                raise ValueError("Context must be a positive integer") from e
        print(self.format_stack_entry(frame_lineno, '', context), file=self.stdout)

        # vds: >>
        frame, lineno = frame_lineno
        filename = frame.f_code.co_filename
        self.shell.hooks.synchronize_with_editor(filename, lineno, 0)
        # vds: <<

    def _get_frame_locals(self, frame):
        """ "
        Acessing f_local of current frame reset the namespace, so we want to avoid
        that or the following can happend

        ipdb> foo
        "old"
        ipdb> foo = "new"
        ipdb> foo
        "new"
        ipdb> where
        ipdb> foo
        "old"

        So if frame is self.current_frame we instead return self.curframe_locals

        """
        if frame is self.curframe:
            return self.curframe_locals
        else:
            return frame.f_locals

    def format_stack_entry(self, frame_lineno, lprefix=': ', context=None):
        if context is None:
            context = self.context
        try:
            context = int(context)
            if context <= 0:
                print("Context must be a positive integer", file=self.stdout)
        except (TypeError, ValueError):
                print("Context must be a positive integer", file=self.stdout)

        import reprlib

        ret = []

        Colors = self.color_scheme_table.active_colors
        ColorsNormal = Colors.Normal
        tpl_link = "%s%%s%s" % (Colors.filenameEm, ColorsNormal)
        tpl_call = "%s%%s%s%%s%s" % (Colors.vName, Colors.valEm, ColorsNormal)
        tpl_line = "%%s%s%%s %s%%s" % (Colors.lineno, ColorsNormal)
        tpl_line_em = "%%s%s%%s %s%%s%s" % (Colors.linenoEm, Colors.line, ColorsNormal)

        frame, lineno = frame_lineno

        return_value = ''
        loc_frame = self._get_frame_locals(frame)
        if "__return__" in loc_frame:
            rv = loc_frame["__return__"]
            # return_value += '->'
            return_value += reprlib.repr(rv) + "\n"
        ret.append(return_value)

        #s = filename + '(' + `lineno` + ')'
        filename = self.canonic(frame.f_code.co_filename)
        link = tpl_link % py3compat.cast_unicode(filename)

        if frame.f_code.co_name:
            func = frame.f_code.co_name
        else:
            func = "<lambda>"

        call = ""
        if func != "?":
            if "__args__" in loc_frame:
                args = reprlib.repr(loc_frame["__args__"])
            else:
                args = '()'
            call = tpl_call % (func, args)

        # The level info should be generated in the same format pdb uses, to
        # avoid breaking the pdbtrack functionality of python-mode in *emacs.
        if frame is self.curframe:
            ret.append('> ')
        else:
            ret.append("  ")
        ret.append("%s(%s)%s\n" % (link, lineno, call))

        start = lineno - 1 - context//2
        lines = linecache.getlines(filename)
        start = min(start, len(lines) - context)
        start = max(start, 0)
        lines = lines[start : start + context]

        for i, line in enumerate(lines):
            show_arrow = start + 1 + i == lineno
            linetpl = (frame is self.curframe or show_arrow) and tpl_line_em or tpl_line
            ret.append(
                self.__format_line(
                    linetpl, filename, start + 1 + i, line, arrow=show_arrow
                )
            )
        return "".join(ret)

    def __format_line(self, tpl_line, filename, lineno, line, arrow=False):
        bp_mark = ""
        bp_mark_color = ""

        new_line, err = self.parser.format2(line, 'str')
        if not err:
            line = new_line

        bp = None
        if lineno in self.get_file_breaks(filename):
            bps = self.get_breaks(filename, lineno)
            bp = bps[-1]

        if bp:
            Colors = self.color_scheme_table.active_colors
            bp_mark = str(bp.number)
            bp_mark_color = Colors.breakpoint_enabled
            if not bp.enabled:
                bp_mark_color = Colors.breakpoint_disabled

        numbers_width = 7
        if arrow:
            # This is the line with the error
            pad = numbers_width - len(str(lineno)) - len(bp_mark)
            num = '%s%s' % (make_arrow(pad), str(lineno))
        else:
            num = '%*s' % (numbers_width - len(bp_mark), str(lineno))

        return tpl_line % (bp_mark_color + bp_mark, num, line)

    def print_list_lines(self, filename, first, last):
        """The printing (as opposed to the parsing part of a 'list'
        command."""
        try:
            Colors = self.color_scheme_table.active_colors
            ColorsNormal = Colors.Normal
            tpl_line = '%%s%s%%s %s%%s' % (Colors.lineno, ColorsNormal)
            tpl_line_em = '%%s%s%%s %s%%s%s' % (Colors.linenoEm, Colors.line, ColorsNormal)
            src = []
            if filename == "<string>" and hasattr(self, "_exec_filename"):
                filename = self._exec_filename

            for lineno in range(first, last+1):
                line = linecache.getline(filename, lineno)
                if not line:
                    break

                if lineno == self.curframe.f_lineno:
                    line = self.__format_line(
                        tpl_line_em, filename, lineno, line, arrow=True
                    )
                else:
                    line = self.__format_line(
                        tpl_line, filename, lineno, line, arrow=False
                    )

                src.append(line)
                self.lineno = lineno

            print(''.join(src), file=self.stdout)

        except KeyboardInterrupt:
            pass

    def do_skip_predicates(self, args):
        """
        Turn on/off individual predicates as to whether a frame should be hidden/skip.

        The global option to skip (or not) hidden frames is set with skip_hidden

        To change the value of a predicate

            skip_predicates key [true|false]

        Call without arguments to see the current values.

        To permanently change the value of an option add the corresponding
        command to your ``~/.pdbrc`` file. If you are programmatically using the
        Pdb instance you can also change the ``default_predicates`` class
        attribute.
        """
        if not args.strip():
            print("current predicates:")
            for (p, v) in self._predicates.items():
                print("   ", p, ":", v)
            return
        type_value = args.strip().split(" ")
        if len(type_value) != 2:
            print(
                f"Usage: skip_predicates <type> <value>, with <type> one of {set(self._predicates.keys())}"
            )
            return

        type_, value = type_value
        if type_ not in self._predicates:
            print(f"{type_!r} not in {set(self._predicates.keys())}")
            return
        if value.lower() not in ("true", "yes", "1", "no", "false", "0"):
            print(
                f"{value!r} is invalid - use one of ('true', 'yes', '1', 'no', 'false', '0')"
            )
            return

        self._predicates[type_] = value.lower() in ("true", "yes", "1")
        if not any(self._predicates.values()):
            print(
                "Warning, all predicates set to False, skip_hidden may not have any effects."
            )

    def do_skip_hidden(self, arg):
        """
        Change whether or not we should skip frames with the
        __tracebackhide__ attribute.
        """
        if not arg.strip():
            print(
                f"skip_hidden = {self.skip_hidden}, use 'yes','no', 'true', or 'false' to change."
            )
        elif arg.strip().lower() in ("true", "yes"):
            self.skip_hidden = True
        elif arg.strip().lower() in ("false", "no"):
            self.skip_hidden = False
        if not any(self._predicates.values()):
            print(
                "Warning, all predicates set to False, skip_hidden may not have any effects."
            )

    def do_list(self, arg):
        """Print lines of code from the current stack frame
        """
        self.lastcmd = 'list'
        last = None
        if arg:
            try:
                x = eval(arg, {}, {})
                if type(x) == type(()):
                    first, last = x
                    first = int(first)
                    last = int(last)
                    if last < first:
                        # Assume it's a count
                        last = first + last
                else:
                    first = max(1, int(x) - 5)
            except:
                print('*** Error in argument:', repr(arg), file=self.stdout)
                return
        elif self.lineno is None:
            first = max(1, self.curframe.f_lineno - 5)
        else:
            first = self.lineno + 1
        if last is None:
            last = first + 10
        self.print_list_lines(self.curframe.f_code.co_filename, first, last)

        # vds: >>
        lineno = first
        filename = self.curframe.f_code.co_filename
        self.shell.hooks.synchronize_with_editor(filename, lineno, 0)
        # vds: <<

    do_l = do_list

    def getsourcelines(self, obj):
        lines, lineno = inspect.findsource(obj)
        if inspect.isframe(obj) and obj.f_globals is self._get_frame_locals(obj):
            # must be a module frame: do not try to cut a block out of it
            return lines, 1
        elif inspect.ismodule(obj):
            return lines, 1
        return inspect.getblock(lines[lineno:]), lineno+1

    def do_longlist(self, arg):
        """Print lines of code from the current stack frame.

        Shows more lines than 'list' does.
        """
        self.lastcmd = 'longlist'
        try:
            lines, lineno = self.getsourcelines(self.curframe)
        except OSError as err:
            self.error(err)
            return
        last = lineno + len(lines)
        self.print_list_lines(self.curframe.f_code.co_filename, lineno, last)
    do_ll = do_longlist

    def do_debug(self, arg):
        """debug code
        Enter a recursive debugger that steps through the code
        argument (which is an arbitrary expression or statement to be
        executed in the current environment).
        """
        trace_function = sys.gettrace()
        sys.settrace(None)
        globals = self.curframe.f_globals
        locals = self.curframe_locals
        p = self.__class__(completekey=self.completekey,
                           stdin=self.stdin, stdout=self.stdout)
        p.use_rawinput = self.use_rawinput
        p.prompt = "(%s) " % self.prompt.strip()
        self.message("ENTERING RECURSIVE DEBUGGER")
        sys.call_tracing(p.run, (arg, globals, locals))
        self.message("LEAVING RECURSIVE DEBUGGER")
        sys.settrace(trace_function)
        self.lastcmd = p.lastcmd

    def do_pdef(self, arg):
        """Print the call signature for any callable object.

        The debugger interface to %pdef"""
        namespaces = [
            ("Locals", self.curframe_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pdef")(arg, namespaces=namespaces)

    def do_pdoc(self, arg):
        """Print the docstring for an object.

        The debugger interface to %pdoc."""
        namespaces = [
            ("Locals", self.curframe_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pdoc")(arg, namespaces=namespaces)

    def do_pfile(self, arg):
        """Print (or run through pager) the file where an object is defined.

        The debugger interface to %pfile.
        """
        namespaces = [
            ("Locals", self.curframe_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pfile")(arg, namespaces=namespaces)

    def do_pinfo(self, arg):
        """Provide detailed information about an object.

        The debugger interface to %pinfo, i.e., obj?."""
        namespaces = [
            ("Locals", self.curframe_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pinfo")(arg, namespaces=namespaces)

    def do_pinfo2(self, arg):
        """Provide extra detailed information about an object.

        The debugger interface to %pinfo2, i.e., obj??."""
        namespaces = [
            ("Locals", self.curframe_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("pinfo2")(arg, namespaces=namespaces)

    def do_psource(self, arg):
        """Print (or run through pager) the source code for an object."""
        namespaces = [
            ("Locals", self.curframe_locals),
            ("Globals", self.curframe.f_globals),
        ]
        self.shell.find_line_magic("psource")(arg, namespaces=namespaces)

    def do_where(self, arg):
        """w(here)
        Print a stack trace, with the most recent frame at the bottom.
        An arrow indicates the "current frame", which determines the
        context of most commands. 'bt' is an alias for this command.

        Take a number as argument as an (optional) number of context line to
        print"""
        if arg:
            try:
                context = int(arg)
            except ValueError as err:
                self.error(err)
                return
            self.print_stack_trace(context)
        else:
            self.print_stack_trace()

    do_w = do_where

    def stop_here(self, frame):
        hidden = False
        if self.skip_hidden:
            hidden = self._hidden_predicate(frame)
        if hidden:
            if self.report_skipped:
                Colors = self.color_scheme_table.active_colors
                ColorsNormal = Colors.Normal
                print(
                    f"{Colors.excName}    [... skipped 1 hidden frame]{ColorsNormal}\n"
                )
        return super().stop_here(frame)

    def do_up(self, arg):
        """u(p) [count]
        Move the current frame count (default one) levels up in the
        stack trace (to an older frame).

        Will skip hidden frames.
        """
        # modified version of upstream that skips
        # frames with __tracebackhide__
        if self.curindex == 0:
            self.error("Oldest frame")
            return
        try:
            count = int(arg or 1)
        except ValueError:
            self.error("Invalid frame count (%s)" % arg)
            return
        skipped = 0
        if count < 0:
            _newframe = 0
        else:
            counter = 0
            hidden_frames = self.hidden_frames(self.stack)
            for i in range(self.curindex - 1, -1, -1):
                if hidden_frames[i] and self.skip_hidden:
                    skipped += 1
                    continue
                counter += 1
                if counter >= count:
                    break
            else:
                # if no break occured.
                self.error(
                    "all frames above hidden, use `skip_hidden False` to get get into those."
                )
                return

            Colors = self.color_scheme_table.active_colors
            ColorsNormal = Colors.Normal
            _newframe = i
        self._select_frame(_newframe)
        if skipped:
            print(
                f"{Colors.excName}    [... skipped {skipped} hidden frame(s)]{ColorsNormal}\n"
            )

    def do_down(self, arg):
        """d(own) [count]
        Move the current frame count (default one) levels down in the
        stack trace (to a newer frame).

        Will skip hidden frames.
        """
        if self.curindex + 1 == len(self.stack):
            self.error("Newest frame")
            return
        try:
            count = int(arg or 1)
        except ValueError:
            self.error("Invalid frame count (%s)" % arg)
            return
        if count < 0:
            _newframe = len(self.stack) - 1
        else:
            counter = 0
            skipped = 0
            hidden_frames = self.hidden_frames(self.stack)
            for i in range(self.curindex + 1, len(self.stack)):
                if hidden_frames[i] and self.skip_hidden:
                    skipped += 1
                    continue
                counter += 1
                if counter >= count:
                    break
            else:
                self.error(
                    "all frames bellow hidden, use `skip_hidden False` to get get into those."
                )
                return

            Colors = self.color_scheme_table.active_colors
            ColorsNormal = Colors.Normal
            if skipped:
                print(
                    f"{Colors.excName}    [... skipped {skipped} hidden frame(s)]{ColorsNormal}\n"
                )
            _newframe = i

        self._select_frame(_newframe)

    do_d = do_down
    do_u = do_up

    def do_context(self, context):
        """context number_of_lines
        Set the number of lines of source code to show when displaying
        stacktrace information.
        """
        try:
            new_context = int(context)
            if new_context <= 0:
                raise ValueError()
            self.context = new_context
        except ValueError:
            self.error("The 'context' command requires a positive integer argument.")


class InterruptiblePdb(Pdb):
    """Version of debugger where KeyboardInterrupt exits the debugger altogether."""

    def cmdloop(self):
        """Wrap cmdloop() such that KeyboardInterrupt stops the debugger."""
        try:
            return OldPdb.cmdloop(self)
        except KeyboardInterrupt:
            self.stop_here = lambda frame: False
            self.do_quit("")
            sys.settrace(None)
            self.quitting = False
            raise

    def _cmdloop(self):
        while True:
            try:
                # keyboard interrupts allow for an easy way to cancel
                # the current command, so allow them during interactive input
                self.allow_kbdint = True
                self.cmdloop()
                self.allow_kbdint = False
                break
            except KeyboardInterrupt:
                self.message('--KeyboardInterrupt--')
                raise


def set_trace(frame=None):
    """
    Start debugging from `frame`.

    If frame is not specified, debugging starts from caller's frame.
    """
    Pdb().set_trace(frame or sys._getframe().f_back)

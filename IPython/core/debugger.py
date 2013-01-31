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

http://www.python.org/2.2.3/license.html"""

#*****************************************************************************
#
#       This file is licensed under the PSF license.
#
#       Copyright (C) 2001 Python Software Foundation, www.python.org
#       Copyright (C) 2005-2006 Fernando Perez. <fperez@colorado.edu>
#
#
#*****************************************************************************
from __future__ import print_function

import bdb
import functools
import linecache
import sys

from IPython.utils import PyColorize, ulinecache
from IPython.core import ipapi
from IPython.utils import coloransi, io, py3compat
from IPython.core.excolors import exception_colors

# See if we can use pydb.
has_pydb = False
prompt = 'ipdb> '
#We have to check this directly from sys.argv, config struct not yet available
if '--pydb' in sys.argv:
    try:
        import pydb
        if hasattr(pydb.pydb, "runl") and pydb.version>'1.17':
            # Version 1.17 is broken, and that's what ships with Ubuntu Edgy, so we
            # better protect against it.
            has_pydb = True
    except ImportError:
        print("Pydb (http://bashdb.sourceforge.net/pydb/) does not seem to be available")

if has_pydb:
    from pydb import Pdb as OldPdb
    #print "Using pydb for %run -d and post-mortem" #dbg
    prompt = 'ipydb> '
else:
    from pdb import Pdb as OldPdb

# Allow the set_trace code to operate outside of an ipython instance, even if
# it does so with some limitations.  The rest of this support is implemented in
# the Tracer constructor.
def BdbQuit_excepthook(et, ev, tb, excepthook=None):
    """Exception hook which handles `BdbQuit` exceptions.

    All other exceptions are processed using the `excepthook`
    parameter.
    """
    if et==bdb.BdbQuit:
        print('Exiting Debugger.')
    elif excepthook is not None:
        excepthook(et, ev, tb)
    else:
        # Backwards compatibility. Raise deprecation warning?
        BdbQuit_excepthook.excepthook_ori(et,ev,tb)

def BdbQuit_IPython_excepthook(self,et,ev,tb,tb_offset=None):
    print('Exiting Debugger.')


class Tracer(object):
    """Class for local debugging, similar to pdb.set_trace.

    Instances of this class, when called, behave like pdb.set_trace, but
    providing IPython's enhanced capabilities.

    This is implemented as a class which must be initialized in your own code
    and not as a standalone function because we need to detect at runtime
    whether IPython is already active or not.  That detection is done in the
    constructor, ensuring that this code plays nicely with a running IPython,
    while functioning acceptably (though with limitations) if outside of it.
    """

    def __init__(self,colors=None):
        """Create a local debugger instance.

        :Parameters:

          - `colors` (None): a string containing the name of the color scheme to
        use, it must be one of IPython's valid color schemes.  If not given, the
        function will default to the current IPython scheme when running inside
        IPython, and to 'NoColor' otherwise.

        Usage example:

        from IPython.core.debugger import Tracer; debug_here = Tracer()

        ... later in your code
        debug_here()  # -> will open up the debugger at that point.

        Once the debugger activates, you can use all of its regular commands to
        step through code, set breakpoints, etc.  See the pdb documentation
        from the Python standard library for usage details.
        """

        try:
            ip = get_ipython()
        except NameError:
            # Outside of ipython, we set our own exception hook manually
            sys.excepthook = functools.partial(BdbQuit_excepthook,
                                               excepthook=sys.excepthook)
            def_colors = 'NoColor'
            try:
                # Limited tab completion support
                import readline
                readline.parse_and_bind('tab: complete')
            except ImportError:
                pass
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
            from repr import aRepr
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


def decorate_fn_with_doc(new_fn, old_fn, additional_text=""):
    """Make new_fn have old_fn's doc string. This is particularly useful
    for the ``do_...`` commands that hook into the help system.
    Adapted from from a comp.lang.python posting
    by Duncan Booth."""
    def wrapper(*args, **kw):
        return new_fn(*args, **kw)
    if old_fn.__doc__:
        wrapper.__doc__ = old_fn.__doc__ + additional_text
    return wrapper


def _file_lines(fname):
    """Return the contents of a named file as a list of lines.

    This function never raises an IOError exception: if the file can't be
    read, it simply returns an empty list."""

    try:
        outfile = open(fname)
    except IOError:
        return []
    else:
        out = outfile.readlines()
        outfile.close()
        return out


class Pdb(OldPdb):
    """Modified Pdb class, does not load readline."""

    def __init__(self,color_scheme='NoColor',completekey=None,
                 stdin=None, stdout=None):

        # Parent constructor:
        if has_pydb and completekey is None:
            OldPdb.__init__(self,stdin=stdin,stdout=io.stdout)
        else:
            OldPdb.__init__(self,completekey,stdin,stdout)

        self.prompt = prompt # The default prompt is '(Pdb)'

        # IPython changes...
        self.is_pydb = has_pydb

        self.shell = ipapi.get()

        if self.is_pydb:

            # interactiveshell.py's ipalias seems to want pdb's checkline
            # which located in pydb.fn
            import pydb.fns
            self.checkline = lambda filename, lineno: \
                             pydb.fns.checkline(self, filename, lineno)

            self.curframe = None
            self.do_restart = self.new_do_restart

            self.old_all_completions = self.shell.Completer.all_completions
            self.shell.Completer.all_completions=self.all_completions

            self.do_list = decorate_fn_with_doc(self.list_command_pydb,
                                                OldPdb.do_list)
            self.do_l     = self.do_list
            self.do_frame = decorate_fn_with_doc(self.new_do_frame,
                                                 OldPdb.do_frame)

        self.aliases = {}

        # Create color table: we copy the default one from the traceback
        # module and add a few attributes needed for debugging
        self.color_scheme_table = exception_colors()

        # shorthands
        C = coloransi.TermColors
        cst = self.color_scheme_table

        cst['NoColor'].colors.breakpoint_enabled = C.NoColor
        cst['NoColor'].colors.breakpoint_disabled = C.NoColor

        cst['Linux'].colors.breakpoint_enabled = C.LightRed
        cst['Linux'].colors.breakpoint_disabled = C.Red

        cst['LightBG'].colors.breakpoint_enabled = C.LightRed
        cst['LightBG'].colors.breakpoint_disabled = C.Red

        self.set_colors(color_scheme)

        # Add a python parser so we can syntax highlight source while
        # debugging.
        self.parser = PyColorize.Parser()

    def set_colors(self, scheme):
        """Shorthand access to the color table scheme selector method."""
        self.color_scheme_table.set_active_scheme(scheme)

    def interaction(self, frame, traceback):
        self.shell.set_completer_frame(frame)
        OldPdb.interaction(self, frame, traceback)

    def new_do_up(self, arg):
        OldPdb.do_up(self, arg)
        self.shell.set_completer_frame(self.curframe)
    do_u = do_up = decorate_fn_with_doc(new_do_up, OldPdb.do_up)

    def new_do_down(self, arg):
        OldPdb.do_down(self, arg)
        self.shell.set_completer_frame(self.curframe)

    do_d = do_down = decorate_fn_with_doc(new_do_down, OldPdb.do_down)

    def new_do_frame(self, arg):
        OldPdb.do_frame(self, arg)
        self.shell.set_completer_frame(self.curframe)

    def new_do_quit(self, arg):

        if hasattr(self, 'old_all_completions'):
            self.shell.Completer.all_completions=self.old_all_completions


        return OldPdb.do_quit(self, arg)

    do_q = do_quit = decorate_fn_with_doc(new_do_quit, OldPdb.do_quit)

    def new_do_restart(self, arg):
        """Restart command. In the context of ipython this is exactly the same
        thing as 'quit'."""
        self.msg("Restart doesn't make sense here. Using 'quit' instead.")
        return self.do_quit(arg)

    def postloop(self):
        self.shell.set_completer_frame(None)

    def print_stack_trace(self):
        try:
            for frame_lineno in self.stack:
                self.print_stack_entry(frame_lineno, context = 5)
        except KeyboardInterrupt:
            pass

    def print_stack_entry(self,frame_lineno,prompt_prefix='\n-> ',
                          context = 3):
        #frame, lineno = frame_lineno
        print(self.format_stack_entry(frame_lineno, '', context), file=io.stdout)

        # vds: >>
        frame, lineno = frame_lineno
        filename = frame.f_code.co_filename
        self.shell.hooks.synchronize_with_editor(filename, lineno, 0)
        # vds: <<

    def format_stack_entry(self, frame_lineno, lprefix=': ', context = 3):
        import repr

        ret = []

        Colors = self.color_scheme_table.active_colors
        ColorsNormal = Colors.Normal
        tpl_link = u'%s%%s%s' % (Colors.filenameEm, ColorsNormal)
        tpl_call = u'%s%%s%s%%s%s' % (Colors.vName, Colors.valEm, ColorsNormal)
        tpl_line = u'%%s%s%%s %s%%s' % (Colors.lineno, ColorsNormal)
        tpl_line_em = u'%%s%s%%s %s%%s%s' % (Colors.linenoEm, Colors.line,
                                            ColorsNormal)

        frame, lineno = frame_lineno

        return_value = ''
        if '__return__' in frame.f_locals:
            rv = frame.f_locals['__return__']
            #return_value += '->'
            return_value += repr.repr(rv) + '\n'
        ret.append(return_value)

        #s = filename + '(' + `lineno` + ')'
        filename = self.canonic(frame.f_code.co_filename)
        link = tpl_link % py3compat.cast_unicode(filename)

        if frame.f_code.co_name:
            func = frame.f_code.co_name
        else:
            func = "<lambda>"

        call = ''
        if func != '?':
            if '__args__' in frame.f_locals:
                args = repr.repr(frame.f_locals['__args__'])
            else:
                args = '()'
            call = tpl_call % (func, args)

        # The level info should be generated in the same format pdb uses, to
        # avoid breaking the pdbtrack functionality of python-mode in *emacs.
        if frame is self.curframe:
            ret.append('> ')
        else:
            ret.append('  ')
        ret.append(u'%s(%s)%s\n' % (link,lineno,call))

        start = lineno - 1 - context//2
        lines = ulinecache.getlines(filename)
        start = min(start, len(lines) - context)
        start = max(start, 0)
        lines = lines[start : start + context]

        for i,line in enumerate(lines):
            show_arrow = (start + 1 + i == lineno)
            linetpl = (frame is self.curframe or show_arrow) \
                      and tpl_line_em \
                      or tpl_line
            ret.append(self.__format_line(linetpl, filename,
                                          start + 1 + i, line,
                                          arrow = show_arrow) )
        return ''.join(ret)

    def __format_line(self, tpl_line, filename, lineno, line, arrow = False):
        bp_mark = ""
        bp_mark_color = ""

        scheme = self.color_scheme_table.active_scheme_name
        new_line, err = self.parser.format2(line, 'str', scheme)
        if not err: line = new_line

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
            if pad >= 3:
                marker = '-'*(pad-3) + '-> '
            elif pad == 2:
                 marker = '> '
            elif pad == 1:
                 marker = '>'
            else:
                 marker = ''
            num = '%s%s' % (marker, str(lineno))
            line = tpl_line % (bp_mark_color + bp_mark, num, line)
        else:
            num = '%*s' % (numbers_width - len(bp_mark), str(lineno))
            line = tpl_line % (bp_mark_color + bp_mark, num, line)

        return line

    def list_command_pydb(self, arg):
        """List command to use if we have a newer pydb installed"""
        filename, first, last = OldPdb.parse_list_cmd(self, arg)
        if filename is not None:
            self.print_list_lines(filename, first, last)

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
                line = ulinecache.getline(filename, lineno)
                if not line:
                    break

                if lineno == self.curframe.f_lineno:
                    line = self.__format_line(tpl_line_em, filename, lineno, line, arrow = True)
                else:
                    line = self.__format_line(tpl_line, filename, lineno, line, arrow = False)

                src.append(line)
                self.lineno = lineno

            print(''.join(src), file=io.stdout)

        except KeyboardInterrupt:
            pass

    def do_list(self, arg):
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
                print('*** Error in argument:', repr(arg))
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

    def do_pdef(self, arg):
        """Print the call signature for any callable object.

        The debugger interface to %pdef"""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        self.shell.find_line_magic('pdef')(arg, namespaces=namespaces)

    def do_pdoc(self, arg):
        """Print the docstring for an object.

        The debugger interface to %pdoc."""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        self.shell.find_line_magic('pdoc')(arg, namespaces=namespaces)

    def do_pfile(self, arg):
        """Print (or run through pager) the file where an object is defined.

        The debugger interface to %pfile.
        """
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        self.shell.find_line_magic('pfile')(arg, namespaces=namespaces)

    def do_pinfo(self, arg):
        """Provide detailed information about an object.

        The debugger interface to %pinfo, i.e., obj?."""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        self.shell.find_line_magic('pinfo')(arg, namespaces=namespaces)

    def do_pinfo2(self, arg):
        """Provide extra detailed information about an object.

        The debugger interface to %pinfo2, i.e., obj??."""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        self.shell.find_line_magic('pinfo2')(arg, namespaces=namespaces)

    def do_psource(self, arg):
        """Print (or run through pager) the source code for an object."""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        self.shell.find_line_magic('psource')(arg, namespaces=namespaces)

    def checkline(self, filename, lineno):
        """Check whether specified line seems to be executable.

        Return `lineno` if it is, 0 if not (e.g. a docstring, comment, blank
        line or EOF). Warning: testing is not comprehensive.
        """
        #######################################################################
        # XXX Hack!  Use python-2.5 compatible code for this call, because with
        # all of our changes, we've drifted from the pdb api in 2.6.  For now,
        # changing:
        #
        #line = linecache.getline(filename, lineno, self.curframe.f_globals)
        # to:
        #
        line = linecache.getline(filename, lineno)
        #
        # does the trick.  But in reality, we need to fix this by reconciling
        # our updates with the new Pdb APIs in Python 2.6.
        #
        # End hack.  The rest of this method is copied verbatim from 2.6 pdb.py
        #######################################################################

        if not line:
            print('End of file', file=self.stdout)
            return 0
        line = line.strip()
        # Don't allow setting breakpoint at a blank line
        if (not line or (line[0] == '#') or
             (line[:3] == '"""') or line[:3] == "'''"):
            print('*** Blank or comment', file=self.stdout)
            return 0
        return lineno

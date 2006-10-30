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

http://www.python.org/2.2.3/license.html

$Id: Debugger.py 1853 2006-10-30 17:00:39Z vivainio $"""

#*****************************************************************************
#
# Since this file is essentially a modified copy of the pdb module which is
# part of the standard Python distribution, I assume that the proper procedure
# is to maintain its copyright as belonging to the Python Software Foundation
# (in addition to my own, for all new code).
#
#       Copyright (C) 2001 Python Software Foundation, www.python.org
#       Copyright (C) 2005-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = 'Python'

import bdb
import cmd
import linecache
import os
import sys

from IPython import PyColorize, ColorANSI
from IPython.genutils import Term
from IPython.excolors import ExceptionColors

# See if we can use pydb.
has_pydb = False
prompt = 'ipdb>'
if sys.version[:3] >= '2.5':
    try:
        import pydb
        if hasattr(pydb.pydb, "runl"):
            has_pydb = True
            from pydb import Pdb as OldPdb
            prompt = 'ipydb>'
    except ImportError:
        pass

if has_pydb:
    from pydb import Pdb as OldPdb
else:
    from pdb import Pdb as OldPdb

def decorate_fn_with_doc(new_fn, old_fn, additional_text=""):
    """Make new_fn have old_fn's doc string. This is particularly useful
    for the do_... commands that hook into the help system.
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

    if sys.version[:3] >= '2.5':
        def __init__(self,color_scheme='NoColor',completekey=None,
                     stdin=None, stdout=None):

            # Parent constructor:
            OldPdb.__init__(self,completekey,stdin,stdout)
            
            # IPython changes...
            self.prompt = prompt # The default prompt is '(Pdb)'
            self.is_pydb = prompt == 'ipydb>'

            if self.is_pydb:

                # iplib.py's ipalias seems to want pdb's checkline
                # which located in pydb.fn
                import pydb.fns
                self.checkline = lambda filename, lineno: \
                                 pydb.fns.checkline(self, filename, lineno)

                self.curframe = None
                self.do_restart = self.new_do_restart

                self.old_all_completions = __IPYTHON__.Completer.all_completions
                __IPYTHON__.Completer.all_completions=self.all_completions

                # Do we have access to pydb's list command parser?
                self.do_list = decorate_fn_with_doc(self.list_command_pydb,
                                                    OldPdb.do_list)
                self.do_l     = self.do_list
                self.do_frame = decorate_fn_with_doc(self.new_do_frame,
                                                     OldPdb.do_frame)

            self.aliases = {}

            # Create color table: we copy the default one from the traceback
            # module and add a few attributes needed for debugging
            self.color_scheme_table = ExceptionColors.copy()

            # shorthands 
            C = ColorANSI.TermColors
            cst = self.color_scheme_table

            cst['NoColor'].colors.breakpoint_enabled = C.NoColor
            cst['NoColor'].colors.breakpoint_disabled = C.NoColor

            cst['Linux'].colors.breakpoint_enabled = C.LightRed
            cst['Linux'].colors.breakpoint_disabled = C.Red

            cst['LightBG'].colors.breakpoint_enabled = C.LightRed
            cst['LightBG'].colors.breakpoint_disabled = C.Red

            self.set_colors(color_scheme)

    else:
        # Ugly hack: for Python 2.3-2.4, we can't call the parent constructor,
        # because it binds readline and breaks tab-completion.  This means we
        # have to COPY the constructor here.
        def __init__(self,color_scheme='NoColor'):
            bdb.Bdb.__init__(self)
            cmd.Cmd.__init__(self,completekey=None) # don't load readline
            self.prompt = 'ipdb> ' # The default prompt is '(Pdb)'
            self.aliases = {}

            # These two lines are part of the py2.4 constructor, let's put them
            # unconditionally here as they won't cause any problems in 2.3.
            self.mainpyfile = ''
            self._wait_for_mainpyfile = 0

            # Read $HOME/.pdbrc and ./.pdbrc
            try:
                self.rcLines = _file_lines(os.path.join(os.environ['HOME'],
                                                        ".pdbrc"))
            except KeyError:
                self.rcLines = []
            self.rcLines.extend(_file_lines(".pdbrc"))

            # Create color table: we copy the default one from the traceback
            # module and add a few attributes needed for debugging
            self.color_scheme_table = ExceptionColors.copy()

            # shorthands 
            C = ColorANSI.TermColors
            cst = self.color_scheme_table

            cst['NoColor'].colors.breakpoint_enabled = C.NoColor
            cst['NoColor'].colors.breakpoint_disabled = C.NoColor

            cst['Linux'].colors.breakpoint_enabled = C.LightRed
            cst['Linux'].colors.breakpoint_disabled = C.Red

            cst['LightBG'].colors.breakpoint_enabled = C.LightRed
            cst['LightBG'].colors.breakpoint_disabled = C.Red

            self.set_colors(color_scheme)
        
    def set_colors(self, scheme):
        """Shorthand access to the color table scheme selector method."""
        self.color_scheme_table.set_active_scheme(scheme)

    def interaction(self, frame, traceback):
        __IPYTHON__.set_completer_frame(frame)
        OldPdb.interaction(self, frame, traceback)

    def new_do_up(self, arg):
        OldPdb.do_up(self, arg)
        __IPYTHON__.set_completer_frame(self.curframe)
    do_u = do_up = decorate_fn_with_doc(new_do_up, OldPdb.do_up)

    def new_do_down(self, arg):
        OldPdb.do_down(self, arg)
        __IPYTHON__.set_completer_frame(self.curframe)

    do_d = do_down = decorate_fn_with_doc(new_do_down, OldPdb.do_down)

    def new_do_frame(self, arg):
        OldPdb.do_frame(self, arg)
        __IPYTHON__.set_completer_frame(self.curframe)

    def new_do_quit(self, arg):
        __IPYTHON__.Completer.all_completions=self.old_all_completions
        return OldPdb.do_quit(self, arg)

    do_q = do_quit = decorate_fn_with_doc(new_do_quit, OldPdb.do_quit)

    def new_do_restart(self, arg):
        """Restart command. In the context of ipython this is exactly the same
        thing as 'quit'."""
        self.msg("Restart doesn't make sense here. Using 'quit' instead.")
        return self.do_quit(arg)

    def postloop(self):
        __IPYTHON__.set_completer_frame(None)

    def print_stack_trace(self):
        try:
            for frame_lineno in self.stack:
                self.print_stack_entry(frame_lineno, context = 5)
        except KeyboardInterrupt:
            pass

    def print_stack_entry(self,frame_lineno,prompt_prefix='\n-> ',
                          context = 3):
        frame, lineno = frame_lineno
        print >>Term.cout, self.format_stack_entry(frame_lineno, '', context)

    def format_stack_entry(self, frame_lineno, lprefix=': ', context = 3):
        import linecache, repr
        
        ret = []
        
        Colors = self.color_scheme_table.active_colors
        ColorsNormal = Colors.Normal
        tpl_link = '%s%%s%s' % (Colors.filenameEm, ColorsNormal)
        tpl_call = '%s%%s%s%%s%s' % (Colors.vName, Colors.valEm, ColorsNormal)
        tpl_line = '%%s%s%%s %s%%s' % (Colors.lineno, ColorsNormal)
        tpl_line_em = '%%s%s%%s %s%%s%s' % (Colors.linenoEm, Colors.line,
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
        link = tpl_link % filename
        
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
        ret.append('> %s(%s)%s\n' % (link,lineno,call))
            
        start = lineno - 1 - context//2
        lines = linecache.getlines(filename)
        start = max(start, 0)
        start = min(start, len(lines) - context)
        lines = lines[start : start + context]
            
        for i,line in enumerate(lines):
            show_arrow = (start + 1 + i == lineno)
            ret.append(self.__format_line(tpl_line_em, filename,
                                          start + 1 + i, line,
                                          arrow = show_arrow) )

        return ''.join(ret)

    def __format_line(self, tpl_line, filename, lineno, line, arrow = False):
        bp_mark = ""
        bp_mark_color = ""

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
            for lineno in range(first, last+1):
                line = linecache.getline(filename, lineno)
                if not line:
                    break

                if lineno == self.curframe.f_lineno:
                    line = self.__format_line(tpl_line_em, filename, lineno, line, arrow = True)
                else:
                    line = self.__format_line(tpl_line, filename, lineno, line, arrow = False)

                src.append(line)
                self.lineno = lineno

            print >>Term.cout, ''.join(src)

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
                print '*** Error in argument:', `arg`
                return
        elif self.lineno is None:
            first = max(1, self.curframe.f_lineno - 5)
        else:
            first = self.lineno + 1
        if last is None:
            last = first + 10
        self.print_list_lines(self.curframe.f_code.co_filename, first, last)

    do_l = do_list

    def do_pdef(self, arg):
        """The debugger interface to magic_pdef"""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        __IPYTHON__.magic_pdef(arg, namespaces=namespaces)

    def do_pdoc(self, arg):
        """The debugger interface to magic_pdoc"""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        __IPYTHON__.magic_pdoc(arg, namespaces=namespaces)

    def do_pinfo(self, arg):
        """The debugger equivalant of ?obj"""
        namespaces = [('Locals', self.curframe.f_locals),
                      ('Globals', self.curframe.f_globals)]
        __IPYTHON__.magic_pinfo("pinfo %s" % arg, namespaces=namespaces)

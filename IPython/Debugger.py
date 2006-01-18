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

$Id: Debugger.py 1029 2006-01-18 07:33:38Z fperez $"""

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
import pdb
import sys

from IPython import PyColorize, ColorANSI
from IPython.genutils import Term
from IPython.excolors import ExceptionColors

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


class Pdb(pdb.Pdb):
    """Modified Pdb class, does not load readline."""

    # Ugly hack: we can't call the parent constructor, because it binds
    # readline and breaks tab-completion.  This means we have to COPY the
    # constructor here, and that requires tracking various python versions.
    
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
        pdb.Pdb.interaction(self, frame, traceback)


    def do_up(self, arg):
        pdb.Pdb.do_up(self, arg)
        __IPYTHON__.set_completer_frame(self.curframe)
    do_u = do_up


    def do_down(self, arg):
        pdb.Pdb.do_down(self, arg)
        __IPYTHON__.set_completer_frame(self.curframe)
    do_d = do_down


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
        
        ret = ""
        
        Colors = self.color_scheme_table.active_colors
        ColorsNormal = Colors.Normal
        tpl_link = '%s%%s%s' % (Colors.filenameEm, ColorsNormal)
        tpl_call = 'in %s%%s%s%%s%s' % (Colors.vName, Colors.valEm, ColorsNormal)
        tpl_line = '%%s%s%%s %s%%s' % (Colors.lineno, ColorsNormal)
        tpl_line_em = '%%s%s%%s %s%%s%s' % (Colors.linenoEm, Colors.line,
                                            ColorsNormal)
        
        frame, lineno = frame_lineno
        
        return_value = ''
        if '__return__' in frame.f_locals:
            rv = frame.f_locals['__return__']
            #return_value += '->'
            return_value += repr.repr(rv) + '\n'
        ret += return_value

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
        
        level = '%s %s\n' % (link, call)
        ret += level
            
        start = lineno - 1 - context//2
        lines = linecache.getlines(filename)
        start = max(start, 0)
        start = min(start, len(lines) - context)
        lines = lines[start : start + context]
            
        for i in range(len(lines)):
            line = lines[i]
            if start + 1 + i == lineno:
                ret += self.__format_line(tpl_line_em, filename, start + 1 + i, line, arrow = True)
            else:
                ret += self.__format_line(tpl_line, filename, start + 1 + i, line, arrow = False)
            
        return ret


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
        filename = self.curframe.f_code.co_filename
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

    do_l = do_list

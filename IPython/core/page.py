# encoding: utf-8
"""
Paging capabilities for IPython.core

Authors:

* Brian Granger
* Fernando Perez

Notes
-----

For now this uses ipapi, so it can't be in IPython.utils.  If we can get
rid of that dependency, we could move it there.
-----
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import re
import subprocess
import sys
import tempfile

from io import UnsupportedOperation

from IPython.core import ipapi
from IPython.core.error import TryNext
from IPython.utils.cursesimport import use_curses
from IPython.utils.data import chop
from IPython.utils import io
from IPython.utils.process import system
from IPython.utils.terminal import get_terminal_size
from IPython.utils import py3compat


#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

esc_re = re.compile(r"(\x1b[^m]+m)")

def page_dumb(strng, start=0, screen_lines=25):
    """Very dumb 'pager' in Python, for when nothing else works.

    Only moves forward, same interface as page(), except for pager_cmd and
    mode."""

    out_ln  = strng.splitlines()[start:]
    screens = chop(out_ln,screen_lines-1)
    if len(screens) == 1:
        print >>io.stdout, os.linesep.join(screens[0])
    else:
        last_escape = ""
        for scr in screens[0:-1]:
            hunk = os.linesep.join(scr)
            print >>io.stdout, last_escape + hunk
            if not page_more():
                return
            esc_list = esc_re.findall(hunk)
            if len(esc_list) > 0:
                last_escape = esc_list[-1]
        print >>io.stdout, last_escape + os.linesep.join(screens[-1])

def _detect_screen_size(use_curses, screen_lines_def):
    """Attempt to work out the number of lines on the screen.

    This is called by page(). It can raise an error (e.g. when run in the
    test suite), so it's separated out so it can easily be called in a try block.
    """
    TERM = os.environ.get('TERM',None)
    if (TERM=='xterm' or TERM=='xterm-color') and sys.platform != 'sunos5':
        local_use_curses = use_curses
    else:
        # curses causes problems on many terminals other than xterm, and
        # some termios calls lock up on Sun OS5.
        local_use_curses = False
    if local_use_curses:
        import termios
        import curses
        # There is a bug in curses, where *sometimes* it fails to properly
        # initialize, and then after the endwin() call is made, the
        # terminal is left in an unusable state.  Rather than trying to
        # check everytime for this (by requesting and comparing termios
        # flags each time), we just save the initial terminal state and
        # unconditionally reset it every time.  It's cheaper than making
        # the checks.
        term_flags = termios.tcgetattr(sys.stdout)

        # Curses modifies the stdout buffer size by default, which messes
        # up Python's normal stdout buffering.  This would manifest itself
        # to IPython users as delayed printing on stdout after having used
        # the pager.
        #
        # We can prevent this by manually setting the NCURSES_NO_SETBUF
        # environment variable.  For more details, see:
        # http://bugs.python.org/issue10144
        NCURSES_NO_SETBUF = os.environ.get('NCURSES_NO_SETBUF', None)
        os.environ['NCURSES_NO_SETBUF'] = ''

        # Proceed with curses initialization
        scr = curses.initscr()
        screen_lines_real,screen_cols = scr.getmaxyx()
        curses.endwin()

        # Restore environment
        if NCURSES_NO_SETBUF is None:
            del os.environ['NCURSES_NO_SETBUF']
        else:
            os.environ['NCURSES_NO_SETBUF'] = NCURSES_NO_SETBUF

        # Restore terminal state in case endwin() didn't.
        termios.tcsetattr(sys.stdout,termios.TCSANOW,term_flags)
        # Now we have what we needed: the screen size in rows/columns
        return screen_lines_real
        #print '***Screen size:',screen_lines_real,'lines x',\
        #screen_cols,'columns.' # dbg
    else:
        return screen_lines_def

def page(strng, start=0, screen_lines=0, pager_cmd=None):
    """Print a string, piping through a pager after a certain length.

    The screen_lines parameter specifies the number of *usable* lines of your
    terminal screen (total lines minus lines you need to reserve to show other
    information).

    If you set screen_lines to a number <=0, page() will try to auto-determine
    your screen size and will only use up to (screen_size+screen_lines) for
    printing, paging after that. That is, if you want auto-detection but need
    to reserve the bottom 3 lines of the screen, use screen_lines = -3, and for
    auto-detection without any lines reserved simply use screen_lines = 0.

    If a string won't fit in the allowed lines, it is sent through the
    specified pager command. If none given, look for PAGER in the environment,
    and ultimately default to less.

    If no system pager works, the string is sent through a 'dumb pager'
    written in python, very simplistic.
    """

    # Some routines may auto-compute start offsets incorrectly and pass a
    # negative value.  Offset to 0 for robustness.
    start = max(0, start)

    # first, try the hook
    ip = ipapi.get()
    if ip:
        try:
            ip.hooks.show_in_pager(strng)
            return
        except TryNext:
            pass

    # Ugly kludge, but calling curses.initscr() flat out crashes in emacs
    TERM = os.environ.get('TERM','dumb')
    if TERM in ['dumb','emacs'] and os.name != 'nt':
        print strng
        return
    # chop off the topmost part of the string we don't want to see
    str_lines = strng.splitlines()[start:]
    str_toprint = os.linesep.join(str_lines)
    num_newlines = len(str_lines)
    len_str = len(str_toprint)

    # Dumb heuristics to guesstimate number of on-screen lines the string
    # takes.  Very basic, but good enough for docstrings in reasonable
    # terminals. If someone later feels like refining it, it's not hard.
    numlines = max(num_newlines,int(len_str/80)+1)

    screen_lines_def = get_terminal_size()[1]

    # auto-determine screen size
    if screen_lines <= 0:
        try:
            screen_lines += _detect_screen_size(use_curses, screen_lines_def)
        except (TypeError, UnsupportedOperation):
            print >>io.stdout, str_toprint
            return

    #print 'numlines',numlines,'screenlines',screen_lines  # dbg
    if numlines <= screen_lines :
        #print '*** normal print'  # dbg
        print >>io.stdout, str_toprint
    else:
        # Try to open pager and default to internal one if that fails.
        # All failure modes are tagged as 'retval=1', to match the return
        # value of a failed system command.  If any intermediate attempt
        # sets retval to 1, at the end we resort to our own page_dumb() pager.
        pager_cmd = get_pager_cmd(pager_cmd)
        pager_cmd += ' ' + get_pager_start(pager_cmd,start)
        if os.name == 'nt':
            if pager_cmd.startswith('type'):
                # The default WinXP 'type' command is failing on complex strings.
                retval = 1
            else:
                tmpname = tempfile.mktemp('.txt')
                tmpfile = open(tmpname,'wt')
                tmpfile.write(strng)
                tmpfile.close()
                cmd = "%s < %s" % (pager_cmd,tmpname)
                if os.system(cmd):
                  retval = 1
                else:
                  retval = None
                os.remove(tmpname)
        else:
            try:
                retval = None
                # if I use popen4, things hang. No idea why.
                #pager,shell_out = os.popen4(pager_cmd)
                pager = os.popen(pager_cmd, 'w')
                try:
                    pager_encoding = pager.encoding or sys.stdout.encoding
                    pager.write(py3compat.cast_bytes_py2(
                        strng, encoding=pager_encoding))
                finally:
                    retval = pager.close()
            except IOError,msg:  # broken pipe when user quits
                if msg.args == (32, 'Broken pipe'):
                    retval = None
                else:
                    retval = 1
            except OSError:
                # Other strange problems, sometimes seen in Win2k/cygwin
                retval = 1
        if retval is not None:
            page_dumb(strng,screen_lines=screen_lines)


def page_file(fname, start=0, pager_cmd=None):
    """Page a file, using an optional pager command and starting line.
    """

    pager_cmd = get_pager_cmd(pager_cmd)
    pager_cmd += ' ' + get_pager_start(pager_cmd,start)

    try:
        if os.environ['TERM'] in ['emacs','dumb']:
            raise EnvironmentError
        system(pager_cmd + ' ' + fname)
    except:
        try:
            if start > 0:
                start -= 1
            page(open(fname).read(),start)
        except:
            print 'Unable to show file',`fname`


def get_pager_cmd(pager_cmd=None):
    """Return a pager command.

    Makes some attempts at finding an OS-correct one.
    """
    if os.name == 'posix':
        default_pager_cmd = 'less -r'  # -r for color control sequences
    elif os.name in ['nt','dos']:
        default_pager_cmd = 'type'

    if pager_cmd is None:
        try:
            pager_cmd = os.environ['PAGER']
        except:
            pager_cmd = default_pager_cmd
    return pager_cmd


def get_pager_start(pager, start):
    """Return the string for paging files with an offset.

    This is the '+N' argument which less and more (under Unix) accept.
    """

    if pager in ['less','more']:
        if start:
            start_string = '+' + str(start)
        else:
            start_string = ''
    else:
        start_string = ''
    return start_string


# (X)emacs on win32 doesn't like to be bypassed with msvcrt.getch()
if os.name == 'nt' and os.environ.get('TERM','dumb') != 'emacs':
    import msvcrt
    def page_more():
        """ Smart pausing between pages

        @return:    True if need print more lines, False if quit
        """
        io.stdout.write('---Return to continue, q to quit--- ')
        ans = msvcrt.getch()
        if ans in ("q", "Q"):
            result = False
        else:
            result = True
        io.stdout.write("\b"*37 + " "*37 + "\b"*37)
        return result
else:
    def page_more():
        ans = raw_input('---Return to continue, q to quit--- ')
        if ans.lower().startswith('q'):
            return False
        else:
            return True


def snip_print(str,width = 75,print_full = 0,header = ''):
    """Print a string snipping the midsection to fit in width.

    print_full: mode control:
      - 0: only snip long strings
      - 1: send to page() directly.
      - 2: snip long strings and ask for full length viewing with page()
    Return 1 if snipping was necessary, 0 otherwise."""

    if print_full == 1:
        page(header+str)
        return 0

    print header,
    if len(str) < width:
        print str
        snip = 0
    else:
        whalf = int((width -5)/2)
        print str[:whalf] + ' <...> ' + str[-whalf:]
        snip = 1
    if snip and print_full == 2:
        if raw_input(header+' Snipped. View (y/n)? [N]').lower() == 'y':
            page(str)
    return snip

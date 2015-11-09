# -*- coding: utf-8 -*-
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
  potentially leak sensitive information like access keys, or unencryted
  password.

Installation instructions for VerboseTB::

    import sys,ultratb
    sys.excepthook = ultratb.VerboseTB()

Note:  Much of the code in this module was lifted verbatim from the standard
library module 'traceback.py' and Ka-Ping Yee's 'cgitb.py'.

Color schemes
-------------

Ultratb support various color schemes through the use of Pygments. 
The scheme `nocolor` can be used to avoid any coloring. 


Inheritance diagram:

.. inheritance-diagram:: IPython.core.ultratb
   :parts: 3
"""

#*****************************************************************************
# Copyright (C) 2001 Nathaniel Gray <n8gray@caltech.edu>
# Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
# Distributed under the terms of the BSD License.  The full license is in
# the file COPYING, distributed as part of this software.
#*****************************************************************************

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import dis
import inspect
import keyword
import linecache
import os
import pydoc
import re
import sys
import time
import tokenize
import traceback
import warnings
import types

try:  # Python 2
    generate_tokens = tokenize.generate_tokens
except AttributeError:  # Python 3
    generate_tokens = tokenize.tokenize

# For purposes of monkeypatching inspect to fix a bug in it.
from inspect import getsourcefile, getfile, getmodule, \
    ismodule, isclass, ismethod, isfunction, istraceback, isframe, iscode

# IPython's own modules
# Modified pdb which doesn't damage IPython's readline handling
from IPython import get_ipython
from IPython.core import debugger
from IPython.core.display_trap import DisplayTrap
from IPython.utils import PyColorize
from IPython.utils import io
from IPython.utils import openpy
from IPython.utils import path as util_path
from IPython.utils import py3compat
from IPython.utils import ulinecache
from IPython.utils.data import uniq_stable
from logging import info, error

import IPython.utils.colorable as colorable
from pygments.token import Token

# Globals
# amount of space to put line numbers before verbose tracebacks
INDENT_SIZE = 8
LINE_LENGTH = 75

# Utility functions
def inspect_error():
    """Print a message about internal inspect errors.

    These are unfortunately quite common."""

    error('Internal Python error in the inspect module.\n'
          'Below is the traceback from this internal error.\n')


# This function is a monkeypatch we apply to the Python inspect module. We have
# now found when it's needed (see discussion on issue gh-1456), and we have a
# test case (IPython.core.tests.test_ultratb.ChangedPyFileTest) that fails if
# the monkeypatch is not applied. TK, Aug 2012.
def findsource(object):
    """Return the entire source file and starting line number for an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a list of all the lines
    in the file and the line number indexes a line in that list.  An IOError
    is raised if the source code cannot be retrieved.

    FIXED version with which we monkeypatch the stdlib to work around a bug."""

    file = getsourcefile(object) or getfile(object)
    # If the object is a frame, then trying to get the globals dict from its
    # module won't work. Instead, the frame object itself has the globals
    # dictionary.
    globals_dict = None
    if inspect.isframe(object):
        # XXX: can this ever be false?
        globals_dict = object.f_globals
    else:
        module = getmodule(object, file)
        if module:
            globals_dict = module.__dict__
    lines = linecache.getlines(file, globals_dict)
    if not lines:
        raise IOError('could not get source code')

    if ismodule(object):
        return lines, 0

    if isclass(object):
        name = object.__name__
        pat = re.compile(r'^(\s*)class\s*' + name + r'\b')
        # make some effort to find the best matching class definition:
        # use the one with the least indentation, which is the one
        # that's most probably not inside a function definition.
        candidates = []
        for i in range(len(lines)):
            match = pat.match(lines[i])
            if match:
                # if it's at toplevel, it's already the best one
                if lines[i][0] == 'c':
                    return lines, i
                # else add whitespace to candidate list
                candidates.append((match.group(1), i))
        if candidates:
            # this will sort by whitespace, and by line number,
            # less whitespace first
            candidates.sort()
            return lines, candidates[0][1]
        else:
            raise IOError('could not find class definition')

    if ismethod(object):
        object = object.__func__
    if isfunction(object):
        object = object.__code__
    if istraceback(object):
        object = object.tb_frame
    if isframe(object):
        object = object.f_code
    if iscode(object):
        if not hasattr(object, 'co_firstlineno'):
            raise IOError('could not find function definition')
        pat = re.compile(r'^(\s*def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)')
        pmatch = pat.match
        # fperez - fix: sometimes, co_firstlineno can give a number larger than
        # the length of lines, which causes an error.  Safeguard against that.
        lnum = min(object.co_firstlineno, len(lines)) - 1
        while lnum > 0:
            if pmatch(lines[lnum]):
                break
            lnum -= 1

        return lines, lnum
    raise IOError('could not find code object')


# This is a patched version of inspect.getargs that applies the (unmerged)
# patch for http://bugs.python.org/issue14611 by Stefano Taschini.  This fixes
# https://github.com/ipython/ipython/issues/8205 and
# https://github.com/ipython/ipython/issues/8293
def getargs(co):
    """Get information about the arguments accepted by a code object.

    Three things are returned: (args, varargs, varkw), where 'args' is
    a list of argument names (possibly containing nested lists), and
    'varargs' and 'varkw' are the names of the * and ** arguments or None."""
    if not iscode(co):
        raise TypeError('{!r} is not a code object'.format(co))

    nargs = co.co_argcount
    names = co.co_varnames
    args = list(names[:nargs])
    step = 0

    # The following acrobatics are for anonymous (tuple) arguments.
    for i in range(nargs):
        if args[i][:1] in ('', '.'):
            stack, remain, count = [], [], []
            while step < len(co.co_code):
                op = ord(co.co_code[step])
                step = step + 1
                if op >= dis.HAVE_ARGUMENT:
                    opname = dis.opname[op]
                    value = ord(co.co_code[step]) + ord(co.co_code[step+1])*256
                    step = step + 2
                    if opname in ('UNPACK_TUPLE', 'UNPACK_SEQUENCE'):
                        remain.append(value)
                        count.append(value)
                    elif opname in ('STORE_FAST', 'STORE_DEREF'):
                        if op in dis.haslocal:
                            stack.append(co.co_varnames[value])
                        elif op in dis.hasfree:
                            stack.append((co.co_cellvars + co.co_freevars)[value])
                        # Special case for sublists of length 1: def foo((bar))
                        # doesn't generate the UNPACK_TUPLE bytecode, so if
                        # `remain` is empty here, we have such a sublist.
                        if not remain:
                            stack[0] = [stack[0]]
                            break
                        else:
                            remain[-1] = remain[-1] - 1
                            while remain[-1] == 0:
                                remain.pop()
                                size = count.pop()
                                stack[-size:] = [stack[-size:]]
                                if not remain:
                                    break
                                remain[-1] = remain[-1] - 1
                            if not remain:
                                break
            args[i] = stack[0]

    varargs = None
    if co.co_flags & inspect.CO_VARARGS:
        varargs = co.co_varnames[nargs]
        nargs = nargs + 1
    varkw = None
    if co.co_flags & inspect.CO_VARKEYWORDS:
        varkw = co.co_varnames[nargs]
    return inspect.Arguments(args, varargs, varkw)


# Monkeypatch inspect to apply our bugfix.
def with_patch_inspect(f):
    """decorator for monkeypatching inspect.findsource"""

    def wrapped(*args, **kwargs):
        save_findsource = inspect.findsource
        save_getargs = inspect.getargs
        inspect.findsource = findsource
        inspect.getargs = getargs
        try:
            return f(*args, **kwargs)
        finally:
            inspect.findsource = save_findsource
            inspect.getargs = save_getargs

    return wrapped


if py3compat.PY3:
    fixed_getargvalues = inspect.getargvalues
else:
    # Fixes for https://github.com/ipython/ipython/issues/8293
    #       and https://github.com/ipython/ipython/issues/8205.
    # The relevant bug is caused by failure to correctly handle anonymous tuple
    # unpacking, which only exists in Python 2.
    fixed_getargvalues = with_patch_inspect(inspect.getargvalues)


def fix_frame_records_filenames(records):
    """Try to fix the filenames in each record from inspect.getinnerframes().

    Particularly, modules loaded from within zip files have useless filenames
    attached to their code object, and inspect.getinnerframes() just uses it.
    """
    fixed_records = []
    for frame, filename, line_no, func_name, lines, index in records:
        # Look inside the frame's globals dictionary for __file__,
        # which should be better. However, keep Cython filenames since
        # we prefer the source filenames over the compiled .so file.
        filename = py3compat.cast_unicode_py2(filename, "utf-8")
        if not filename.endswith(('.pyx', '.pxd', '.pxi')):
            better_fn = frame.f_globals.get('__file__', None)
            if isinstance(better_fn, str):
                # Check the type just in case someone did something weird with
                # __file__. It might also be None if the error occurred during
                # import.
                filename = better_fn
        fixed_records.append((frame, filename, line_no, func_name, lines, index))
    return fixed_records


@with_patch_inspect
def _fixed_getinnerframes(etb, context=1, tb_offset=0):
    LNUM_POS, LINES_POS, INDEX_POS = 2, 4, 5

    records = fix_frame_records_filenames(inspect.getinnerframes(etb, context))
    # If the error is at the console, don't build any context, since it would
    # otherwise produce 5 blank lines printed out (there is no file at the
    # console)
    rec_check = records[tb_offset:]
    try:
        rname = rec_check[0][1]
        if rname == '<ipython console>' or rname.endswith('<string>'):
            return rec_check
    except IndexError:
        pass

    aux = traceback.extract_tb(etb)
    assert len(records) == len(aux)
    for i, (file, lnum, _, _) in zip(range(len(records)), aux):
        maybeStart = lnum - 1 - context // 2
        start = max(maybeStart, 0)
        end = start + context
        lines = ulinecache.getlines(file)[start:end]
        buf = list(records[i])
        buf[LNUM_POS] = lnum
        buf[INDEX_POS] = lnum - 1 - start
        buf[LINES_POS] = lines
        records[i] = tuple(buf)
    return records[tb_offset:]

# Helper function -- largely belongs to VerboseTB, but we need the same
# functionality to produce a pseudo verbose TB for SyntaxErrors, so that they
# can be recognized properly by ipython.el's py-traceback-line-re
# (SyntaxErrors have to be treated specially because they have no traceback)


def _yield_traceback_lines(lnum, index, lines, lvals=None, _parser=None):
    """
    yields each (token, value) pair from a traceback line

    `lvals` is list of token to insert just after lnum,
    that represent the locals variables.
    """

    if _parser is None:
        _parser = PyColorize.Parser(style='nocolor') 

    numbers_width = INDENT_SIZE - 1
    i = lnum - index

    for i, line in enumerate(lines, lnum - index) :
        if i == lnum:
            # This is the line with the error
            pad = numbers_width - len(str(i))
            num = debugger.make_arrow(pad) + str(i)
            yield (Token.LinenoEm, num)
        else:
            num = '%*s' % (numbers_width, i)
            yield (Token.Lineno, num)

        yield (Token.Line, ' ')
        
        line = py3compat.cast_unicode(line)
        line = _parser._lex.get_tokens(line) 
        for l in line:
            yield l

        if lvals and i == lnum:
            for l in lvals:
                yield l 



def is_recursion_error(etype, value, records):
    try:
        # RecursionError is new in Python 3.5
        recursion_error_type = RecursionError
    except NameError:
        recursion_error_type = RuntimeError

    # The default recursion limit is 1000, but some of that will be taken up
    # by stack frames in IPython itself. >500 frames probably indicates
    # a recursion error.
    print("is not recerror")
    #import pdb; pdb.set_trace()
    return (etype is recursion_error_type) \
            and "recursion" in str(value).lower() \
            and len(records) > 500

def find_recursion(etype, value, records):
    """Identify the repeating stack frames from a RecursionError traceback

    'records' is a list as returned by VerboseTB.get_records()

    Returns (last_unique, repeat_length)
    """
    # This involves a bit of guesswork - we want to show enough of the traceback
    # to indicate where the recursion is occurring. We guess that the innermost
    # quarter of the traceback (250 frames by default) is repeats, and find the
    # first frame (from in to out) that looks different.
    if not is_recursion_error(etype, value, records):
        return len(records), 0

    # Select filename, lineno, func_name to track frames with
    records = [r[1:4] for r in records]
    inner_frames = records[-(len(records)//4):]
    frames_repeated = set(inner_frames)

    last_seen_at = {}
    longest_repeat = 0
    i = len(records)
    for frame in reversed(records):
        i -= 1
        if frame not in frames_repeated:
            last_unique = i
            break

        if frame in last_seen_at:
            distance = last_seen_at[frame] - i
            longest_repeat = max(longest_repeat, distance)

        last_seen_at[frame] = i
    else:
        last_unique = 0 # The whole traceback was recursion

def is_recursion_error(etype, value, records):
    try:
        # RecursionError is new in Python 3.5
        recursion_error_type = RecursionError
    except NameError:
        recursion_error_type = RuntimeError

    # The default recursion limit is 1000, but some of that will be taken up
    # by stack frames in IPython itself. >500 frames probably indicates
    # a recursion error.
    return (etype is recursion_error_type) \
           and "recursion" in str(value).lower() \
           and len(records) > 500

def find_recursion(etype, value, records):
    """Identify the repeating stack frames from a RecursionError traceback

    'records' is a list as returned by VerboseTB.get_records()

    Returns (last_unique, repeat_length)
    """
    # This involves a bit of guesswork - we want to show enough of the traceback
    # to indicate where the recursion is occurring. We guess that the innermost
    # quarter of the traceback (250 frames by default) is repeats, and find the
    # first frame (from in to out) that looks different.
    if not is_recursion_error(etype, value, records):
        return len(records), 0

    # Select filename, lineno, func_name to track frames with
    records = [r[1:4] for r in records]
    inner_frames = records[-(len(records)//4):]
    frames_repeated = set(inner_frames)

    last_seen_at = {}
    longest_repeat = 0
    i = len(records)
    for frame in reversed(records):
        i -= 1
        if frame not in frames_repeated:
            last_unique = i
            break

        if frame in last_seen_at:
            distance = last_seen_at[frame] - i
            longest_repeat = max(longest_repeat, distance)

        last_seen_at[frame] = i
    else:
        last_unique = 0 # The whole traceback was recursion

    return last_unique, longest_repeat

#---------------------------------------------------------------------------
# Module classes
class TBTools(colorable.Colorable):
    """Basic tools used by all traceback printer classes."""

    # Number of frames to skip when reporting tracebacks
    tb_offset = 0

    def __init__(self, color_scheme='NoColor', call_pdb=False, ostream=None, parent=None, config=None):
        # Whether to call the interactive pdb debugger after printing
        # tracebacks or not
        #if not parent: 
        super(TBTools, self).__init__(parent=parent, config=config)
        self.call_pdb = call_pdb
        self._parser = PyColorize.Parser(style=color_scheme, parent=self)

        # Output stream to write to.  Note that we store the original value in
        # a private attribute and then make the public ostream a property, so
        # that we can delay accessing io.stdout until runtime.  The way
        # things are written now, the io.stdout object is dynamically managed
        # so a reference to it should NEVER be stored statically.  This
        # property approach confines this detail to a single location, and all
        # subclasses can simply access self.ostream for writing.
        self._ostream = ostream

        self.set_colors(color_scheme)

        if call_pdb:
            self.pdb = debugger.Pdb(self.style)
        else:
            self.pdb = None

    @property
    def Colors(self):
        warnings.warn("%s.Colors is deprecated and will be removed in IPython 6.0" % self.__class__, DeprecationWarning)

    @Colors.setter
    def Colors(self, value):
        warnings.warn("%s.Colors is deprecated and will be removed in IPython 6.0" % self.__class__, DeprecationWarning)


    def _get_ostream(self):
        """Output stream that exceptions are written to.

        Valid values are:

        - None: the default, which means that IPython will dynamically resolve
          to io.stdout.  This ensures compatibility with most tools, including
          Windows (where plain stdout doesn't recognize ANSI escapes).

        - Any object with 'write' and 'flush' attributes.
        """
        return io.stdout if self._ostream is None else self._ostream

    def _set_ostream(self, val):
        assert val is None or (hasattr(val, 'write') and hasattr(val, 'flush'))
        self._ostream = val

    ostream = property(_get_ostream, _set_ostream)

    def set_colors(self, scheme):
        """Shorthand access to the color table scheme selector method."""
        self.style = scheme
        self._parser.style = scheme
        if hasattr(self, 'pdb') and self.pdb is not None:
            self.pdb.set_colors(scheme=scheme)

    def color_toggle(self):
        """Toggle between the currently active color scheme and NoColor."""
        warnings.warn("color toggle has been deprecated", DeprecationWarning)


    def stb2text(self, stb):
        """Convert a structured traceback (a list) to a string."""
        return '\n'.join(stb)

    def text(self, etype, value, tb, tb_offset=None, context=5):
        """Return formatted traceback.

        Subclasses may override this if they add extra arguments.
        """
        tb_list = self.structured_traceback(etype, value, tb,
                                            tb_offset, context)
        return self.stb2text(tb_list)

    def structured_traceback(self, etype, evalue, tb, tb_offset=None,
                             context=5, mode=None):
        """Return a list of traceback frames.

        Must be implemented by each class.
        """
        raise NotImplementedError()


#---------------------------------------------------------------------------
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

    def __init__(self, color_scheme='NoColor', call_pdb=False, ostream=None, parent=None):
        TBTools.__init__(self, color_scheme=color_scheme, call_pdb=call_pdb,
                         ostream=ostream, parent=parent)

    def __call__(self, etype, value, elist):
        self.ostream.flush()
        self.ostream.write(self.text(etype, value, elist))
        self.ostream.write('\n')

    def structured_traceback(self, etype, value, elist, tb_offset=None,
                             context=5):
        """Return a color formatted string with the traceback info.

        Parameters
        ----------
        etype : exception type
          Type of the exception raised.

        value : object
          Data stored in the exception

        elist : list
          List of frames, see class docstring for details.

        tb_offset : int, optional
          Number of frames in the traceback to skip.  If not given, the
          instance value is used (set in constructor).

        context : int, optional
          Number of lines of context information to print.

        Returns
        -------
        String with formatted exception.
        """
        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        out_list = []
        if elist:

            if tb_offset and len(elist) > tb_offset:
                elist = elist[tb_offset:]

            out_list.append(self._parser.fmt((Token.Normal, 'Traceback '),
                                     (Token.NormalEm, '(most recent call last)'),
                                     (Token.Normal,':\n')))
            out_list.extend(self._format_list(elist))
        # The exception info should be a single entry in the list.
        # TODO : Bytes or string Py2 ?
        fe = self._format_exception_only(etype, value)
        lines = '<none>'
        # TODO: don't make sens, if we join, it's a list, 
        # if it's a list we can't  call str_to_unicode on it
        dfe = py3compat.str_to_unicode(fe)
        lines = u''.join(dfe)

        lines = lines + '\n'
        out_list.append(lines)

        return out_list

    # TODO: refactor to yield
    def _format_list(self, extracted_list):
        """Format a list of traceback entry tuples for printing.

        Given a list of tuples as returned by extract_tb() or
        extract_stack(), return a list of strings ready for printing.
        Each string in the resulting list corresponds to the item with the
        same index in the argument list.  Each string ends in a newline;
        the strings may contain internal newlines as well, for those items
        whose source text line is not None.

        Lifted almost verbatim from traceback.py
        """
        return [self._parser.fmt(*x) for x in self._yield_format_list(extracted_list)]
        

    def _yield_format_list(self, extracted_list):
        for filename, lineno, name, line in extracted_list[:-1]:
            item = [ (Token.Normal,   "  File "),
                     (Token.Filename, '"%s"' % py3compat.cast_unicode_py2(filename, "utf-8") ),
                     (Token.Normal, ', line '),
                     (Token.Lineno, '%s' % lineno),
                     (Token.Normal, ', in '),
                     (Token.Name, py3compat.cast_unicode_py2(name, "utf-8") ),
                     (Token.Normal, '\n'),
                    ]
            if line:
                item.append((Token.Normal, '    %s\n' % line.strip()))
            yield item
        # Emphasize the last entry
        filename, lineno, name, line = extracted_list[-1]
        item = [ (Token.Normal,     '  File '),
                 (Token.FilenameEm, '"%s"' %  py3compat.cast_unicode_py2(filename, "utf-8") ),
                 (Token.NormalEm,   ', line '),
                 (Token.LinenoEm,   '%s' % lineno),
                 (Token.NormalEm,   ', in '),
                 (Token.NameEm, py3compat.cast_unicode_py2(name, "utf-8") ),
                 (Token.Normal,     '\n'),
                    ]
        if line:
            item.append((Token.Line, '    %s\n' % line.strip()))

        yield item

    def _format_exception_only(self, etype, value):
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
        return self._parser.fmt(*self._yield_from_format_exception_only(etype, value))

    def _yield_from_format_exception_only(self, etype, value):
        have_filedata = False
        stype = (Token.ExcName, etype.__name__)
        if value is None:
            # Not sure if this can still happen in Python 2.6 and above
            yield stype
            yield (Token.Normal,'\n')
        else:
            if issubclass(etype, SyntaxError):
                have_filedata = True
                if not value.filename: value.filename = "<string>"
                if value.lineno:
                    lineno = value.lineno
                    textline = ulinecache.getline(value.filename, value.lineno)
                else:
                    lineno = ' unknown'
                    textline = ''
                yield (Token.NormalEm, '  File ')
                yield (Token.FileNameEm, '"'+py3compat.cast_unicode(value.filename+'"'))
                yield (Token.NormalEm, ', line')
                yield (Token.LineNoEm, str(lineno))
                yield (Token.Normal, '\n')

                if textline == '':
                    textline = py3compat.cast_unicode(value.text, "utf-8")

                if textline is not None:
                    i = 0
                    while i < len(textline) and textline[i].isspace():
                        i += 1
                    yield (Token.Line, '    '+textline.strip())
                    if value.offset is not None:
                        s = '\n    '
                        for c in textline[i:value.offset - 1]:
                            if c.isspace():
                                s += c
                            else:
                                s += ' '
                        yield (Token.Carret, s+'^\n')

            try:
                s = value.msg
            except Exception:
                s = self._some_str(value)
            yield stype
            
            if s:
                yield (Token.ExcName, ':')
                yield (Token.Normal,  ' '+s)
            else:
                yield (Token.Normal, '\n' )

        # sync with user hooks
        if have_filedata:
            ipinst = get_ipython()
            if ipinst is not None:
                ipinst.hooks.synchronize_with_editor(value.filename, value.lineno, 0)

    def get_exception_only(self, etype, value):
        """Only print the exception type and message, without a traceback.

        Parameters
        ----------
        etype : exception type
        value : exception value
        """
        # TODO: ListTB here seem like it can be `self..` check why
        return ListTB.structured_traceback(self, etype, value, [])

    def show_exception_only(self, etype, evalue):
        """Only print the exception type and message, without a traceback.

        Parameters
        ----------
        etype : exception type
        value : exception value
        """
        # This method needs to use __call__ from *this* class, not the one from
        # a subclass whose signature or behavior may be different
        ostream = self.ostream
        ostream.flush()
        ostream.write('\n'.join(self.get_exception_only(etype, evalue)))
        ostream.flush()

    def _some_str(self, value):
        # Lifted from traceback.py
        try:
            return str(value)
        except:
            return '<unprintable %s object>' % type(value).__name__


#----------------------------------------------------------------------------
class VerboseTB(TBTools):
    """A port of Ka-Ping Yee's cgitb.py module that outputs color text instead
    of HTML.  Requires inspect and pydoc.  Crazy, man.

    Modified version which optionally strips the topmost entries from the
    traceback, to be used with alternate interpreters (because their own code
    would appear in the traceback)."""

    def __init__(self, color_scheme='Linux', call_pdb=False, ostream=None,
                 tb_offset=0, long_header=False, include_vars=True,
                 check_cache=None, parent=None):
        """Specify traceback offset, headers and color scheme.

        Define how many frames to drop from the tracebacks. Calling it with
        tb_offset=1 allows use of this handler in interpreters which will have
        their own code at the top of the traceback (VerboseTB will first
        remove that frame before printing the traceback info)."""
        TBTools.__init__(self, color_scheme=color_scheme, call_pdb=call_pdb,
                         ostream=ostream, parent=parent)
        self.tb_offset = tb_offset
        self.long_header = long_header
        self.include_vars = include_vars
        # By default we use linecache.checkcache, but the user can provide a
        # different check_cache implementation.  This is used by the IPython
        # kernel to provide tracebacks for interactive code that is cached,
        # by a compiler instance that flushes the linecache but preserves its
        # own code cache.
        if check_cache is None:
            check_cache = linecache.checkcache
        self.check_cache = check_cache

    # TODO: docstring
    # TODO: function seem likely too long, and too complex. 
#    def _format_records(self, records):
#        for record in records:
#            yield from self._format_record(record)

    def _format_records(self, records, last_unique, recursion_repeat):
        """Format the stack frames of the traceback"""
        for r in records[:last_unique+recursion_repeat+1]:
            #print '*** record:',file,lnum,func,lines,index  # dbg
            yield from self._format_record(r)

        if recursion_repeat:
            yield [(Token.Normal, '... last %d frames repeated, from the frame below ...\n' % recursion_repeat)]
            yield from self._format_record(records[last_unique+recursion_repeat+1])



    def _format_record(self, record):
        indent = ' ' * INDENT_SIZE

        undefined = (Token.Em, 'undefined')
        
        # build some color string templates outside these nested loops
        _ycall = lambda x,y: [(Token.Normal, 'in '), (Token.VName, x), (Token.ValEm, y), (Token.Normal, '\n')]

        ValEm = lambda value : (Token.ValEm, value )

        abspath = os.path.abspath
        frame, file, lnum, func, lines, index  = record

        if not file:
            file = '?'
        elif file.startswith(str("<")) and file.endswith(str(">")):
            # Not a real filename, no problem...
            pass
        elif not os.path.isabs(file):
            # Try to make the filename absolute by trying all
            # sys.path entries (which is also what linecache does)
            for dirname in sys.path:
                try:
                    fullname = os.path.join(dirname, file)
                    if os.path.isfile(fullname):
                        file = os.path.abspath(fullname)
                        break
                except Exception:
                    # Just in case that sys.path contains very
                    # strange entries...
                    pass

        file = py3compat.cast_unicode(file, util_path.fs_encoding)
        ylink = file
        args, varargs, varkw, locals = fixed_getargvalues(frame)

        if func == '?':
            ycall = [(Token.Normal, '')]
        else:
            # Decide whether to include variable details or not
            var_repr = self.include_vars and eqrepr or nullrepr
            try:
                ycall = _ycall(func, inspect.formatargvalues(args,
                                                                    varargs, varkw,
                                                                    locals, formatvalue=var_repr))
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
                ycall = _ycall (func, "(***failed resolving arguments***)")

        # Don't attempt to tokenize binary files.
        if file.endswith(('.so', '.pyd', '.dll')):
            yield [(Token.Link, ylink), (Token.Normal, ' ') ] + ycall
            return
        elif file.endswith(('.pyc', '.pyo')):
            # Look up the corresponding source file.
            file = openpy.source_from_cache(file)

        # TODO: closure with on purpose mutable default argument
        # used as a generator. refactor that as a real generator. 
        # TODO: the kwarg getline seem useless too as this is a closure. 
        def linereader(file=file, lnum=[lnum], getline=ulinecache.getline):
            line = getline(file, lnum[0])
            lnum[0] += 1
            return line

        # Build the list of names on this line of code where the exception
        # occurred.
        try:
            names = []
            name_cont = False

            for token_type, token, start, end, line in generate_tokens(linereader):
                # build composite names
                if token_type == tokenize.NAME and token not in keyword.kwlist:
                    if name_cont:
                        # Continuation of a dotted name
                        try:
                            names[-1].append(token)
                        except IndexError:
                            names.append([token])
                        name_cont = False
                    else:
                        # Regular new names.  We append everything, the caller
                        # will be responsible for pruning the list later.  It's
                        # very tricky to try to prune as we go, b/c composite
                        # names can fool us.  The pruning at the end is easy
                        # to do (or the caller can print a list with repeated
                        # names if so desired.
                        names.append([token])
                elif token == '.':
                    name_cont = True
                elif token_type == tokenize.NEWLINE:
                    break

        except (IndexError, UnicodeDecodeError, SyntaxError):
            # signals exit of tokenizer
            # SyntaxError can occur if the file is not actually Python
            #  - see gh-6300
            pass
        except tokenize.TokenError as msg:
            _m = ("An unexpected error occurred while tokenizing input\n"
                  "The following traceback may be corrupted or invalid\n"
                  "The error message is: %s\n" % msg)
            error(_m)

        # Join composite names (e.g. "dict.fromkeys")
        names = ['.'.join(n) for n in names]
        # prune names list of duplicates, but keep the right order
        unique_names = uniq_stable(names)

        # Start loop over vars
        lvals = []
        if self.include_vars:
            for name_full in unique_names:
                name_base = name_full.split('.', 1)[0]
                if name_base in frame.f_code.co_varnames:
                    if name_base in locals:
                        try:
                            value = ValEm(repr(eval(name_full, locals)))
                        except:
                            value = undefined
                    else:
                        value = undefined
                    name = ((Token.VName, name_full),)
                else:
                    if name_base in frame.f_globals:
                        try:
                            value = ValEm(repr(eval(name_full, frame.f_globals)))
                        except:
                            value = undefined
                    else:
                        value = undefined
                    name = ((Token.Em, 'global '), (Token.VName, name_full))

                lvals.append((Token.Normal, indent))
                lvals.extend(name)
                lvals.append((Token.ValEm, ' = ' ))
                lvals.append(value)
                lvals.append((Token.Normal, '\n'))
        if not lvals:
            lvals = ()

        yt = [(Token.Link, ylink), (Token.Normal, ' ') ] + ycall
        if index is not None:
            yt = yt + list(_yield_traceback_lines(lnum, index, lines, lvals, _parser=self._parser))

        yield yt

    # TODO: likely refactor to yield or list comprehension
    def format_records(self, records, last_unique, recursion_repeat):
        rcds = self._format_records(records, last_unique, recursion_repeat)
        return [ self._parser.fmt(*x) for x in rcds]

    def prepare_chained_exception_message(self, cause):
        direct_cause = "\nThe above exception was the direct cause of the following exception:\n"
        exception_during_handling = "\nDuring handling of the above exception, another exception occurred:\n"

        if cause:
            message = [[direct_cause]]
        else:
            message = [[exception_during_handling]]
        return message

    def prepare_header(self, etype, long_version=False):


        if long_version:
            # Header with the exception type, python version, and date
            pyver = 'Python ' + sys.version.split()[0] + ': ' + sys.executable
            date = time.ctime(time.time())

            head = ((Token.Topline, '-'*LINE_LENGTH),
                    (Token.Normal,  '\n'),
                    (Token.ExcName, etype),
                    (Token.Normal,  ' ' * (LINE_LENGTH - len(str(etype)) - len(pyver))), 
                    (Token.Normal,  pyver), 
                    (Token.Normal,  date.rjust(LINE_LENGTH)), 
                    (Token.Normal,  "\nA problem occurred executing Python code.  Here is the sequence of function" \
                                    "\ncalls leading up to the error, with the most recent (innermost) call last."))
                      
        else:
            # Simplified header
            head = ((Token.ExcName, etype),
                    (Token.Normal, 'Traceback (most recent call last)'.  rjust(LINE_LENGTH - len(str(etype)))))

        return self._parser.fmt(*head)

    # TODO: docstring
    def format_exception(self, etype, evalue):
        # TODO: list comprehension seem more suitable.
        return list(map(lambda _: self._parser.fmt(*_), self._format_exception_tokens(etype, evalue)))

    def _format_exception_tokens(self, etype, evalue):
        indent = ' ' * INDENT_SIZE
        # Get (safely) a string form of the exception info
        try:
            etype_str, evalue_str = map(str, (etype, evalue))
        except:
            # User exception is improperly defined.
            etype, evalue = str, sys.exc_info()[:2]
            etype_str, evalue_str = map(str, (etype, evalue))
        # ... and format it
        yield (
                (Token.EcxName, etype_str),
                (Token.Normal, ': '),
                (Token.Normal, py3compat.cast_unicode(evalue_str))
                )

        if (not py3compat.PY3) and type(evalue) is types.InstanceType:
            try:
                names = [w for w in dir(evalue) if isinstance(w, py3compat.string_types)]
            except:
                # Every now and then, an object with funny internals blows up
                # when dir() is called on it.  We do the best we can to report
                # the problem and continue
                _m = 'Exception reporting error (object with broken dir())'
                # TODO, likely not tested as bug, but test pass.
                yield ((Token.ExcName, _m), (Token.Normal, ':'))
                etype_str, evalue_str = map(str, sys.exc_info()[:2])
                yield ( (Token.ExcName, etype_str), 
                        (Token.Normal, ': '), 
                        (Token.Normal, py3compat.cast_unicode(evalue_str))
                      )
                names = []
            for name in names:
                value = text_repr(getattr(evalue, name))
                # TODO, likely not tested as bug, but test pass.
                yield (
                    (Token.Normal, indent)
                    (Token.Normal, name),
                    (Token.Normal, ' = '),
                    (Token.Normal, value),
                    )

    def format_exception_as_a_whole(self, etype, evalue, etb, number_of_lines_of_context, tb_offset):
        """Formats the header, traceback and exception message for a single exception.

        This may be called multiple times by Python 3 exception chaining
        (PEP 3134).
        """
        # some locals
        orig_etype = etype
        try:
            etype = etype.__name__
        except AttributeError:
            pass

        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        head = self.prepare_header(etype, self.long_header)
        records = self.get_records(etb, number_of_lines_of_context, tb_offset)

        if records is None:
            return ""
        
        # TODO revert this after rebase
        last_unique, recursion_repeat = find_recursion(orig_etype, evalue, records)

        frames = self.format_records(records, last_unique, recursion_repeat)

        formatted_exception = self.format_exception(etype, evalue)
        if records:
            filepath, lnum = records[-1][1:3]
            filepath = os.path.abspath(filepath)
            ipinst = get_ipython()
            if ipinst is not None:
                ipinst.hooks.synchronize_with_editor(filepath, lnum, 0)

        return [[head] + frames + [''.join(formatted_exception[0])]]

    def get_records(self, etb, number_of_lines_of_context, tb_offset):
        try:
            # Try the default getinnerframes and Alex's: Alex's fixes some
            # problems, but it generates empty tracebacks for console errors
            # (5 blanks lines) where none should be returned.
            return _fixed_getinnerframes(etb, number_of_lines_of_context, tb_offset)
        except:
            # FIXME: I've been getting many crash reports from python 2.3
            # users, traceable to inspect.py.  If I can find a small test-case
            # to reproduce this, I should either write a better workaround or
            # file a bug report against inspect (if that's the real problem).
            # So far, I haven't been able to find an isolated example to
            # reproduce the problem.
            inspect_error()
            traceback.print_exc(file=self.ostream)
            info('\nUnfortunately, your original traceback can not be constructed.\n')
            return None

    def get_parts_of_chained_exception(self, evalue):
        def get_chained_exception(exception_value):
            cause = getattr(exception_value, '__cause__', None)
            if cause:
                return cause
            if getattr(exception_value, '__suppress_context__', False):
                return None
            return getattr(exception_value, '__context__', None)

        chained_evalue = get_chained_exception(evalue)

        if chained_evalue:
            return chained_evalue.__class__, chained_evalue, chained_evalue.__traceback__

    def structured_traceback(self, etype, evalue, etb, tb_offset=None,
                             number_of_lines_of_context=5):
        """Return a nice text document describing the traceback."""

        formatted_exception = self.format_exception_as_a_whole(etype, evalue, etb, number_of_lines_of_context,
                                                               tb_offset)

        head = self._parser.fmt((Token.Topline, '-' * LINE_LENGTH))
        structured_traceback_parts = [head]
        if py3compat.PY3:
            chained_exceptions_tb_offset = 0
            lines_of_context = 3
            formatted_exceptions = formatted_exception
            exception = self.get_parts_of_chained_exception(evalue)
            if exception:
                formatted_exceptions += self.prepare_chained_exception_message(evalue.__cause__)
                etype, evalue, etb = exception
            else:
                evalue = None
            chained_exc_ids = set()
            while evalue:
                formatted_exceptions += self.format_exception_as_a_whole(etype, evalue, etb, lines_of_context,
                                                                         chained_exceptions_tb_offset)
                exception = self.get_parts_of_chained_exception(evalue)

                if exception and not id(exception[1]) in chained_exc_ids:
                    chained_exc_ids.add(id(exception[1])) # trace exception to avoid infinite 'cause' loop
                    formatted_exceptions += self.prepare_chained_exception_message(evalue.__cause__)
                    etype, evalue, etb = exception
                else:
                    evalue = None

            # we want to see exceptions in a reversed order:
            # the first exception should be on top
            for formatted_exception in reversed(formatted_exceptions):
                structured_traceback_parts += formatted_exception
        else:
            structured_traceback_parts += formatted_exception[0]

        # TODO check unicode/byte Py2/3
        # TODO: list comprehension
        dfe = list(map(py3compat.str_to_unicode, structured_traceback_parts))
        return dfe

    def debugger(self, force=False):
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
                self.pdb = debugger.Pdb(
                    self.style)
            # the system displayhook may have changed, restore the original
            # for pdb
            display_trap = DisplayTrap(hook=sys.__displayhook__)
            with display_trap:
                self.pdb.reset()
                # Find the right frame so we don't pop up inside ipython itself
                if hasattr(self, 'tb') and self.tb is not None:
                    etb = self.tb
                else:
                    etb = self.tb = sys.last_traceback
                while self.tb is not None and self.tb.tb_next is not None:
                    self.tb = self.tb.tb_next
                if etb and etb.tb_next:
                    etb = etb.tb_next
                self.pdb.botframe = etb.tb_frame
                self.pdb.interaction(self.tb.tb_frame, self.tb)

        if hasattr(self, 'tb'):
            del self.tb

    def handler(self, info=None):
        (etype, evalue, etb) = info or sys.exc_info()
        self.tb = etb
        ostream = self.ostream
        ostream.flush()
        ostream.write(self.text(etype, evalue, etb))
        ostream.write('\n')
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


#----------------------------------------------------------------------------
class FormattedTB(VerboseTB, ListTB):
    """Subclass ListTB but allow calling with a traceback.

    It can thus be used as a sys.excepthook for Python > 2.1.

    Also adds 'Context' and 'Verbose' modes, not available in ListTB.

    Allows a tb_offset to be specified. This is useful for situations where
    one needs to remove a number of topmost frames from the traceback (such as
    occurs with python programs that themselves execute other python code,
    like Python shells).  """

    def __init__(self, mode='Plain', color_scheme='Linux', call_pdb=False,
                 ostream=None,
                 tb_offset=0, long_header=False, include_vars=False,
                 check_cache=None, parent=None):

        # NEVER change the order of this list. Put new modes at the end:
        self.valid_modes = ['Plain', 'Context', 'Verbose']
        self.verbose_modes = self.valid_modes[1:3]

        VerboseTB.__init__(self, color_scheme=color_scheme, call_pdb=call_pdb,
                           ostream=ostream, tb_offset=tb_offset,
                           long_header=long_header, include_vars=include_vars,
                           check_cache=check_cache, parent=parent)

        # Different types of tracebacks are joined with different separators to
        # form a single string.  They are taken from this dict
        self._join_chars = dict(Plain='', Context='\n', Verbose='\n')
        # set_mode also sets the tb_join_char attribute
        self.set_mode(mode)

    def _extract_tb(self, tb):
        if tb:
            return traceback.extract_tb(tb)
        else:
            return None

    def structured_traceback(self, etype, value, tb, tb_offset=None, number_of_lines_of_context=5):
        tb_offset = self.tb_offset if tb_offset is None else tb_offset
        mode = self.mode
        if mode in self.verbose_modes:
            # Verbose modes need a full traceback
            return VerboseTB.structured_traceback(
                self, etype, value, tb, tb_offset, number_of_lines_of_context
            )
        else:
            # We must check the source cache because otherwise we can print
            # out-of-date source code.
            self.check_cache()
            # Now we can extract and format the exception
            elist = self._extract_tb(tb)
            return ListTB.structured_traceback(
                self, etype, value, elist, tb_offset, number_of_lines_of_context
            )

    def stb2text(self, stb):
        """Convert a structured traceback (a list) to a string."""
        return self.tb_join_char.join(stb)


    def set_mode(self, mode=None):
        """Switch to the desired mode.

        If mode is not specified, cycles through the available modes."""

        if not mode:
            new_idx = (self.valid_modes.index(self.mode) + 1 ) % \
                      len(self.valid_modes)
            self.mode = self.valid_modes[new_idx]
        elif mode not in self.valid_modes:
            raise ValueError('Unrecognized mode in FormattedTB: <' + mode + '>\n'
                                                                            'Valid modes: ' + str(self.valid_modes))
        else:
            self.mode = mode
        # include variable details only in 'Verbose' mode
        self.include_vars = (self.mode == self.valid_modes[2])
        # Set the join character for generating text tracebacks
        self.tb_join_char = self._join_chars[self.mode]

    # some convenient shortcuts
    def plain(self):
        self.set_mode(self.valid_modes[0])

    def context(self):
        self.set_mode(self.valid_modes[1])

    def verbose(self):
        self.set_mode(self.valid_modes[2])


#----------------------------------------------------------------------------
class AutoFormattedTB(FormattedTB):
    """A traceback printer which can be called on the fly.

    It will find out about exceptions by itself.

    A brief example::

        AutoTB = AutoFormattedTB(mode = 'Verbose',color_scheme='Linux')
        try:
          ...
        except:
          AutoTB()  # or AutoTB(out=logfile) where logfile is an open file object
    """

    def __call__(self, etype=None, evalue=None, etb=None,
                 out=None, tb_offset=None):
        """Print out a formatted exception traceback.

        Optional arguments:
          - out: an open file-like object to direct output to.

          - tb_offset: the number of frames to skip over in the stack, on a
          per-call basis (this overrides temporarily the instance's tb_offset
          given at initialization time.  """

        if out is None:
            out = self.ostream
        out.flush()
        out.write(self.text(etype, evalue, etb, tb_offset))
        out.write('\n')
        out.flush()
        # FIXME: we should remove the auto pdb behavior from here and leave
        # that to the clients.
        try:
            self.debugger()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")

    def structured_traceback(self, etype=None, value=None, tb=None,
                             tb_offset=None, number_of_lines_of_context=5):
        if etype is None:
            etype, value, tb = sys.exc_info()
        self.tb = tb
        # TODO: Py23/bytestr
        return FormattedTB.structured_traceback(
            self, etype, value, tb, tb_offset, number_of_lines_of_context)


#---------------------------------------------------------------------------

# A simple class to preserve Nathan's original functionality.
class ColorTB(FormattedTB):
    """Shorthand to initialize a FormattedTB in Linux colors mode."""

    def __init__(self, color_scheme='Linux', call_pdb=0, **kwargs):
        FormattedTB.__init__(self, color_scheme=color_scheme,
                             call_pdb=call_pdb, **kwargs)


class SyntaxTB(ListTB):
    """Extension which holds some state: the last exception value"""

    def __init__(self, color_scheme='NoColor', parent=None):
        ListTB.__init__(self, color_scheme, parent=parent)
        self.last_syntax_error = None

    def __call__(self, etype, value, elist):
        self.last_syntax_error = value

        ListTB.__call__(self, etype, value, elist)

    def structured_traceback(self, etype, value, elist, tb_offset=None,
                             context=5):
        # If the source file has been edited, the line in the syntax error can
        # be wrong (retrieved from an outdated cache). This replaces it with
        # the current value.
        if isinstance(value, SyntaxError) \
                and isinstance(value.filename, py3compat.string_types) \
                and isinstance(value.lineno, int):
            linecache.checkcache(value.filename)
            newtext = ulinecache.getline(value.filename, value.lineno)
            if newtext:
                value.text = newtext
        return super(SyntaxTB, self).structured_traceback(etype, value, elist,
                                                          tb_offset=tb_offset, context=context)

    def clear_err_state(self):
        """Return the current error state and clear it"""
        e = self.last_syntax_error
        self.last_syntax_error = None
        return e

    def stb2text(self, stb):
        """Convert a structured traceback (a list) to a string."""
        return ''.join(stb)


# some internal-use functions
def text_repr(value):
    """Hopefully pretty robust repr equivalent."""
    # this is pretty horrible but should always return *something*
    try:
        return pydoc.text.repr(value)
    except KeyboardInterrupt:
        raise
    except:
        try:
            return repr(value)
        except KeyboardInterrupt:
            raise
        except:
            try:
                # all still in an except block so we catch
                # getattr raising
                name = getattr(value, '__name__', None)
                if name:
                    # ick, recursion
                    return text_repr(name)
                klass = getattr(value, '__class__', None)
                if klass:
                    return '%s instance' % text_repr(klass)
            except KeyboardInterrupt:
                raise
            except:
                return 'UNRECOVERABLE REPR FAILURE'


def eqrepr(value, repr=text_repr):
    return '=%s' % repr(value)


def nullrepr(value, repr=text_repr):
    return ''

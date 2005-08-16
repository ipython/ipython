# -*- coding: utf-8 -*-
"""
ultraTB.py -- Spice up your tracebacks!

* ColorTB
I've always found it a bit hard to visually parse tracebacks in Python.  The
ColorTB class is a solution to that problem.  It colors the different parts of a
traceback in a manner similar to what you would expect from a syntax-highlighting
text editor.

Installation instructions for ColorTB:
    import sys,ultraTB
    sys.excepthook = ultraTB.ColorTB()

* VerboseTB  
I've also included a port of Ka-Ping Yee's "cgitb.py" that produces all kinds
of useful info when a traceback occurs.  Ping originally had it spit out HTML
and intended it for CGI programmers, but why should they have all the fun?  I
altered it to spit out colored text to the terminal.  It's a bit overwhelming,
but kind of neat, and maybe useful for long-running programs that you believe
are bug-free.  If a crash *does* occur in that type of program you want details.
Give it a shot--you'll love it or you'll hate it.

Note:

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
  

Installation instructions for ColorTB:
    import sys,ultraTB
    sys.excepthook = ultraTB.VerboseTB()

Note:  Much of the code in this module was lifted verbatim from the standard
library module 'traceback.py' and Ka-Ping Yee's 'cgitb.py'.

* Color schemes
The colors are defined in the class TBTools through the use of the
ColorSchemeTable class. Currently the following exist:

  - NoColor: allows all of this module to be used in any terminal (the color
  escapes are just dummy blank strings).

  - Linux: is meant to look good in a terminal like the Linux console (black
  or very dark background).

  - LightBG: similar to Linux but swaps dark/light colors to be more readable
  in light background terminals.

You can implement other color schemes easily, the syntax is fairly
self-explanatory. Please send back new schemes you develop to the author for
possible inclusion in future releases.

$Id: ultraTB.py 703 2005-08-16 17:34:44Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001 Nathaniel Gray <n8gray@caltech.edu>
#       Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>\n%s <%s>' % (Release.authors['Nathan']+
                                    Release.authors['Fernando'])
__license__ = Release.license

# Required modules
import sys, os, traceback, types, string, time
import keyword, tokenize, linecache, inspect, pydoc
from UserDict import UserDict

# IPython's own modules
# Modified pdb which doesn't damage IPython's readline handling
from IPython import Debugger

from IPython.Struct import Struct
from IPython.ColorANSI import *
from IPython.genutils import Term,uniq_stable,error,info

#---------------------------------------------------------------------------
# Code begins

def inspect_error():
    """Print a message about internal inspect errors.

    These are unfortunately quite common."""
    
    error('Internal Python error in the inspect module.\n'
          'Below is the traceback from this internal error.\n')

# Make a global variable out of the color scheme table used for coloring
# exception tracebacks.  This allows user code to add new schemes at runtime.
ExceptionColors = ColorSchemeTable()

# Populate it with color schemes
C = TermColors # shorthand and local lookup
ExceptionColors.add_scheme(ColorScheme(
    'NoColor',
    # The color to be used for the top line
    topline = C.NoColor,

    # The colors to be used in the traceback
    filename = C.NoColor,
    lineno = C.NoColor,
    name = C.NoColor,
    vName = C.NoColor,
    val = C.NoColor,
    em = C.NoColor,
    
    # Emphasized colors for the last frame of the traceback
    normalEm = C.NoColor,
    filenameEm = C.NoColor,
    linenoEm = C.NoColor,
    nameEm = C.NoColor,
    valEm = C.NoColor,
    
    # Colors for printing the exception
    excName = C.NoColor,
    line = C.NoColor,
    caret = C.NoColor,
    Normal = C.NoColor
    ))

# make some schemes as instances so we can copy them for modification easily
ExceptionColors.add_scheme(ColorScheme(
    'Linux',
    # The color to be used for the top line
    topline = C.LightRed,

    # The colors to be used in the traceback
    filename = C.Green,
    lineno = C.Green,
    name = C.Purple,
    vName = C.Cyan,
    val = C.Green,
    em = C.LightCyan,

    # Emphasized colors for the last frame of the traceback
    normalEm = C.LightCyan,
    filenameEm = C.LightGreen,
    linenoEm = C.LightGreen,
    nameEm = C.LightPurple,
    valEm = C.LightBlue,

    # Colors for printing the exception
    excName = C.LightRed,
    line = C.Yellow,
    caret = C.White,
    Normal = C.Normal
    ))

# For light backgrounds, swap dark/light colors
ExceptionColors.add_scheme(ColorScheme(
    'LightBG',
    # The color to be used for the top line
    topline = C.Red,
    
    # The colors to be used in the traceback
    filename = C.LightGreen,
    lineno = C.LightGreen,
    name = C.LightPurple,
    vName = C.Cyan,
    val = C.LightGreen,
    em = C.Cyan,

    # Emphasized colors for the last frame of the traceback
    normalEm = C.Cyan,
    filenameEm = C.Green,
    linenoEm = C.Green,
    nameEm = C.Purple,
    valEm = C.Blue,

    # Colors for printing the exception
    excName = C.Red,
    #line = C.Brown,  # brown often is displayed as yellow
    line = C.Red,
    caret = C.Normal,
    Normal = C.Normal
    ))

class TBTools:
    """Basic tools used by all traceback printer classes."""

    def __init__(self,color_scheme = 'NoColor',call_pdb=0):
        # Whether to call the interactive pdb debugger after printing
        # tracebacks or not
        self.call_pdb = call_pdb
        if call_pdb:
            self.pdb = Debugger.Pdb()
        else:
            self.pdb = None

        # Create color table
        self.ColorSchemeTable = ExceptionColors 

        self.set_colors(color_scheme)
        self.old_scheme = color_scheme  # save initial value for toggles

    def set_colors(self,*args,**kw):
        """Shorthand access to the color table scheme selector method."""
        
        self.ColorSchemeTable.set_active_scheme(*args,**kw)
        # for convenience, set Colors to the active scheme
        self.Colors = self.ColorSchemeTable.active_colors

    def color_toggle(self):
        """Toggle between the currently active color scheme and NoColor."""
        
        if self.ColorSchemeTable.active_scheme_name == 'NoColor':
            self.ColorSchemeTable.set_active_scheme(self.old_scheme)
            self.Colors = self.ColorSchemeTable.active_colors
        else:
            self.old_scheme = self.ColorSchemeTable.active_scheme_name
            self.ColorSchemeTable.set_active_scheme('NoColor')
            self.Colors = self.ColorSchemeTable.active_colors

#---------------------------------------------------------------------------
class ListTB(TBTools):
    """Print traceback information from a traceback list, with optional color.
        
    Calling: requires 3 arguments:
      (etype, evalue, elist)
    as would be obtained by:
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

    def __init__(self,color_scheme = 'NoColor'):
        TBTools.__init__(self,color_scheme = color_scheme,call_pdb=0)
        
    def __call__(self, etype, value, elist):
        print >> Term.cerr, self.text(etype,value,elist)

    def text(self,etype, value, elist,context=5):
        """Return a color formatted string with the traceback info."""

        Colors = self.Colors
        out_string = ['%s%s%s\n' % (Colors.topline,'-'*60,Colors.Normal)]
        if elist:
            out_string.append('Traceback %s(most recent call last)%s:' % \
                                (Colors.normalEm, Colors.Normal) + '\n')
            out_string.extend(self._format_list(elist))
        lines = self._format_exception_only(etype, value)
        for line in lines[:-1]:
            out_string.append(" "+line)
        out_string.append(lines[-1])
        return ''.join(out_string)

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

        Colors = self.Colors
        list = []
        for filename, lineno, name, line in extracted_list[:-1]:
            item = '  File %s"%s"%s, line %s%d%s, in %s%s%s\n' % \
                    (Colors.filename, filename, Colors.Normal, 
                     Colors.lineno, lineno, Colors.Normal,
                     Colors.name, name, Colors.Normal)
            if line:
                item = item + '    %s\n' % line.strip()
            list.append(item)
        # Emphasize the last entry
        filename, lineno, name, line = extracted_list[-1]
        item = '%s  File %s"%s"%s, line %s%d%s, in %s%s%s%s\n' % \
                (Colors.normalEm,
                 Colors.filenameEm, filename, Colors.normalEm,
                 Colors.linenoEm, lineno, Colors.normalEm,
                 Colors.nameEm, name, Colors.normalEm,
                 Colors.Normal)
        if line:
            item = item + '%s    %s%s\n' % (Colors.line, line.strip(),
                                            Colors.Normal)
        list.append(item)
        return list
        
    def _format_exception_only(self, etype, value):
        """Format the exception part of a traceback.

        The arguments are the exception type and value such as given by
        sys.last_type and sys.last_value. The return value is a list of
        strings, each ending in a newline.  Normally, the list contains a
        single string; however, for SyntaxError exceptions, it contains
        several lines that (when printed) display detailed information
        about where the syntax error occurred.  The message indicating
        which exception occurred is the always last string in the list.
        
        Also lifted nearly verbatim from traceback.py
        """
        
        Colors = self.Colors
        list = []
        if type(etype) == types.ClassType:
            stype = Colors.excName + etype.__name__ + Colors.Normal
        else:
            stype = etype  # String exceptions don't get special coloring
        if value is None:
            list.append( str(stype) + '\n')
        else:
            if etype is SyntaxError:
                try:
                    msg, (filename, lineno, offset, line) = value
                except:
                    pass
                else:
                    #print 'filename is',filename  # dbg
                    if not filename: filename = "<string>"
                    list.append('%s  File %s"%s"%s, line %s%d%s\n' % \
                            (Colors.normalEm,
                             Colors.filenameEm, filename, Colors.normalEm,
                             Colors.linenoEm, lineno, Colors.Normal  ))
                    if line is not None:
                        i = 0
                        while i < len(line) and line[i].isspace():
                            i = i+1
                        list.append('%s    %s%s\n' % (Colors.line,
                                                      line.strip(), 
                                                      Colors.Normal))
                        if offset is not None:
                            s = '    '
                            for c in line[i:offset-1]:
                                if c.isspace():
                                    s = s + c
                                else:
                                    s = s + ' '
                            list.append('%s%s^%s\n' % (Colors.caret, s,
                                                       Colors.Normal) )
                        value = msg
            s = self._some_str(value)
            if s:
                list.append('%s%s:%s %s\n' % (str(stype), Colors.excName,
                                              Colors.Normal, s))
            else:
                list.append('%s\n' % str(stype))
        return list

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

    def __init__(self,color_scheme = 'Linux',tb_offset=0,long_header=0,
                 call_pdb = 0, include_vars=1):
        """Specify traceback offset, headers and color scheme.

        Define how many frames to drop from the tracebacks. Calling it with
        tb_offset=1 allows use of this handler in interpreters which will have
        their own code at the top of the traceback (VerboseTB will first
        remove that frame before printing the traceback info)."""
        TBTools.__init__(self,color_scheme=color_scheme,call_pdb=call_pdb)
        self.tb_offset = tb_offset
        self.long_header = long_header
        self.include_vars = include_vars

    def text(self, etype, evalue, etb, context=5):
        """Return a nice text document describing the traceback."""

        # some locals
        Colors        = self.Colors   # just a shorthand + quicker name lookup
        ColorsNormal  = Colors.Normal  # used a lot
        indent_size   = 8  # we need some space to put line numbers before
        indent        = ' '*indent_size
        numbers_width = indent_size - 1 # leave space between numbers & code
        text_repr     = pydoc.text.repr
        exc           = '%s%s%s' % (Colors.excName, str(etype), ColorsNormal)
        em_normal     = '%s\n%s%s' % (Colors.valEm, indent,ColorsNormal)
        undefined     = '%sundefined%s' % (Colors.em, ColorsNormal)

        # some internal-use functions
        def eqrepr(value, repr=text_repr): return '=%s' % repr(value)
        def nullrepr(value, repr=text_repr): return ''

        # meat of the code begins
        if type(etype) is types.ClassType:
            etype = etype.__name__

        if self.long_header:
            # Header with the exception type, python version, and date
            pyver = 'Python ' + string.split(sys.version)[0] + ': ' + sys.executable
            date = time.ctime(time.time())
            
            head = '%s%s%s\n%s%s%s\n%s' % (Colors.topline, '-'*75, ColorsNormal,
                                           exc, ' '*(75-len(str(etype))-len(pyver)),
                                           pyver, string.rjust(date, 75) )
            head += "\nA problem occured executing Python code.  Here is the sequence of function"\
                    "\ncalls leading up to the error, with the most recent (innermost) call last."
        else:
            # Simplified header
            head = '%s%s%s\n%s%s' % (Colors.topline, '-'*75, ColorsNormal,exc,
                                     string.rjust('Traceback (most recent call last)',
                                                  75 - len(str(etype)) ) )
        frames = []
        # Flush cache before calling inspect.  This helps alleviate some of the
        # problems with python 2.3's inspect.py.
        linecache.checkcache()
        # Drop topmost frames if requested
        try:
            records = inspect.getinnerframes(etb, context)[self.tb_offset:]
        except:

            # FIXME: I've been getting many crash reports from python 2.3
            # users, traceable to inspect.py.  If I can find a small test-case
            # to reproduce this, I should either write a better workaround or
            # file a bug report against inspect (if that's the real problem).
            # So far, I haven't been able to find an isolated example to
            # reproduce the problem.
            inspect_error()
            traceback.print_exc(file=Term.cerr)
            info('\nUnfortunately, your original traceback can not be constructed.\n')
            return ''

        # build some color string templates outside these nested loops
        tpl_link       = '%s%%s%s' % (Colors.filenameEm,ColorsNormal)
        tpl_call       = 'in %s%%s%s%%s%s' % (Colors.vName, Colors.valEm,
                                              ColorsNormal)
        tpl_call_fail  = 'in %s%%s%s(***failed resolving arguments***)%s' % \
                         (Colors.vName, Colors.valEm, ColorsNormal)
        tpl_local_var  = '%s%%s%s' % (Colors.vName, ColorsNormal)
        tpl_global_var = '%sglobal%s %s%%s%s' % (Colors.em, ColorsNormal,
                                                 Colors.vName, ColorsNormal)
        tpl_name_val   = '%%s %s= %%s%s' % (Colors.valEm, ColorsNormal)
        tpl_line       = '%s%%s%s %%s' % (Colors.lineno, ColorsNormal)
        tpl_line_em    = '%s%%s%s %%s%s' % (Colors.linenoEm,Colors.line,
                                            ColorsNormal)

        # now, loop over all records printing context and info
        abspath = os.path.abspath
        for frame, file, lnum, func, lines, index in records:
            #print '*** record:',file,lnum,func,lines,index  # dbg
            try:
                file = file and abspath(file) or '?'
            except OSError:
                # if file is '<console>' or something not in the filesystem,
                # the abspath call will throw an OSError.  Just ignore it and
                # keep the original file string.
                pass
            link = tpl_link % file
            try:
                args, varargs, varkw, locals = inspect.getargvalues(frame)
            except:
                # This can happen due to a bug in python2.3.  We should be
                # able to remove this try/except when 2.4 becomes a
                # requirement.  Bug details at http://python.org/sf/1005466
                inspect_error()
                traceback.print_exc(file=Term.cerr)
                info("\nIPython's exception reporting continues...\n")
                
            if func == '?':
                call = ''
            else:
                # Decide whether to include variable details or not
                var_repr = self.include_vars and eqrepr or nullrepr
                try:
                    call = tpl_call % (func,inspect.formatargvalues(args,
                                                varargs, varkw,
                                                locals,formatvalue=var_repr))
                except KeyError:
                    # Very odd crash from inspect.formatargvalues().  The
                    # scenario under which it appeared was a call to
                    # view(array,scale) in NumTut.view.view(), where scale had
                    # been defined as a scalar (it should be a tuple). Somehow
                    # inspect messes up resolving the argument list of view()
                    # and barfs out. At some point I should dig into this one
                    # and file a bug report about it.
                    inspect_error()
                    traceback.print_exc(file=Term.cerr)
                    info("\nIPython's exception reporting continues...\n")
                    call = tpl_call_fail % func

            # Initialize a list of names on the current line, which the
            # tokenizer below will populate.
            names = []

            def tokeneater(token_type, token, start, end, line):
                """Stateful tokeneater which builds dotted names.

                The list of names it appends to (from the enclosing scope) can
                contain repeated composite names.  This is unavoidable, since
                there is no way to disambguate partial dotted structures until
                the full list is known.  The caller is responsible for pruning
                the final list of duplicates before using it."""
                
                # build composite names
                if token == '.':
                    try:
                        names[-1] += '.'
                        # store state so the next token is added for x.y.z names
                        tokeneater.name_cont = True
                        return
                    except IndexError:
                        pass
                if token_type == tokenize.NAME and token not in keyword.kwlist:
                    if tokeneater.name_cont:
                        # Dotted names
                        names[-1] += token
                        tokeneater.name_cont = False
                    else:
                        # Regular new names.  We append everything, the caller
                        # will be responsible for pruning the list later.  It's
                        # very tricky to try to prune as we go, b/c composite
                        # names can fool us.  The pruning at the end is easy
                        # to do (or the caller can print a list with repeated
                        # names if so desired.
                        names.append(token)
                elif token_type == tokenize.NEWLINE:
                    raise IndexError
            # we need to store a bit of state in the tokenizer to build
            # dotted names
            tokeneater.name_cont = False

            def linereader(file=file, lnum=[lnum], getline=linecache.getline):
                line = getline(file, lnum[0])
                lnum[0] += 1
                return line

            # Build the list of names on this line of code where the exception
            # occurred.
            try:
                # This builds the names list in-place by capturing it from the
                # enclosing scope.
                tokenize.tokenize(linereader, tokeneater)
            except IndexError:
                # signals exit of tokenizer
                pass
            except tokenize.TokenError,msg:
                _m = ("An unexpected error occurred while tokenizing input\n"
                      "The following traceback may be corrupted or invalid\n"
                      "The error message is: %s\n" % msg)
                error(_m)
            
            # prune names list of duplicates, but keep the right order
            unique_names = uniq_stable(names)

            # Start loop over vars
            lvals = []
            if self.include_vars:
                for name_full in unique_names:
                    name_base = name_full.split('.',1)[0]
                    if name_base in frame.f_code.co_varnames:
                        if locals.has_key(name_base):
                            try:
                                value = repr(eval(name_full,locals))
                            except:
                                value = undefined
                        else:
                            value = undefined
                        name = tpl_local_var % name_full
                    else:
                        if frame.f_globals.has_key(name_base):
                            try:
                                value = repr(eval(name_full,frame.f_globals))
                            except:
                                value = undefined
                        else:
                            value = undefined
                        name = tpl_global_var % name_full
                    lvals.append(tpl_name_val % (name,value))
            if lvals:
                lvals = '%s%s' % (indent,em_normal.join(lvals))
            else:
                lvals = ''

            level = '%s %s\n' % (link,call)
            excerpt = []
            if index is not None:
                i = lnum - index
                for line in lines:
                    if i == lnum:
                        # This is the line with the error
                        pad = numbers_width - len(str(i))
                        if pad >= 3:
                            marker = '-'*(pad-3) + '-> '
                        elif pad == 2:
                            marker = '> '
                        elif pad == 1:
                            marker = '>'
                        else:
                            marker = ''
                        num = '%s%s' % (marker,i)
                        line = tpl_line_em % (num,line)
                    else:
                        num = '%*s' % (numbers_width,i)
                        line = tpl_line % (num,line)

                    excerpt.append(line)
                    if self.include_vars and i == lnum:
                        excerpt.append('%s\n' % lvals)
                    i += 1
            frames.append('%s%s' % (level,''.join(excerpt)) )

        # Get (safely) a string form of the exception info
        try:
            etype_str,evalue_str = map(str,(etype,evalue))
        except:
            # User exception is improperly defined.
            etype,evalue = str,sys.exc_info()[:2]
            etype_str,evalue_str = map(str,(etype,evalue))
        # ... and format it
        exception = ['%s%s%s: %s' % (Colors.excName, etype_str,
                                     ColorsNormal, evalue_str)]
        if type(evalue) is types.InstanceType:
            names = [w for w in dir(evalue) if isinstance(w, basestring)]
            for name in names:
                value = text_repr(getattr(evalue, name))
                exception.append('\n%s%s = %s' % (indent, name, value))
        # return all our info assembled as a single string
        return '%s\n\n%s\n%s' % (head,'\n'.join(frames),''.join(exception[0]) )

    def debugger(self):
        """Call up the pdb debugger if desired, always clean up the tb reference.

        If the call_pdb flag is set, the pdb interactive debugger is
        invoked. In all cases, the self.tb reference to the current traceback
        is deleted to prevent lingering references which hamper memory
        management.

        Note that each call to pdb() does an 'import readline', so if your app
        requires a special setup for the readline completers, you'll have to
        fix that by hand after invoking the exception handler."""

        if self.call_pdb:
            if self.pdb is None:
                self.pdb = Debugger.Pdb()
            # the system displayhook may have changed, restore the original for pdb
            dhook = sys.displayhook
            sys.displayhook = sys.__displayhook__
            self.pdb.reset()
            while self.tb.tb_next is not None:
                self.tb = self.tb.tb_next
            try:
                self.pdb.interaction(self.tb.tb_frame, self.tb)
            except:
                print '*** ERROR ***'
                print 'This version of pdb has a bug and crashed.'
                print 'Returning to IPython...'
            sys.displayhook = dhook
        del self.tb

    def handler(self, info=None):
        (etype, evalue, etb) = info or sys.exc_info()
        self.tb = etb
        print >> Term.cerr, self.text(etype, evalue, etb)

    # Changed so an instance can just be called as VerboseTB_inst() and print
    # out the right info on its own.
    def __call__(self, etype=None, evalue=None, etb=None):
        """This hook can replace sys.excepthook (for Python 2.1 or higher)."""
        if etb is not None:
            self.handler((etype, evalue, etb))
        else:
            self.handler()
        self.debugger()

#----------------------------------------------------------------------------
class FormattedTB(VerboseTB,ListTB):
    """Subclass ListTB but allow calling with a traceback.

    It can thus be used as a sys.excepthook for Python > 2.1.

    Also adds 'Context' and 'Verbose' modes, not available in ListTB.

    Allows a tb_offset to be specified. This is useful for situations where
    one needs to remove a number of topmost frames from the traceback (such as
    occurs with python programs that themselves execute other python code,
    like Python shells).  """
    
    def __init__(self, mode = 'Plain', color_scheme='Linux',
                 tb_offset = 0,long_header=0,call_pdb=0,include_vars=0):

        # NEVER change the order of this list. Put new modes at the end:
        self.valid_modes = ['Plain','Context','Verbose']
        self.verbose_modes = self.valid_modes[1:3]

        VerboseTB.__init__(self,color_scheme,tb_offset,long_header,
                           call_pdb=call_pdb,include_vars=include_vars)
        self.set_mode(mode)
        
    def _extract_tb(self,tb):
        if tb:
            return traceback.extract_tb(tb)
        else:
            return None

    def text(self, etype, value, tb,context=5,mode=None):
        """Return formatted traceback.

        If the optional mode parameter is given, it overrides the current
        mode."""

        if mode is None:
            mode = self.mode
        if mode in self.verbose_modes:
            # verbose modes need a full traceback
            return VerboseTB.text(self,etype, value, tb,context=5)
        else:
            # We must check the source cache because otherwise we can print
            # out-of-date source code.
            linecache.checkcache()
            # Now we can extract and format the exception
            elist = self._extract_tb(tb)
            if len(elist) > self.tb_offset:
                del elist[:self.tb_offset]
            return ListTB.text(self,etype,value,elist)

    def set_mode(self,mode=None):
        """Switch to the desired mode.

        If mode is not specified, cycles through the available modes."""

        if not mode:
            new_idx = ( self.valid_modes.index(self.mode) + 1 ) % \
                      len(self.valid_modes)
            self.mode = self.valid_modes[new_idx]
        elif mode not in self.valid_modes:
            raise ValueError, 'Unrecognized mode in FormattedTB: <'+mode+'>\n'\
                  'Valid modes: '+str(self.valid_modes)
        else:
            self.mode = mode
        # include variable details only in 'Verbose' mode
        self.include_vars = (self.mode == self.valid_modes[2])

    # some convenient shorcuts
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

    A brief example:
    
    AutoTB = AutoFormattedTB(mode = 'Verbose',color_scheme='Linux')
    try:
      ...
    except:
      AutoTB()  # or AutoTB(out=logfile) where logfile is an open file object
    """
    def __call__(self,etype=None,evalue=None,etb=None,
                 out=None,tb_offset=None):
        """Print out a formatted exception traceback.

        Optional arguments:
          - out: an open file-like object to direct output to.

          - tb_offset: the number of frames to skip over in the stack, on a
          per-call basis (this overrides temporarily the instance's tb_offset
          given at initialization time.  """
        
        if out is None:
            out = Term.cerr
        if tb_offset is not None:
            tb_offset, self.tb_offset = self.tb_offset, tb_offset
            print >> out, self.text(etype, evalue, etb)
            self.tb_offset = tb_offset
        else:
            print >> out, self.text()
        self.debugger()

    def text(self,etype=None,value=None,tb=None,context=5,mode=None):
        if etype is None:
            etype,value,tb = sys.exc_info()
        self.tb = tb
        return FormattedTB.text(self,etype,value,tb,context=5,mode=mode)

#---------------------------------------------------------------------------
# A simple class to preserve Nathan's original functionality.
class ColorTB(FormattedTB):
    """Shorthand to initialize a FormattedTB in Linux colors mode."""
    def __init__(self,color_scheme='Linux',call_pdb=0):
        FormattedTB.__init__(self,color_scheme=color_scheme,
                             call_pdb=call_pdb)

#----------------------------------------------------------------------------
# module testing (minimal)
if __name__ == "__main__":
    def spam(c, (d, e)):
        x = c + d
        y = c * d
        foo(x, y)

    def foo(a, b, bar=1):
        eggs(a, b + bar)

    def eggs(f, g, z=globals()):
        h = f + g
        i = f - g
        return h / i

    print ''
    print '*** Before ***'
    try:
        print spam(1, (2, 3))
    except:
        traceback.print_exc()
    print ''
    
    handler = ColorTB()
    print '*** ColorTB ***'
    try:
        print spam(1, (2, 3))
    except:
        apply(handler, sys.exc_info() )
    print ''
    
    handler = VerboseTB()
    print '*** VerboseTB ***'
    try:
        print spam(1, (2, 3))
    except:
        apply(handler, sys.exc_info() )
    print ''
    

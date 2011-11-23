"""Analysis of text input into executable blocks.

The main class in this module, :class:`InputSplitter`, is designed to break
input from either interactive, line-by-line environments or block-based ones,
into standalone blocks that can be executed by Python as 'single' statements
(thus triggering sys.displayhook).

A companion, :class:`IPythonInputSplitter`, provides the same functionality but
with full support for the extended IPython syntax (magics, system calls, etc).

For more details, see the class docstring below.

Syntax Transformations
----------------------

One of the main jobs of the code in this file is to apply all syntax
transformations that make up 'the IPython language', i.e. magics, shell
escapes, etc.  All transformations should be implemented as *fully stateless*
entities, that simply take one line as their input and return a line.
Internally for implementation purposes they may be a normal function or a
callable object, but the only input they receive will be a single line and they
should only return a line, without holding any data-dependent state between
calls.

As an example, the EscapedTransformer is a class so we can more clearly group
together the functionality of dispatching to individual functions based on the
starting escape character, but the only method for public use is its call
method.


ToDo
----

- Should we make push() actually raise an exception once push_accepts_more()
  returns False?

- Naming cleanups.  The tr_* names aren't the most elegant, though now they are
  at least just attributes of a class so not really very exposed.

- Think about the best way to support dynamic things: automagic, autocall,
  macros, etc.

- Think of a better heuristic for the application of the transforms in
  IPythonInputSplitter.push() than looking at the buffer ending in ':'.  Idea:
  track indentation change events (indent, dedent, nothing) and apply them only
  if the indentation went up, but not otherwise.

- Think of the cleanest way for supporting user-specified transformations (the
  user prefilters we had before).

Authors
-------

* Fernando Perez
* Brian Granger
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------
from __future__ import print_function

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import ast
import codeop
import re
import sys
import tokenize
from StringIO import StringIO

# IPython modules
from IPython.core.splitinput import split_user_input, LineInfo
from IPython.utils.py3compat import cast_unicode

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# The escape sequences that define the syntax transformations IPython will
# apply to user input.  These can NOT be just changed here: many regular
# expressions and other parts of the code may use their hardcoded values, and
# for all intents and purposes they constitute the 'IPython syntax', so they
# should be considered fixed.

ESC_SHELL  = '!'     # Send line to underlying system shell
ESC_SH_CAP = '!!'    # Send line to system shell and capture output
ESC_HELP   = '?'     # Find information about object
ESC_HELP2  = '??'    # Find extra-detailed information about object
ESC_MAGIC  = '%'     # Call magic function
ESC_QUOTE  = ','     # Split args on whitespace, quote each as string and call
ESC_QUOTE2 = ';'     # Quote all args as a single string, call
ESC_PAREN  = '/'     # Call first argument with rest of line as arguments

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

# FIXME: These are general-purpose utilities that later can be moved to the
# general ward.  Kept here for now because we're being very strict about test
# coverage with this code, and this lets us ensure that we keep 100% coverage
# while developing.

# compiled regexps for autoindent management
dedent_re = re.compile('|'.join([
    r'^\s+raise(\s.*)?$', # raise statement (+ space + other stuff, maybe)
    r'^\s+raise\([^\)]*\).*$', # wacky raise with immediate open paren
    r'^\s+return(\s.*)?$', # normal return (+ space + other stuff, maybe)
    r'^\s+return\([^\)]*\).*$', # wacky return with immediate open paren
    r'^\s+pass\s*$' # pass (optionally followed by trailing spaces)
]))
ini_spaces_re = re.compile(r'^([ \t\r\f\v]+)')

# regexp to match pure comment lines so we don't accidentally insert 'if 1:'
# before pure comments
comment_line_re = re.compile('^\s*\#')


def num_ini_spaces(s):
    """Return the number of initial spaces in a string.

    Note that tabs are counted as a single space.  For now, we do *not* support
    mixing of tabs and spaces in the user's input.

    Parameters
    ----------
    s : string

    Returns
    -------
    n : int
    """

    ini_spaces = ini_spaces_re.match(s)
    if ini_spaces:
        return ini_spaces.end()
    else:
        return 0


def remove_comments(src):
    """Remove all comments from input source.

    Note: comments are NOT recognized inside of strings!

    Parameters
    ----------
    src : string
      A single or multiline input string.

    Returns
    -------
    String with all Python comments removed.
    """

    return re.sub('#.*', '', src)
    
def has_comment(src):
    """Indicate whether an input line has (i.e. ends in, or is) a comment.
    
    This uses tokenize, so it can distinguish comments from # inside strings.
    
    Parameters
    ----------
    src : string
      A single line input string.
    
    Returns
    -------
    Boolean: True if source has a comment.
    """
    readline = StringIO(src).readline
    toktypes = set()
    try:
        for t in tokenize.generate_tokens(readline):
            toktypes.add(t[0])
    except tokenize.TokenError:
        pass
    return(tokenize.COMMENT in toktypes)


def get_input_encoding():
    """Return the default standard input encoding.

    If sys.stdin has no encoding, 'ascii' is returned."""
    # There are strange environments for which sys.stdin.encoding is None. We
    # ensure that a valid encoding is returned.
    encoding = getattr(sys.stdin, 'encoding', None)
    if encoding is None:
        encoding = 'ascii'
    return encoding

#-----------------------------------------------------------------------------
# Classes and functions for normal Python syntax handling
#-----------------------------------------------------------------------------

class InputSplitter(object):
    """An object that can accumulate lines of Python source before execution.

    This object is designed to be fed python source line-by-line, using
       :meth:`push`. It will return on each push whether the currently pushed
       code could be executed already. In addition, it provides a method called
       :meth:`push_accepts_more` that can be used to query whether more input
       can be pushed into a single interactive block.

    This is a simple example of how an interactive terminal-based client can use
    this tool::

        isp = InputSplitter()
        while isp.push_accepts_more():
            indent = ' '*isp.indent_spaces
            prompt = '>>> ' + indent
            line = indent + raw_input(prompt)
            isp.push(line)
        print 'Input source was:\n', isp.source_reset(),
    """
    # Number of spaces of indentation computed from input that has been pushed
    # so far.  This is the attributes callers should query to get the current
    # indentation level, in order to provide auto-indent facilities.
    indent_spaces = 0
    # String, indicating the default input encoding.  It is computed by default
    # at initialization time via get_input_encoding(), but it can be reset by a
    # client with specific knowledge of the encoding.
    encoding = ''
    # String where the current full source input is stored, properly encoded.
    # Reading this attribute is the normal way of querying the currently pushed
    # source code, that has been properly encoded.
    source = ''
    # Code object corresponding to the current source.  It is automatically
    # synced to the source, so it can be queried at any time to obtain the code
    # object; it will be None if the source doesn't compile to valid Python.
    code = None
    # Input mode
    input_mode = 'line'
    
    # Private attributes
    
    # List with lines of input accumulated so far
    _buffer = None
    # Command compiler
    _compile = None
    # Mark when input has changed indentation all the way back to flush-left
    _full_dedent = False
    # Boolean indicating whether the current block is complete
    _is_complete = None
    
    def __init__(self, input_mode=None):
        """Create a new InputSplitter instance.

        Parameters
        ----------
        input_mode : str

          One of ['line', 'cell']; default is 'line'.

       The input_mode parameter controls how new inputs are used when fed via
       the :meth:`push` method:

       - 'line': meant for line-oriented clients, inputs are appended one at a
         time to the internal buffer and the whole buffer is compiled.

       - 'cell': meant for clients that can edit multi-line 'cells' of text at
          a time.  A cell can contain one or more blocks that can be compile in
          'single' mode by Python.  In this mode, each new input new input
          completely replaces all prior inputs.  Cell mode is thus equivalent
          to prepending a full reset() to every push() call.
        """
        self._buffer = []
        self._compile = codeop.CommandCompiler()
        self.encoding = get_input_encoding()
        self.input_mode = InputSplitter.input_mode if input_mode is None \
                          else input_mode

    def reset(self):
        """Reset the input buffer and associated state."""
        self.indent_spaces = 0
        self._buffer[:] = []
        self.source = ''
        self.code = None
        self._is_complete = False
        self._full_dedent = False

    def source_reset(self):
        """Return the input source and perform a full reset.
        """
        out = self.source
        self.reset()
        return out

    def push(self, lines):
        """Push one or more lines of input.

        This stores the given lines and returns a status code indicating
        whether the code forms a complete Python block or not.

        Any exceptions generated in compilation are swallowed, but if an
        exception was produced, the method returns True.

        Parameters
        ----------
        lines : string
          One or more lines of Python input.
        
        Returns
        -------
        is_complete : boolean
          True if the current input source (the result of the current input
        plus prior inputs) forms a complete Python execution block.  Note that
        this value is also stored as a private attribute (_is_complete), so it
        can be queried at any time.
        """
        if self.input_mode == 'cell':
            self.reset()
        
        self._store(lines)
        source = self.source

        # Before calling _compile(), reset the code object to None so that if an
        # exception is raised in compilation, we don't mislead by having
        # inconsistent code/source attributes.
        self.code, self._is_complete = None, None

        # Honor termination lines properly
        if source.rstrip().endswith('\\'):
            return False

        self._update_indent(lines)
        try:
            self.code = self._compile(source, symbol="exec")
        # Invalid syntax can produce any of a number of different errors from
        # inside the compiler, so we have to catch them all.  Syntax errors
        # immediately produce a 'ready' block, so the invalid Python can be
        # sent to the kernel for evaluation with possible ipython
        # special-syntax conversion.
        except (SyntaxError, OverflowError, ValueError, TypeError,
                MemoryError):
            self._is_complete = True
        else:
            # Compilation didn't produce any exceptions (though it may not have
            # given a complete code object)
            self._is_complete = self.code is not None

        return self._is_complete

    def push_accepts_more(self):
        """Return whether a block of interactive input can accept more input.

        This method is meant to be used by line-oriented frontends, who need to
        guess whether a block is complete or not based solely on prior and
        current input lines.  The InputSplitter considers it has a complete
        interactive block and will not accept more input only when either a
        SyntaxError is raised, or *all* of the following are true:

        1. The input compiles to a complete statement.
        
        2. The indentation level is flush-left (because if we are indented,
           like inside a function definition or for loop, we need to keep
           reading new input).
          
        3. There is one extra line consisting only of whitespace.

        Because of condition #3, this method should be used only by
        *line-oriented* frontends, since it means that intermediate blank lines
        are not allowed in function definitions (or any other indented block).

        If the current input produces a syntax error, this method immediately
        returns False but does *not* raise the syntax error exception, as
        typically clients will want to send invalid syntax to an execution
        backend which might convert the invalid syntax into valid Python via
        one of the dynamic IPython mechanisms.
        """

        # With incomplete input, unconditionally accept more
        if not self._is_complete:
            return True

        # If we already have complete input and we're flush left, the answer
        # depends.  In line mode, if there hasn't been any indentation,
        # that's it. If we've come back from some indentation, we need
        # the blank final line to finish.
        # In cell mode, we need to check how many blocks the input so far
        # compiles into, because if there's already more than one full
        # independent block of input, then the client has entered full
        # 'cell' mode and is feeding lines that each is complete.  In this
        # case we should then keep accepting. The Qt terminal-like console
        # does precisely this, to provide the convenience of terminal-like
        # input of single expressions, but allowing the user (with a
        # separate keystroke) to switch to 'cell' mode and type multiple
        # expressions in one shot.
        if self.indent_spaces==0:
            if self.input_mode=='line':
                if not self._full_dedent:
                    return False
            else:
                try:
                    code_ast = ast.parse(u''.join(self._buffer))
                except Exception:
                    return False
                else:
                    if len(code_ast.body) == 1:
                        return False

        # When input is complete, then termination is marked by an extra blank
        # line at the end.
        last_line = self.source.splitlines()[-1]
        return bool(last_line and not last_line.isspace())

    #------------------------------------------------------------------------
    # Private interface
    #------------------------------------------------------------------------

    def _find_indent(self, line):
        """Compute the new indentation level for a single line.

        Parameters
        ----------
        line : str
          A single new line of non-whitespace, non-comment Python input.
          
        Returns
        -------
        indent_spaces : int
          New value for the indent level (it may be equal to self.indent_spaces
        if indentation doesn't change.

        full_dedent : boolean
          Whether the new line causes a full flush-left dedent.
        """
        indent_spaces = self.indent_spaces
        full_dedent = self._full_dedent
        
        inisp = num_ini_spaces(line)
        if inisp < indent_spaces:
            indent_spaces = inisp
            if indent_spaces <= 0:
                #print 'Full dedent in text',self.source # dbg
                full_dedent = True

        if line.rstrip()[-1] == ':':
            indent_spaces += 4
        elif dedent_re.match(line):
            indent_spaces -= 4
            if indent_spaces <= 0:
                full_dedent = True

        # Safety
        if indent_spaces < 0:
            indent_spaces = 0
            #print 'safety' # dbg
            
        return indent_spaces, full_dedent
    
    def _update_indent(self, lines):
        for line in remove_comments(lines).splitlines():
            if line and not line.isspace():
                self.indent_spaces, self._full_dedent = self._find_indent(line)

    def _store(self, lines, buffer=None, store='source'):
        """Store one or more lines of input.

        If input lines are not newline-terminated, a newline is automatically
        appended."""
        
        if buffer is None:
            buffer = self._buffer
            
        if lines.endswith('\n'):
            buffer.append(lines)
        else:
            buffer.append(lines+'\n')
        setattr(self, store, self._set_source(buffer))

    def _set_source(self, buffer):
        return u''.join(buffer)


#-----------------------------------------------------------------------------
# Functions and classes for IPython-specific syntactic support
#-----------------------------------------------------------------------------

# The escaped translators ALL receive a line where their own escape has been
# stripped.  Only '?' is valid at the end of the line, all others can only be
# placed at the start.

# Transformations of the special syntaxes that don't rely on an explicit escape
# character but instead on patterns on the input line

# The core transformations are implemented as standalone functions that can be
# tested and validated in isolation.  Each of these uses a regexp, we
# pre-compile these and keep them close to each function definition for clarity

_assign_system_re = re.compile(r'(?P<lhs>(\s*)([\w\.]+)((\s*,\s*[\w\.]+)*))'
                               r'\s*=\s*!\s*(?P<cmd>.*)')

def transform_assign_system(line):
    """Handle the `files = !ls` syntax."""
    m = _assign_system_re.match(line)
    if m is not None:
        cmd = m.group('cmd')
        lhs = m.group('lhs')
        new_line = '%s = get_ipython().getoutput(%r)' % (lhs, cmd)
        return new_line
    return line


_assign_magic_re = re.compile(r'(?P<lhs>(\s*)([\w\.]+)((\s*,\s*[\w\.]+)*))'
                               r'\s*=\s*%\s*(?P<cmd>.*)')

def transform_assign_magic(line):
    """Handle the `a = %who` syntax."""
    m = _assign_magic_re.match(line)
    if m is not None:
        cmd = m.group('cmd')
        lhs = m.group('lhs')
        new_line = '%s = get_ipython().magic(%r)' % (lhs, cmd)
        return new_line
    return line


_classic_prompt_re = re.compile(r'^([ \t]*>>> |^[ \t]*\.\.\. )')

def transform_classic_prompt(line):
    """Handle inputs that start with '>>> ' syntax."""

    if not line or line.isspace():
        return line
    m = _classic_prompt_re.match(line)
    if m:
        return line[len(m.group(0)):]
    else:
        return line


_ipy_prompt_re = re.compile(r'^([ \t]*In \[\d+\]: |^[ \t]*\ \ \ \.\.\.+: )')

def transform_ipy_prompt(line):
    """Handle inputs that start classic IPython prompt syntax."""

    if not line or line.isspace():
        return line
    #print 'LINE:  %r' % line # dbg
    m = _ipy_prompt_re.match(line)
    if m:
        #print 'MATCH! %r -> %r' % (line, line[len(m.group(0)):]) # dbg
        return line[len(m.group(0)):]
    else:
        return line


def _make_help_call(target, esc, lspace, next_input=None):
    """Prepares a pinfo(2)/psearch call from a target name and the escape
    (i.e. ? or ??)"""
    method  = 'pinfo2' if esc == '??' \
                else 'psearch' if '*' in target \
                else 'pinfo'
    arg = " ".join([method, target])
    
    if next_input:
        tpl = '%sget_ipython().magic(%r, next_input=%r)'
        return tpl % (lspace, arg, next_input)
    else:
        return '%sget_ipython().magic(%r)' % (lspace, arg)

_initial_space_re = re.compile(r'\s*')
_help_end_re = re.compile(r"""(%?
                              [a-zA-Z_*][\w*]*        # Variable name
                              (\.[a-zA-Z_*][\w*]*)*   # .etc.etc
                              )
                              (\?\??)$                # ? or ??""",
                              re.VERBOSE)
def transform_help_end(line):
    """Translate lines with ?/?? at the end"""
    m = _help_end_re.search(line)
    if m is None or has_comment(line):
        return line
    target = m.group(1)
    esc = m.group(3)
    lspace = _initial_space_re.match(line).group(0)
    
    # If we're mid-command, put it back on the next prompt for the user.
    next_input = line.rstrip('?') if line.strip() != m.group(0) else None
        
    return _make_help_call(target, esc, lspace, next_input)


class EscapedTransformer(object):
    """Class to transform lines that are explicitly escaped out."""

    def __init__(self):
        tr = { ESC_SHELL  : self._tr_system,
               ESC_SH_CAP : self._tr_system2,
               ESC_HELP   : self._tr_help,
               ESC_HELP2  : self._tr_help,
               ESC_MAGIC  : self._tr_magic,
               ESC_QUOTE  : self._tr_quote,
               ESC_QUOTE2 : self._tr_quote2,
               ESC_PAREN  : self._tr_paren }
        self.tr = tr
        
    # Support for syntax transformations that use explicit escapes typed by the
    # user at the beginning of a line
    @staticmethod
    def _tr_system(line_info):
        "Translate lines escaped with: !"
        cmd = line_info.line.lstrip().lstrip(ESC_SHELL)
        return '%sget_ipython().system(%r)' % (line_info.pre, cmd)

    @staticmethod
    def _tr_system2(line_info):
        "Translate lines escaped with: !!"
        cmd = line_info.line.lstrip()[2:]
        return '%sget_ipython().getoutput(%r)' % (line_info.pre, cmd)

    @staticmethod
    def _tr_help(line_info):
        "Translate lines escaped with: ?/??"
        # A naked help line should just fire the intro help screen
        if not line_info.line[1:]:
            return 'get_ipython().show_usage()'
        
        return _make_help_call(line_info.ifun, line_info.esc, line_info.pre)

    @staticmethod
    def _tr_magic(line_info):
        "Translate lines escaped with: %"
        tpl = '%sget_ipython().magic(%r)'
        cmd = ' '.join([line_info.ifun, line_info.the_rest]).strip()
        return tpl % (line_info.pre, cmd)

    @staticmethod
    def _tr_quote(line_info):
        "Translate lines escaped with: ,"
        return '%s%s("%s")' % (line_info.pre, line_info.ifun,
                             '", "'.join(line_info.the_rest.split()) )

    @staticmethod
    def _tr_quote2(line_info):
        "Translate lines escaped with: ;"
        return '%s%s("%s")' % (line_info.pre, line_info.ifun,
                               line_info.the_rest)

    @staticmethod
    def _tr_paren(line_info):
        "Translate lines escaped with: /"
        return '%s%s(%s)' % (line_info.pre, line_info.ifun,
                             ", ".join(line_info.the_rest.split()))

    def __call__(self, line):
        """Class to transform lines that are explicitly escaped out.

        This calls the above _tr_* static methods for the actual line
        translations."""

        # Empty lines just get returned unmodified
        if not line or line.isspace():
            return line

        # Get line endpoints, where the escapes can be
        line_info = LineInfo(line)

        if not line_info.esc in self.tr:
            # If we don't recognize the escape, don't modify the line
            return line

        return self.tr[line_info.esc](line_info)


# A function-looking object to be used by the rest of the code.  The purpose of
# the class in this case is to organize related functionality, more than to
# manage state.
transform_escaped = EscapedTransformer()


class IPythonInputSplitter(InputSplitter):
    """An input splitter that recognizes all of IPython's special syntax."""

    # String with raw, untransformed input.
    source_raw = ''

    # Private attributes
    
    # List with lines of raw input accumulated so far.
    _buffer_raw = None

    def __init__(self, input_mode=None):
        InputSplitter.__init__(self, input_mode)
        self._buffer_raw = []
        
    def reset(self):
        """Reset the input buffer and associated state."""
        InputSplitter.reset(self)
        self._buffer_raw[:] = []
        self.source_raw = ''

    def source_raw_reset(self):
        """Return input and raw source and perform a full reset.
        """
        out = self.source
        out_r = self.source_raw
        self.reset()
        return out, out_r

    def push(self, lines):
        """Push one or more lines of IPython input.
        """
        if not lines:
            return super(IPythonInputSplitter, self).push(lines)

        # We must ensure all input is pure unicode
        lines = cast_unicode(lines, self.encoding)

        lines_list = lines.splitlines()

        transforms = [transform_ipy_prompt, transform_classic_prompt,
                      transform_help_end, transform_escaped,
                      transform_assign_system, transform_assign_magic]

        # Transform logic
        #
        # We only apply the line transformers to the input if we have either no
        # input yet, or complete input, or if the last line of the buffer ends
        # with ':' (opening an indented block).  This prevents the accidental
        # transformation of escapes inside multiline expressions like
        # triple-quoted strings or parenthesized expressions.
        #
        # The last heuristic, while ugly, ensures that the first line of an
        # indented block is correctly transformed.
        #
        # FIXME: try to find a cleaner approach for this last bit.

        # If we were in 'block' mode, since we're going to pump the parent
        # class by hand line by line, we need to temporarily switch out to
        # 'line' mode, do a single manual reset and then feed the lines one
        # by one.  Note that this only matters if the input has more than one
        # line.
        changed_input_mode = False

        if self.input_mode == 'cell':
            self.reset()
            changed_input_mode = True
            saved_input_mode = 'cell'
            self.input_mode = 'line'

        # Store raw source before applying any transformations to it.  Note
        # that this must be done *after* the reset() call that would otherwise
        # flush the buffer.
        self._store(lines, self._buffer_raw, 'source_raw')
        
        try:
            push = super(IPythonInputSplitter, self).push
            buf = self._buffer
            for line in lines_list:
                if self._is_complete or not buf or \
                       (buf and (buf[-1].rstrip().endswith(':') or
                                 buf[-1].rstrip().endswith(',')) ):
                    for f in transforms:
                        line = f(line)

                out = push(line)
        finally:
            if changed_input_mode:
                self.input_mode = saved_input_mode
        return out

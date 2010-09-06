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
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import codeop
import re
import sys

# IPython modules
from IPython.utils.text import make_quoted_expr
#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# The escape sequences that define the syntax transformations IPython will
# apply to user input.  These can NOT be just changed here: many regular
# expressions and other parts of the code may use their hardcoded values, and
# for all intents and purposes they constitute the 'IPython syntax', so they
# should be considered fixed.

ESC_SHELL  = '!'
ESC_SH_CAP = '!!'
ESC_HELP   = '?'
ESC_HELP2  = '??'
ESC_MAGIC  = '%'
ESC_QUOTE  = ','
ESC_QUOTE2 = ';'
ESC_PAREN  = '/'

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

# FIXME: These are general-purpose utilities that later can be moved to the
# general ward.  Kept here for now because we're being very strict about test
# coverage with this code, and this lets us ensure that we keep 100% coverage
# while developing.

# compiled regexps for autoindent management
dedent_re = re.compile(r'^\s+raise|^\s+return|^\s+pass')
ini_spaces_re = re.compile(r'^([ \t\r\f\v]+)')


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
    """An object that can split Python source input in executable blocks.

    This object is designed to be used in one of two basic modes:

    1. By feeding it python source line-by-line, using :meth:`push`.  In this
       mode, it will return on each push whether the currently pushed code
       could be executed already.  In addition, it provides a method called
       :meth:`push_accepts_more` that can be used to query whether more input
       can be pushed into a single interactive block.

    2. By calling :meth:`split_blocks` with a single, multiline Python string,
       that is then split into blocks each of which can be executed
       interactively as a single statement.

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

          One of ['line', 'block']; default is 'line'.

       The input_mode parameter controls how new inputs are used when fed via
       the :meth:`push` method:

       - 'line': meant for line-oriented clients, inputs are appended one at a
         time to the internal buffer and the whole buffer is compiled.

       - 'block': meant for clients that can edit multi-line blocks of text at
          a time.  Each new input new input completely replaces all prior
          inputs.  Block mode is thus equivalent to prepending a full reset()
          to every push() call.
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
        """Push one ore more lines of input.

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
        if self.input_mode == 'block':
            self.reset()
        
        # If the source code has leading blanks, add 'if 1:\n' to it
        # this allows execution of indented pasted code. It is tempting
        # to add '\n' at the end of source to run commands like ' a=1'
        # directly, but this fails for more complicated scenarios
        if not self._buffer and lines[:1] in [' ', '\t']:
            lines = 'if 1:\n%s' % lines
        
        self._store(lines)
        source = self.source

        # Before calling _compile(), reset the code object to None so that if an
        # exception is raised in compilation, we don't mislead by having
        # inconsistent code/source attributes.
        self.code, self._is_complete = None, None

        self._update_indent(lines)
        try:
            self.code = self._compile(source)
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

        Block-oriented frontends that have a separate keyboard event to
        indicate execution should use the :meth:`split_blocks` method instead.

        If the current input produces a syntax error, this method immediately
        returns False but does *not* raise the syntax error exception, as
        typically clients will want to send invalid syntax to an execution
        backend which might convert the invalid syntax into valid Python via
        one of the dynamic IPython mechanisms.
        """
            
        if not self._is_complete:
            return True

        if self.indent_spaces==0:
            return False
        
        last_line = self.source.splitlines()[-1]
        return bool(last_line and not last_line.isspace())
        
    def split_blocks(self, lines):
        """Split a multiline string into multiple input blocks.

        Note: this method starts by performing a full reset().
        
        Parameters
        ----------
        lines : str
          A possibly multiline string.

        Returns
        -------
        blocks : list
          A list of strings, each possibly multiline.  Each string corresponds
          to a single block that can be compiled in 'single' mode (unless it
          has a syntax error)."""

        # This code is fairly delicate.  If you make any changes here, make
        # absolutely sure that you do run the full test suite and ALL tests
        # pass.

        self.reset()
        blocks = []
        
        # Reversed copy so we can use pop() efficiently and consume the input
        # as a stack
        lines = lines.splitlines()[::-1]
        # Outer loop over all input
        while lines:
            #print 'Current lines:', lines  # dbg
            # Inner loop to build each block
            while True:
                # Safety exit from inner loop
                if not lines:
                    break
                # Grab next line but don't push it yet
                next_line = lines.pop()
                # Blank/empty lines are pushed as-is
                if not next_line or next_line.isspace():
                    self.push(next_line)
                    continue

                # Check indentation changes caused by the *next* line
                indent_spaces, _full_dedent = self._find_indent(next_line)

                # If the next line causes a dedent, it can be for two differnt
                # reasons: either an explicit de-dent by the user or a
                # return/raise/pass statement.  These MUST be handled
                # separately:
                #
                # 1. the first case is only detected when the actual explicit
                # dedent happens, and that would be the *first* line of a *new*
                # block.  Thus, we must put the line back into the input buffer
                # so that it starts a new block on the next pass.
                #
                # 2. the second case is detected in the line before the actual
                # dedent happens, so , we consume the line and we can break out
                # to start a new block.

                # Case 1, explicit dedent causes a break.
                # Note: check that we weren't on the very last line, else we'll
                # enter an infinite loop adding/removing the last line.
                if  _full_dedent and lines and not next_line.startswith(' '):
                    lines.append(next_line)
                    break
                
                # Otherwise any line is pushed
                self.push(next_line)

                # Case 2, full dedent with full block ready:
                if _full_dedent or \
                       self.indent_spaces==0 and not self.push_accepts_more():
                    break
            # Form the new block with the current source input
            blocks.append(self.source_reset())
            
        return blocks

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

        if line[-1] == ':':
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

    def _store(self, lines):
        """Store one or more lines of input.

        If input lines are not newline-terminated, a newline is automatically
        appended."""

        if lines.endswith('\n'):
            self._buffer.append(lines)
        else:
            self._buffer.append(lines+'\n')
        self._set_source()

    def _set_source(self):
        self.source = ''.join(self._buffer).encode(self.encoding)


#-----------------------------------------------------------------------------
# Functions and classes for IPython-specific syntactic support
#-----------------------------------------------------------------------------

# RegExp for splitting line contents into pre-char//first word-method//rest.
# For clarity, each group in on one line.

line_split = re.compile("""
             ^(\s*)              # any leading space
             ([,;/%]|!!?|\?\??)  # escape character or characters
             \s*(%?[\w\.]*)      # function/method, possibly with leading %
                                 # to correctly treat things like '?%magic'
             (\s+.*$|$)          # rest of line
             """, re.VERBOSE)


def split_user_input(line):
    """Split user input into early whitespace, esc-char, function part and rest.

    This is currently handles lines with '=' in them in a very inconsistent
    manner.

    Examples
    ========
    >>> split_user_input('x=1')
    ('', '', 'x=1', '')
    >>> split_user_input('?')
    ('', '?', '', '')
    >>> split_user_input('??')
    ('', '??', '', '')
    >>> split_user_input(' ?')
    (' ', '?', '', '')
    >>> split_user_input(' ??')
    (' ', '??', '', '')
    >>> split_user_input('??x')
    ('', '??', 'x', '')
    >>> split_user_input('?x=1')
    ('', '', '?x=1', '')
    >>> split_user_input('!ls')
    ('', '!', 'ls', '')
    >>> split_user_input('  !ls')
    ('  ', '!', 'ls', '')
    >>> split_user_input('!!ls')
    ('', '!!', 'ls', '')
    >>> split_user_input('  !!ls')
    ('  ', '!!', 'ls', '')
    >>> split_user_input(',ls')
    ('', ',', 'ls', '')
    >>> split_user_input(';ls')
    ('', ';', 'ls', '')
    >>> split_user_input('  ;ls')
    ('  ', ';', 'ls', '')
    >>> split_user_input('f.g(x)')
    ('', '', 'f.g(x)', '')
    >>> split_user_input('f.g (x)')
    ('', '', 'f.g', '(x)')
    >>> split_user_input('?%hist')
    ('', '?', '%hist', '')
    """
    match = line_split.match(line)
    if match:
        lspace, esc, fpart, rest = match.groups()
    else:
        # print "match failed for line '%s'" % line
        try:
            fpart, rest = line.split(None, 1)
        except ValueError:
            # print "split failed for line '%s'" % line
            fpart, rest = line,''
        lspace = re.match('^(\s*)(.*)', line).groups()[0]
        esc = ''

    # fpart has to be a valid python identifier, so it better be only pure
    # ascii, no unicode:
    try:
        fpart = fpart.encode('ascii')
    except UnicodeEncodeError:
        lspace = unicode(lspace)
        rest = fpart + u' ' + rest
        fpart = u''

    #print 'line:<%s>' % line # dbg
    #print 'esc <%s> fpart <%s> rest <%s>' % (esc,fpart.strip(),rest) # dbg
    return lspace, esc, fpart.strip(), rest.lstrip()


# The escaped translators ALL receive a line where their own escape has been
# stripped.  Only '?' is valid at the end of the line, all others can only be
# placed at the start.

class LineInfo(object):
    """A single line of input and associated info.

    This is a utility class that mostly wraps the output of
    :func:`split_user_input` into a convenient object to be passed around
    during input transformations.

    Includes the following as properties: 

    line
      The original, raw line

    lspace
      Any early whitespace before actual text starts.

    esc
      The initial esc character (or characters, for double-char escapes like
      '??' or '!!').
    
    fpart
      The 'function part', which is basically the maximal initial sequence
      of valid python identifiers and the '.' character.  This is what is
      checked for alias and magic transformations, used for auto-calling,
      etc.
    
    rest
      Everything else on the line.
    """
    def __init__(self, line):
        self.line = line
        self.lspace, self.esc, self.fpart, self.rest = \
                             split_user_input(line)

    def __str__(self):                                                         
        return "LineInfo [%s|%s|%s|%s]" % (self.lspace, self.esc,
                                           self.fpart, self.rest)


# Transformations of the special syntaxes that don't rely on an explicit escape
# character but instead on patterns on the input line

# The core transformations are implemented as standalone functions that can be
# tested and validated in isolation.  Each of these uses a regexp, we
# pre-compile these and keep them close to each function definition for clarity

_assign_system_re = re.compile(r'(?P<lhs>(\s*)([\w\.]+)((\s*,\s*[\w\.]+)*))'
                               r'\s*=\s*!\s*(?P<cmd>.*)')

def transform_assign_system(line):
    """Handle the `files = !ls` syntax."""
    # FIXME: This transforms the line to use %sc, but we've listed that magic
    # as deprecated.  We should then implement this functionality in a
    # standalone api that we can transform to, without going through a
    # deprecated magic.
    m = _assign_system_re.match(line)
    if m is not None:
        cmd = m.group('cmd')
        lhs = m.group('lhs')
        expr = make_quoted_expr("sc -l = %s" % cmd)
        new_line = '%s = get_ipython().magic(%s)' % (lhs, expr)
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
        expr = make_quoted_expr(cmd)
        new_line = '%s = get_ipython().magic(%s)' % (lhs, expr)
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
        return '%sget_ipython().system(%s)' % (line_info.lspace,
                                               make_quoted_expr(cmd))

    @staticmethod
    def _tr_system2(line_info):
        "Translate lines escaped with: !!"
        cmd = line_info.line.lstrip()[2:]
        return '%sget_ipython().getoutput(%s)' % (line_info.lspace,
                                                  make_quoted_expr(cmd))

    @staticmethod
    def _tr_help(line_info):
        "Translate lines escaped with: ?/??"
        # A naked help line should just fire the intro help screen
        if not line_info.line[1:]:
            return 'get_ipython().show_usage()'

        # There may be one or two '?' at the end, move them to the front so that
        # the rest of the logic can assume escapes are at the start
        line = line_info.line
        if line.endswith('?'):
            line = line[-1] + line[:-1]
        if line.endswith('?'):
            line = line[-1] + line[:-1]
        line_info = LineInfo(line)

        # From here on, simply choose which level of detail to get.
        if line_info.esc == '?':
            pinfo = 'pinfo'
        elif line_info.esc == '??':
            pinfo = 'pinfo2'

        tpl = '%sget_ipython().magic("%s %s")'
        return tpl % (line_info.lspace, pinfo,
                      ' '.join([line_info.fpart, line_info.rest]).strip())

    @staticmethod
    def _tr_magic(line_info):
        "Translate lines escaped with: %"
        tpl = '%sget_ipython().magic(%s)'
        cmd = make_quoted_expr(' '.join([line_info.fpart,
                                         line_info.rest]).strip())
        return tpl % (line_info.lspace, cmd)

    @staticmethod
    def _tr_quote(line_info):
        "Translate lines escaped with: ,"
        return '%s%s("%s")' % (line_info.lspace, line_info.fpart,
                             '", "'.join(line_info.rest.split()) )

    @staticmethod
    def _tr_quote2(line_info):
        "Translate lines escaped with: ;"
        return '%s%s("%s")' % (line_info.lspace, line_info.fpart,
                               line_info.rest)

    @staticmethod
    def _tr_paren(line_info):
        "Translate lines escaped with: /"
        return '%s%s(%s)' % (line_info.lspace, line_info.fpart,
                             ", ".join(line_info.rest.split()))

    def __call__(self, line):
        """Class to transform lines that are explicitly escaped out.

        This calls the above _tr_* static methods for the actual line
        translations."""

        # Empty lines just get returned unmodified
        if not line or line.isspace():
            return line

        # Get line endpoints, where the escapes can be
        line_info = LineInfo(line)

        # If the escape is not at the start, only '?' needs to be special-cased.
        # All other escapes are only valid at the start
        if not line_info.esc in self.tr:
            if line.endswith(ESC_HELP):
                return self._tr_help(line_info)
            else:
                # If we don't recognize the escape, don't modify the line
                return line

        return self.tr[line_info.esc](line_info)


# A function-looking object to be used by the rest of the code.  The purpose of
# the class in this case is to organize related functionality, more than to
# manage state.
transform_escaped = EscapedTransformer()


class IPythonInputSplitter(InputSplitter):
    """An input splitter that recognizes all of IPython's special syntax."""

    def push(self, lines):
        """Push one or more lines of IPython input.
        """
        if not lines:
            return super(IPythonInputSplitter, self).push(lines)

        lines_list = lines.splitlines()

        transforms = [transform_escaped, transform_assign_system,
                      transform_assign_magic, transform_ipy_prompt,
                      transform_classic_prompt]

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
        
        if len(lines_list)>1 and self.input_mode == 'block':
            self.reset()
            changed_input_mode = True
            saved_input_mode = 'block'
            self.input_mode = 'line'

        try:
            push = super(IPythonInputSplitter, self).push
            for line in lines_list:
                if self._is_complete or not self._buffer or \
                   (self._buffer and self._buffer[-1].rstrip().endswith(':')):
                    for f in transforms:
                        line = f(line)

                out = push(line)
        finally:
            if changed_input_mode:
                self.input_mode = saved_input_mode
        
        return out

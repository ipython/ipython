"""Analysis of text input into executable blocks.

The main class in this module, :class:`InputSplitter`, is designed to break
input from either interactive, line-by-line environments or block-based ones,
into standalone blocks that can be executed by Python as 'single' statements
(thus triggering sys.displayhook).

For more details, see the class docstring below.
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

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

# FIXME: move these utilities to the general ward...

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
# Classes and functions
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
    input_mode = 'append'
    
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

          One of 'append', 'replace', default is 'append'.  This controls how
          new inputs are used: in 'append' mode, they are appended to the
          existing buffer and the whole buffer is compiled; in 'replace' mode,
          each new input completely replaces all prior inputs.  Replace mode is
          thus equivalent to prepending a full reset() to every push() call.

          In practice, line-oriented clients likely want to use 'append' mode
          while block-oriented ones will want to use 'replace'.
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
        if self.input_mode == 'replace':
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

                # Case 1, explicit dedent causes a break
                if _full_dedent and not next_line.startswith(' '):
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

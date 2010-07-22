"""Analysis of text input into executable blocks.

This is a simple example of how an interactive terminal-based client can use
this tool::

    bb = BlockBreaker()
    while not bb.interactive_block_ready():
        bb.push(raw_input('>>> '))
    print 'Input source was:\n', bb.source,
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
    """Return the default standard input encoding."""
    return getattr(sys.stdin, 'encoding', 'ascii')

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class BlockBreaker(object):
    # Command compiler
    compile = None
    # Number of spaces of indentation
    indent_spaces = 0
    # String, indicating the default input encoding
    encoding = ''
    # String where the current full source input is stored, properly encoded
    source = ''
    # Code object corresponding to the current source
    code = None
    # Boolean indicating whether the current block is complete
    is_complete = None
    # Input mode
    input_mode = 'append'
    
    # Private attributes
    
    # List
    _buffer = None
    
    def __init__(self, input_mode=None):
        """Create a new BlockBreaker instance.

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
        self.compile = codeop.CommandCompiler()
        self.encoding = get_input_encoding()
        self.input_mode = BlockBreaker.input_mode if input_mode is None \
                          else input_mode

    def reset(self):
        """Reset the input buffer and associated state."""
        self.indent_spaces = 0
        self._buffer[:] = []
        self.source = ''
        self.code = None

    def get_source(self, reset=False):
        """Return the input source.

        Parameters
        ----------
        reset : boolean
          If true, all state is reset and prior input forgotten.
        """
        out = self.source
        if reset:
            self.reset()
        return out

    def push(self, lines):
        """Push one ore more lines of input.

        This stores the given lines and returns a status code indicating
        whether the code forms a complete Python block or not.

        Any exceptions generated in compilation are allowed to propagate.

        Parameters
        ----------
        lines : string
          One or more lines of Python input.
        
        Returns
        -------
        is_complete : boolean
          True if the current input source (the result of the current input
        plus prior inputs) forms a complete Python execution block.  Note that
        this value is also stored as an attribute so it can be queried at any
        time.
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

        # Before calling compile(), reset the code object to None so that if an
        # exception is raised in compilation, we don't mislead by having
        # inconsistent code/source attributes.
        self.code, self.is_complete = None, None
        self.code = self.compile(source)
        # Compilation didn't produce any exceptions (though it may not have
        # given a complete code object)
        if self.code is None:
            self.is_complete = False
        else:
            self.is_complete = True
        self._update_indent(lines)
        return self.is_complete

    def interactive_block_ready(self):
        """Return whether a block of interactive input is ready for execution.

        This method is meant to be used by line-oriented frontends, who need to
        guess whether a block is complete or not based solely on prior and
        current input lines.  The BlockBreaker considers it has a complete
        interactive block when *all* of the following are true:

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
        """
        if not self.is_complete:
            return False
        if self.indent_spaces==0:
            return True
        last_line = self.source.splitlines()[-1]
        if not last_line or last_line.isspace():
            return True
        else:
            return False

    def split_blocks(self, lines):
        """Split a multiline string into multiple input blocks"""
        raise NotImplementedError

    #------------------------------------------------------------------------
    # Private interface
    #------------------------------------------------------------------------
    
    def _update_indent(self, lines):
        """Keep track of the indent level."""

        for line in remove_comments(lines).splitlines():
            
            if line and not line.isspace():
                if self.code is not None:
                    inisp = num_ini_spaces(line)
                    if inisp < self.indent_spaces:
                        self.indent_spaces = inisp

                if line[-1] == ':':
                    self.indent_spaces += 4
                elif dedent_re.match(line):
                    self.indent_spaces -= 4

    def _store(self, lines):
        """Store one or more lines of input.

        If input lines are not newline-terminated, a newline is automatically
        appended."""

        if lines.endswith('\n'):
            self._buffer.append(lines)
        else:
            self._buffer.append(lines+'\n')
        self.source = ''.join(self._buffer).encode(self.encoding)

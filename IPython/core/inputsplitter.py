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
import ast
import codeop
import re
import sys

# IPython modules
from IPython.utils.py3compat import cast_unicode
from IPython.core.inputtransformer import (leading_indent,
                                           classic_prompt,
                                           ipy_prompt,
                                           strip_encoding_cookie,
                                           cellmagic,
                                           assemble_logical_lines,
                                           help_end,
                                           escaped_commands,
                                           assign_from_magic,
                                           assign_from_system,
                                           assemble_python_lines,
                                           )

# These are available in this module for backwards compatibility.
from IPython.core.inputtransformer import (ESC_SHELL, ESC_SH_CAP, ESC_HELP,
                                        ESC_HELP2, ESC_MAGIC, ESC_MAGIC2,
                                        ESC_QUOTE, ESC_QUOTE2, ESC_PAREN, ESC_SEQUENCES)

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
    r'^\s+pass\s*$', # pass (optionally followed by trailing spaces)
    r'^\s+break\s*$', # break (optionally followed by trailing spaces)
    r'^\s+continue\s*$', # continue (optionally followed by trailing spaces)
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

def last_blank(src):
    """Determine if the input source ends in a blank.

    A blank is either a newline or a line consisting of whitespace.

    Parameters
    ----------
    src : string
      A single or multiline string.
    """
    if not src: return False
    ll  = src.splitlines()[-1]
    return (ll == '') or ll.isspace()


last_two_blanks_re = re.compile(r'\n\s*\n\s*$', re.MULTILINE)
last_two_blanks_re2 = re.compile(r'.+\n\s*\n\s+$', re.MULTILINE)

def last_two_blanks(src):
    """Determine if the input source ends in two blanks.

    A blank is either a newline or a line consisting of whitespace.

    Parameters
    ----------
    src : string
      A single or multiline string.
    """
    if not src: return False
    # The logic here is tricky: I couldn't get a regexp to work and pass all
    # the tests, so I took a different approach: split the source by lines,
    # grab the last two and prepend '###\n' as a stand-in for whatever was in
    # the body before the last two lines.  Then, with that structure, it's
    # possible to analyze with two regexps.  Not the most elegant solution, but
    # it works.  If anyone tries to change this logic, make sure to validate
    # the whole test suite first!
    new_src = '\n'.join(['###\n'] + src.splitlines()[-2:])
    return (bool(last_two_blanks_re.match(new_src)) or
            bool(last_two_blanks_re2.match(new_src)) )


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

    # Private attributes

    # List with lines of input accumulated so far
    _buffer = None
    # Command compiler
    _compile = None
    # Mark when input has changed indentation all the way back to flush-left
    _full_dedent = False
    # Boolean indicating whether the current block is complete
    _is_complete = None

    def __init__(self):
        """Create a new InputSplitter instance.
        """
        self._buffer = []
        self._compile = codeop.CommandCompiler()
        self.encoding = get_input_encoding()

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
          this value is also stored as a private attribute (``_is_complete``), so it
          can be queried at any time.
        """
        self._store(lines)
        source = self.source

        # Before calling _compile(), reset the code object to None so that if an
        # exception is raised in compilation, we don't mislead by having
        # inconsistent code/source attributes.
        self.code, self._is_complete = None, None

        # Honor termination lines properly
        if source.endswith('\\\n'):
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
        interactive block and will not accept more input when either:
        
        * A SyntaxError is raised

        * The code is complete and consists of a single line or a single
          non-compound statement

        * The code is complete and has a blank line at the end

        If the current input produces a syntax error, this method immediately
        returns False but does *not* raise the syntax error exception, as
        typically clients will want to send invalid syntax to an execution
        backend which might convert the invalid syntax into valid Python via
        one of the dynamic IPython mechanisms.
        """

        # With incomplete input, unconditionally accept more
        # A syntax error also sets _is_complete to True - see push()
        if not self._is_complete:
            #print("Not complete")  # debug
            return True
        
        # The user can make any (complete) input execute by leaving a blank line
        last_line = self.source.splitlines()[-1]
        if (not last_line) or last_line.isspace():
            #print("Blank line")  # debug
            return False
        
        # If there's just a single line or AST node, and we're flush left, as is
        # the case after a simple statement such as 'a=1', we want to execute it
        # straight away.
        if self.indent_spaces==0:
            if len(self.source.splitlines()) <= 1:
                return False
            
            try:
                code_ast = ast.parse(u''.join(self._buffer))
            except Exception:
                #print("Can't parse AST")  # debug
                return False
            else:
                if len(code_ast.body) == 1 and \
                                    not hasattr(code_ast.body[0], 'body'):
                    #print("Simple statement")  # debug
                    return False

        # General fallback - accept more code
        return True

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


class IPythonInputSplitter(InputSplitter):
    """An input splitter that recognizes all of IPython's special syntax."""

    # String with raw, untransformed input.
    source_raw = ''
    
    # Flag to track when a transformer has stored input that it hasn't given
    # back yet.
    transformer_accumulating = False
    
    # Flag to track when assemble_python_lines has stored input that it hasn't
    # given back yet.
    within_python_line = False

    # Private attributes

    # List with lines of raw input accumulated so far.
    _buffer_raw = None

    def __init__(self, line_input_checker=True, physical_line_transforms=None,
                    logical_line_transforms=None, python_line_transforms=None):
        super(IPythonInputSplitter, self).__init__()
        self._buffer_raw = []
        self._validate = True
        
        if physical_line_transforms is not None:
            self.physical_line_transforms = physical_line_transforms
        else:
            self.physical_line_transforms = [
                                             leading_indent(),
                                             classic_prompt(),
                                             ipy_prompt(),
                                             strip_encoding_cookie(),
                                             cellmagic(end_on_blank_line=line_input_checker),
                                            ]
        
        self.assemble_logical_lines = assemble_logical_lines()
        if logical_line_transforms is not None:
            self.logical_line_transforms = logical_line_transforms
        else:
            self.logical_line_transforms = [
                                            help_end(),
                                            escaped_commands(),
                                            assign_from_magic(),
                                            assign_from_system(),
                                           ]
        
        self.assemble_python_lines = assemble_python_lines()
        if python_line_transforms is not None:
            self.python_line_transforms = python_line_transforms
        else:
            # We don't use any of these at present
            self.python_line_transforms = []
    
    @property
    def transforms(self):
        "Quick access to all transformers."
        return self.physical_line_transforms + \
            [self.assemble_logical_lines] + self.logical_line_transforms + \
            [self.assemble_python_lines]  + self.python_line_transforms
    
    @property
    def transforms_in_use(self):
        """Transformers, excluding logical line transformers if we're in a
        Python line."""
        t = self.physical_line_transforms[:]
        if not self.within_python_line:
            t += [self.assemble_logical_lines] + self.logical_line_transforms
        return t + [self.assemble_python_lines] + self.python_line_transforms

    def reset(self):
        """Reset the input buffer and associated state."""
        super(IPythonInputSplitter, self).reset()
        self._buffer_raw[:] = []
        self.source_raw = ''
        self.transformer_accumulating = False
        self.within_python_line = False
        for t in self.transforms:
            t.reset()
    
    def flush_transformers(self):
        def _flush(transform, out):
            if out is not None:
                tmp = transform.push(out)
                return tmp or transform.reset() or None
            else:
                return transform.reset() or None
        
        out = None
        for t in self.transforms_in_use:
            out = _flush(t, out)
        
        if out is not None:
            self._store(out)

    def source_raw_reset(self):
        """Return input and raw source and perform a full reset.
        """
        self.flush_transformers()
        out = self.source
        out_r = self.source_raw
        self.reset()
        return out, out_r
    
    def source_reset(self):
        self.flush_transformers()
        return super(IPythonInputSplitter, self).source_reset()

    def push_accepts_more(self):
        if self.transformer_accumulating:
            return True
        else:
            return super(IPythonInputSplitter, self).push_accepts_more()

    def transform_cell(self, cell):
        """Process and translate a cell of input.
        """
        self.reset()
        self.push(cell)
        return self.source_reset()

    def push(self, lines):
        """Push one or more lines of IPython input.

        This stores the given lines and returns a status code indicating
        whether the code forms a complete Python block or not, after processing
        all input lines for special IPython syntax.

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

        # We must ensure all input is pure unicode
        lines = cast_unicode(lines, self.encoding)
        
        # ''.splitlines() --> [], but we need to push the empty line to transformers
        lines_list = lines.splitlines()
        if not lines_list:
            lines_list = ['']

        # Store raw source before applying any transformations to it.  Note
        # that this must be done *after* the reset() call that would otherwise
        # flush the buffer.
        self._store(lines, self._buffer_raw, 'source_raw')

        for line in lines_list:
            out = self.push_line(line)

        return out
    
    def push_line(self, line):
        buf = self._buffer
        
        def _accumulating(dbg):
            #print(dbg)
            self.transformer_accumulating = True
            return False
        
        for transformer in self.physical_line_transforms:
            line = transformer.push(line)
            if line is None:
                return _accumulating(transformer)
        
        if not self.within_python_line:
            line = self.assemble_logical_lines.push(line)
            if line is None:
                return _accumulating('acc logical line')        
        
            for transformer in self.logical_line_transforms:
                line = transformer.push(line)
                if line is None:
                    return _accumulating(transformer)
        
        line = self.assemble_python_lines.push(line)
        if line is None:
            self.within_python_line = True
            return _accumulating('acc python line')
        else:
            self.within_python_line = False
        
        for transformer in self.python_line_transforms:
            line = transformer.push(line)
            if line is None:
                return _accumulating(transformer)

        #print("transformers clear") #debug
        self.transformer_accumulating = False
        return super(IPythonInputSplitter, self).push(line)

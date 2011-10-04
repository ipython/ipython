# -*- coding: utf-8 -*-
"""String interpolation for Python (by Ka-Ping Yee, 14 Feb 2000).

This module lets you quickly and conveniently interpolate values into
strings (in the flavour of Perl or Tcl, but with less extraneous
punctuation).  You get a bit more power than in the other languages,
because this module allows subscripting, slicing, function calls,
attribute lookup, or arbitrary expressions.  Variables and expressions
are evaluated in the namespace of the caller.

The itpl() function returns the result of interpolating a string, and
printpl() prints out an interpolated string.  Here are some examples:

    from Itpl import printpl
    printpl("Here is a $string.")
    printpl("Here is a $module.member.")
    printpl("Here is an $object.member.")
    printpl("Here is a $functioncall(with, arguments).")
    printpl("Here is an ${arbitrary + expression}.")
    printpl("Here is an $array[3] member.")
    printpl("Here is a $dictionary['member'].")

The filter() function filters a file object so that output through it
is interpolated.  This lets you produce the illusion that Python knows
how to do interpolation:

    import Itpl
    sys.stdout = Itpl.filter()
    f = "fancy"
    print "Is this not $f?"
    print "Standard output has been replaced with a $sys.stdout object."
    sys.stdout = Itpl.unfilter()
    print "Okay, back $to $normal."

Under the hood, the Itpl class represents a string that knows how to
interpolate values.  An instance of the class parses the string once
upon initialization; the evaluation and substitution can then be done
each time the instance is evaluated with str(instance).  For example:

    from Itpl import Itpl
    s = Itpl("Here is $foo.")
    foo = 5
    print str(s)
    foo = "bar"
    print str(s)
"""

#*****************************************************************************
#
# Copyright (c) 2001 Ka-Ping Yee <ping@lfw.org>
#
#
# Published under the terms of the MIT license, hereby reproduced:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
#*****************************************************************************

__author__  = 'Ka-Ping Yee <ping@lfw.org>'
__license__ = 'MIT'

import sys
from tokenize import tokenprog

class ItplError(ValueError):
    def __init__(self, text, pos):
        self.text = text
        self.pos = pos
    def __str__(self):
        return "unfinished expression in %s at char %d" % (
            repr(self.text), self.pos)

def matchorfail(text, pos):
    match = tokenprog.match(text, pos)
    if match is None:
        raise ItplError(text, pos)
    return match, match.end()

class Itpl:
    """Class representing a string with interpolation abilities.

    Upon creation, an instance works out what parts of the format
    string are literal and what parts need to be evaluated.  The
    evaluation and substitution happens in the namespace of the
    caller when str(instance) is called."""

    def __init__(self, format,codec='utf_8',encoding_errors='backslashreplace'):
        """The single mandatory argument to this constructor is a format
        string.

        The format string is parsed according to the following rules:

        1.  A dollar sign and a name, possibly followed by any of:
              - an open-paren, and anything up to the matching paren
              - an open-bracket, and anything up to the matching bracket
              - a period and a name
            any number of times, is evaluated as a Python expression.

        2.  A dollar sign immediately followed by an open-brace, and
            anything up to the matching close-brace, is evaluated as
            a Python expression.

        3.  Outside of the expressions described in the above two rules,
            two dollar signs in a row give you one literal dollar sign.

        Optional arguments:

        - codec('utf_8'): a string containing the name of a valid Python
        codec.

        - encoding_errors('backslashreplace'): a string with a valid error handling
        policy.  See the codecs module documentation for details.

        These are used to encode the format string if a call to str() fails on
        the expanded result."""

        if not isinstance(format,basestring):
            raise TypeError, "needs string initializer"
        self.format = format
        self.codec = codec
        self.encoding_errors = encoding_errors

        namechars = "abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
        chunks = []
        pos = 0

        while 1:
            dollar = format.find("$", pos)
            if dollar < 0: break
            nextchar = format[dollar+1]

            if nextchar == "{":
                chunks.append((0, format[pos:dollar]))
                pos, level = dollar+2, 1
                while level:
                    match, pos = matchorfail(format, pos)
                    tstart, tend = match.regs[3]
                    token = format[tstart:tend]
                    if token == "{": level = level+1
                    elif token == "}": level = level-1
                chunks.append((1, format[dollar+2:pos-1]))

            elif nextchar in namechars:
                chunks.append((0, format[pos:dollar]))
                match, pos = matchorfail(format, dollar+1)
                while pos < len(format):
                    if format[pos] == "." and \
                        pos+1 < len(format) and format[pos+1] in namechars:
                        match, pos = matchorfail(format, pos+1)
                    elif format[pos] in "([":
                        pos, level = pos+1, 1
                        while level:
                            match, pos = matchorfail(format, pos)
                            tstart, tend = match.regs[3]
                            token = format[tstart:tend]
                            if token[0] in "([": level = level+1
                            elif token[0] in ")]": level = level-1
                    else: break
                chunks.append((1, format[dollar+1:pos]))

            else:
                chunks.append((0, format[pos:dollar+1]))
                pos = dollar + 1 + (nextchar == "$")

        if pos < len(format): chunks.append((0, format[pos:]))
        self.chunks = chunks

    def __repr__(self):
        return "<Itpl %s >" % repr(self.format)

    def _str(self,glob,loc):
        """Evaluate to a string in the given globals/locals.

        The final output is built by calling str(), but if this fails, the
        result is encoded with the instance's codec and error handling policy,
        via a call to out.encode(self.codec,self.encoding_errors)"""
        result = []
        app = result.append
        for live, chunk in self.chunks:
            if live: app(str(eval(chunk,glob,loc)))
            else: app(chunk)
        out = ''.join(result)
        try:
            return str(out)
        except UnicodeError:
            return out.encode(self.codec,self.encoding_errors)

    def __str__(self):
        """Evaluate and substitute the appropriate parts of the string."""

        # We need to skip enough frames to get to the actual caller outside of
        # Itpl.
        frame = sys._getframe(1)
        while frame.f_globals["__name__"] == __name__: frame = frame.f_back
        loc, glob = frame.f_locals, frame.f_globals

        return self._str(glob,loc)

class ItplNS(Itpl):
    """Class representing a string with interpolation abilities.

    This inherits from Itpl, but at creation time a namespace is provided
    where the evaluation will occur.  The interpolation becomes a bit more
    efficient, as no traceback needs to be extracte.  It also allows the
    caller to supply a different namespace for the interpolation to occur than
    its own."""

    def __init__(self, format,globals,locals=None,
                 codec='utf_8',encoding_errors='backslashreplace'):
        """ItplNS(format,globals[,locals]) -> interpolating string instance.

        This constructor, besides a format string, takes a globals dictionary
        and optionally a locals (which defaults to globals if not provided).

        For further details, see the Itpl constructor."""

        if locals is None:
            locals = globals
        self.globals = globals
        self.locals = locals
        Itpl.__init__(self,format,codec,encoding_errors)

    def __str__(self):
        """Evaluate and substitute the appropriate parts of the string."""
        return self._str(self.globals,self.locals)

    def __repr__(self):
        return "<ItplNS %s >" % repr(self.format)

# utilities for fast printing
def itpl(text): return str(Itpl(text))
def printpl(text): print itpl(text)
# versions with namespace
def itplns(text,globals,locals=None): return str(ItplNS(text,globals,locals))
def printplns(text,globals,locals=None): print itplns(text,globals,locals)

class ItplFile:
    """A file object that filters each write() through an interpolator."""
    def __init__(self, file): self.file = file
    def __repr__(self): return "<interpolated " + repr(self.file) + ">"
    def __getattr__(self, attr): return getattr(self.file, attr)
    def write(self, text): self.file.write(str(Itpl(text)))

def filter(file=sys.stdout):
    """Return an ItplFile that filters writes to the given file object.

    'file = filter(file)' replaces 'file' with a filtered object that
    has a write() method.  When called with no argument, this creates
    a filter to sys.stdout."""
    return ItplFile(file)

def unfilter(ifile=None):
    """Return the original file that corresponds to the given ItplFile.

    'file = unfilter(file)' undoes the effect of 'file = filter(file)'.
    'sys.stdout = unfilter()' undoes the effect of 'sys.stdout = filter()'."""
    return ifile and ifile.file or sys.stdout.file

# -*- coding: utf-8 -*-
"""
Class and program to colorize python source code for ANSI terminals.

Based on an HTML code highlighter by Jurgen Hermann found at:
http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52298

Modifications by Fernando Perez (fperez@colorado.edu).

Information on the original HTML highlighter follows:

MoinMoin - Python Source Parser

Title: Colorize Python source using the built-in tokenizer

Submitter: Jurgen Hermann
Last Updated:2001/04/06

Version no:1.2

Description:

This code is part of MoinMoin (http://moin.sourceforge.net/) and converts
Python source code to HTML markup, rendering comments, keywords,
operators, numeric and string literals in different colors.

It shows how to use the built-in keyword, token and tokenize modules to
scan Python source code and re-emit it with no changes to its original
formatting (which is the hard part).
"""

__all__ = ['ANSICodeColors','Parser']

_scheme_default = 'Linux'

# Imports
import StringIO
import keyword
import os
import optparse
import sys
import token
import tokenize

try:
    generate_tokens = tokenize.generate_tokens
except AttributeError:
    # Python 3. Note that we use the undocumented _tokenize because it expects
    # strings, not bytes. See also Python issue #9969.
    generate_tokens = tokenize._tokenize

from IPython.utils.coloransi import *

#############################################################################
### Python Source Parser (does Hilighting)
#############################################################################

_KEYWORD = token.NT_OFFSET + 1
_TEXT    = token.NT_OFFSET + 2

#****************************************************************************
# Builtin color schemes

Colors = TermColors  # just a shorthand

# Build a few color schemes
NoColor = ColorScheme(
    'NoColor',{
    token.NUMBER     : Colors.NoColor,
    token.OP         : Colors.NoColor,
    token.STRING     : Colors.NoColor,
    tokenize.COMMENT : Colors.NoColor,
    token.NAME       : Colors.NoColor,
    token.ERRORTOKEN : Colors.NoColor,

    _KEYWORD         : Colors.NoColor,
    _TEXT            : Colors.NoColor,

    'normal'         : Colors.NoColor  # color off (usu. Colors.Normal)
    }  )

LinuxColors = ColorScheme(
    'Linux',{
    token.NUMBER     : Colors.LightCyan,
    token.OP         : Colors.Yellow,
    token.STRING     : Colors.LightBlue,
    tokenize.COMMENT : Colors.LightRed,
    token.NAME       : Colors.Normal,
    token.ERRORTOKEN : Colors.Red,

    _KEYWORD         : Colors.LightGreen,
    _TEXT            : Colors.Yellow,

    'normal'         : Colors.Normal  # color off (usu. Colors.Normal)
    } )

LightBGColors = ColorScheme(
    'LightBG',{
    token.NUMBER     : Colors.Cyan,
    token.OP         : Colors.Blue,
    token.STRING     : Colors.Blue,
    tokenize.COMMENT : Colors.Red,
    token.NAME       : Colors.Normal,
    token.ERRORTOKEN : Colors.Red,

    _KEYWORD         : Colors.Green,
    _TEXT            : Colors.Blue,

    'normal'         : Colors.Normal  # color off (usu. Colors.Normal)
    }  )

# Build table of color schemes (needed by the parser)
ANSICodeColors = ColorSchemeTable([NoColor,LinuxColors,LightBGColors],
                                  _scheme_default)

class Parser:
    """ Format colored Python source.
    """

    def __init__(self, color_table=None,out = sys.stdout):
        """ Create a parser with a specified color table and output channel.

        Call format() to process code.
        """
        self.color_table = color_table and color_table or ANSICodeColors
        self.out = out

    def format(self, raw, out = None, scheme = ''):
        return self.format2(raw, out, scheme)[0]

    def format2(self, raw, out = None, scheme = ''):
        """ Parse and send the colored source.

        If out and scheme are not specified, the defaults (given to
        constructor) are used.

        out should be a file-type object. Optionally, out can be given as the
        string 'str' and the parser will automatically return the output in a
        string."""
        
        string_output = 0
        if out == 'str' or self.out == 'str' or \
           isinstance(self.out,StringIO.StringIO):
            # XXX - I don't really like this state handling logic, but at this
            # point I don't want to make major changes, so adding the
            # isinstance() check is the simplest I can do to ensure correct
            # behavior.
            out_old = self.out
            self.out = StringIO.StringIO()
            string_output = 1
        elif out is not None:
            self.out = out

        # Fast return of the unmodified input for NoColor scheme
        if scheme == 'NoColor':
            error = False
            self.out.write(raw)
            if string_output:
                return raw,error
            else:
                return None,error
        
        # local shorthands
        colors = self.color_table[scheme].colors
        self.colors = colors # put in object so __call__ sees it

        # Remove trailing whitespace and normalize tabs
        self.raw = raw.expandtabs().rstrip()
        
        # store line offsets in self.lines
        self.lines = [0, 0]
        pos = 0
        raw_find = self.raw.find
        lines_append = self.lines.append
        while 1:
            pos = raw_find('\n', pos) + 1
            if not pos: break
            lines_append(pos)
        lines_append(len(self.raw))

        # parse the source and write it
        self.pos = 0
        text = StringIO.StringIO(self.raw)

        error = False
        try:
            for atoken in generate_tokens(text.readline):
                self(*atoken)
        except tokenize.TokenError as ex:
            msg = ex.args[0]
            line = ex.args[1][0]
            self.out.write("%s\n\n*** ERROR: %s%s%s\n" %
                           (colors[token.ERRORTOKEN],
                            msg, self.raw[self.lines[line]:],
                            colors.normal)
                           )
            error = True
        self.out.write(colors.normal+'\n')
        if string_output:
            output = self.out.getvalue()
            self.out = out_old
            return (output, error)
        return (None, error)

    def __call__(self, toktype, toktext, (srow,scol), (erow,ecol), line):
        """ Token handler, with syntax highlighting."""

        # local shorthands
        colors = self.colors
        owrite = self.out.write

        # line separator, so this works across platforms
        linesep = os.linesep

        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)

        # handle newlines
        if toktype in [token.NEWLINE, tokenize.NL]:
            owrite(linesep)
            return

        # send the original whitespace, if needed
        if newpos > oldpos:
            owrite(self.raw[oldpos:newpos])

        # skip indenting tokens
        if toktype in [token.INDENT, token.DEDENT]:
            self.pos = newpos
            return

        # map token type to a color group
        if token.LPAR <= toktype and toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        color = colors.get(toktype, colors[_TEXT])

        #print '<%s>' % toktext,    # dbg

        # Triple quoted strings must be handled carefully so that backtracking
        # in pagers works correctly. We need color terminators on _each_ line.
        if linesep in toktext:
            toktext = toktext.replace(linesep, '%s%s%s' %
                                      (colors.normal,linesep,color))

        # send text
        owrite('%s%s%s' % (color,toktext,colors.normal))
            
def main(argv=None):
    """Run as a command-line script: colorize a python file or stdin using ANSI
    color escapes and print to stdout.

    Inputs:

      - argv(None): a list of strings like sys.argv[1:] giving the command-line
        arguments. If None, use sys.argv[1:].
    """

    usage_msg = """%prog [options] [filename]

Colorize a python file or stdin using ANSI color escapes and print to stdout.
If no filename is given, or if filename is -, read standard input."""

    parser = optparse.OptionParser(usage=usage_msg)
    newopt = parser.add_option
    newopt('-s','--scheme',metavar='NAME',dest='scheme_name',action='store',
           choices=['Linux','LightBG','NoColor'],default=_scheme_default,
           help="give the color scheme to use. Currently only 'Linux'\
 (default) and 'LightBG' and 'NoColor' are implemented (give without\
 quotes)")

    opts,args = parser.parse_args(argv)

    if len(args) > 1:
        parser.error("you must give at most one filename.")

    if len(args) == 0:
        fname = '-' # no filename given; setup to read from stdin
    else:
        fname = args[0]

    if fname == '-':
        stream = sys.stdin
    else:
        try:
            stream = file(fname)
        except IOError,msg:
            print >> sys.stderr, msg
            sys.exit(1)

    parser = Parser()

    # we need nested try blocks because pre-2.5 python doesn't support unified
    # try-except-finally
    try:
        try:
            # write colorized version to stdout
            parser.format(stream.read(),scheme=opts.scheme_name)
        except IOError,msg:
            # if user reads through a pager and quits, don't print traceback
            if msg.args != (32,'Broken pipe'):
                raise
    finally:
        if stream is not sys.stdin:
            stream.close() # in case a non-handled exception happened above

if __name__ == "__main__":
    main()

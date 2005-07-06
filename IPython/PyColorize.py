# -*- coding: utf-8 -*-
"""
    Class and program to colorize python source code for ANSI terminals.

    Based on an HTML code highlighter by Jurgen Hermann found at:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52298

    Modifications by Fernando Perez (fperez@colorado.edu).

    Information on the original HTML highlighter follows:
    
    MoinMoin - Python Source Parser

    Title:olorize Python source using the built-in tokenizer
           
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

    $Id: PyColorize.py 485 2005-01-27 19:15:39Z fperez $"""

__all__ = ['ANSICodeColors','Parser']

_scheme_default = 'Linux'

# Imports
import string, sys, os, cStringIO
import keyword, token, tokenize

from IPython.ColorANSI import *

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
    token.NAME       : Colors.White,
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
    token.NAME       : Colors.Black,
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
        """ Parse and send the colored source.

        If out and scheme are not specified, the defaults (given to
        constructor) are used.

        out should be a file-type object. Optionally, out can be given as the
        string 'str' and the parser will automatically return the output in a
        string."""
        
        self.raw = string.strip(string.expandtabs(raw))
        string_output = 0
        if out == 'str' or self.out == 'str':
            out_old = self.out
            self.out = cStringIO.StringIO()
            string_output = 1
        elif out is not None:
            self.out = out
        # local shorthand
        colors = self.color_table[scheme].colors
        self.colors = colors # put in object so __call__ sees it
        # store line offsets in self.lines
        self.lines = [0, 0]
        pos = 0
        while 1:
            pos = string.find(self.raw, '\n', pos) + 1
            if not pos: break
            self.lines.append(pos)
        self.lines.append(len(self.raw))

        # parse the source and write it
        self.pos = 0
        text = cStringIO.StringIO(self.raw)
        #self.out.write('<pre><font face="Courier New">')
        try:
            tokenize.tokenize(text.readline, self)
        except tokenize.TokenError, ex:
            msg = ex[0]
            line = ex[1][0]
            self.out.write("%s\n\n*** ERROR: %s%s%s\n" %
                           (colors[token.ERRORTOKEN],
                            msg, self.raw[self.lines[line]:],
                            colors.normal)
                           )
        self.out.write(colors.normal+'\n')
        if string_output:
            output = self.out.getvalue()
            self.out = out_old
            return output

    def __call__(self, toktype, toktext, (srow,scol), (erow,ecol), line):
        """ Token handler, with syntax highlighting."""

        # local shorthand
        colors = self.colors

        # line separator, so this works across platforms
        linesep = os.linesep

        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)

        # handle newlines
        if toktype in [token.NEWLINE, tokenize.NL]:
            self.out.write(linesep)
            return

        # send the original whitespace, if needed
        if newpos > oldpos:
            self.out.write(self.raw[oldpos:newpos])

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
        self.out.write('%s%s%s' % (color,toktext,colors.normal))
            
def main():
    """Colorize a python file using ANSI color escapes and print to stdout.

    Usage:
      %s [-s scheme] filename

    Options:

      -s scheme: give the color scheme to use. Currently only 'Linux'
      (default) and 'LightBG' and 'NoColor' are implemented (give without
      quotes).  """  

    def usage():
        print >> sys.stderr, main.__doc__ % sys.argv[0]
        sys.exit(1)
        
    # FIXME: rewrite this to at least use getopt
    try:
        if sys.argv[1] == '-s':
            scheme_name = sys.argv[2]
            del sys.argv[1:3]
        else:
            scheme_name = _scheme_default
        
    except:
        usage()

    try:
        fname = sys.argv[1]
    except:
        usage()
        
    # write colorized version to stdout
    parser = Parser()
    try:
        parser.format(file(fname).read(),scheme = scheme_name)
    except IOError,msg:
        # if user reads through a pager and quits, don't print traceback
        if msg.args != (32,'Broken pipe'):
            raise

if __name__ == "__main__":
    main()

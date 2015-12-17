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
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

__all__ = ['ANSICodeColors','Parser']

_scheme_default = 'Linux'


# Imports
import io
import sys
import token
import tokenize

try:
    generate_tokens = tokenize.generate_tokens
except AttributeError:
    # Python 3. Note that we use the undocumented _tokenize because it expects
    # strings, not bytes. See also Python issue #9969.
    generate_tokens = tokenize._tokenize

from IPython.utils.coloransi import TermColors, InputTermColors ,ColorScheme, ColorSchemeTable
from IPython.utils.py3compat import PY3

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import  Terminal256Formatter
import pygments.styles

from collections import defaultdict

from IPython.utils.linux import LinuxStyle
from IPython.utils.lightbg import LightBGStyle, NoColorStyle
from traitlets.config import Configurable
from traitlets import Unicode, Bool

available_themes = lambda : [s for s in pygments.styles.get_all_styles()]+['NoColor','LightBG','Linux']

class Colorable(Configurable):
    """
    A subclass of configurable for all the classes that have a `default_scheme`
    """
    default_style=Unicode('lightbg', config=True)


## map from lower case styles 
# to uppercase one. 
style_map = {
    'linux': LinuxStyle,
    'Linux': LinuxStyle,
    'lightbg': LightBGStyle, 
    'LightBG': LightBGStyle, 
    'nocolor': NoColorStyle,
    'NoColors': NoColorStyle,
    'NoColor': NoColorStyle,
    }

## map to old-style Prompt token name to new ones. 
tmap = {
    'in_number': 'Token.InPrompt.Color',
    'in_prompt': 'Token.InPrompt.Number',
    'out_number': 'Token.OutPrompt.Color',
    'out_prompt': 'Token.OutPrompt.Number',
}

## map to default Token name, if the definition for above token do not exist
# (eg, all the non-ipython styles in pygments) 
fallbackp = defaultdict(lambda:'Token.Literal.String',{
    'in_number': 'Token.Keyword',
    'in_prompt': 'Token.Keyword',
    'out_number': 'Token.Generic.Output',
    'out_prompt': 'Token.Generic.Output',
})


class debugWrappAccessor(dict):
    def __getitem__(self, key):
        return ('<'+key+'>', '</'+key+'>')

import random

class wrappAccessor(dict):
    """
    Wrapper Pygments styles Setting dict that wrap colors codes in \001 and \002
    to correctly calculate the length of formatted strings when redrawing the
    prompts.
    """

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except:
            #print('Asked for unknown token:', key, 'of type', type(key))
            pass
        if isinstance(key, str):
            for k in (key, tmap.get(key), fallbackp.get(key)):
                try:
                    escape_code = dict.__getitem__(self, k)
                except KeyError:
                    escape_code = None
                if escape_code:
                    break
            if escape_code:
                # if there are escape codes, wrap them in
                # print('got ec.')
                v = ['\001%s\002'% x  if x else '' for x in escape_code ] 
                return v
            #print('return random rainbow mode for unknown token types')
            return dict.__getitem__(self, random.choice(list(self.keys())))
        else:
            print('Unknown Key Type will raise')
            raise ValueError('Unknown Key Type')
                 
def normalize_style(style):
    return style_map.get(style, style)

class IPythonTerm256Formatter(Colorable, Terminal256Formatter ):
    """Pygments Terminal formater special-cased for IPython

    Addition of single_format, that **returns** a single formatted token.
    Wraps colorcodes on \001 and \002 to correctly measure length of colored
    strings. 
    """

    debug = Bool(False, config=True, help='replace color by <tagname>...<tagname>')
    
    def __init__(self, *args, **kwargs):
        Colorable.__init__(self, *args, **kwargs)

        if kwargs.get('style'):
            kwargs['style'] = normalize_style(kwargs['style'])
        else:
            kwargs['style']= normalize_style(self.default_style)
        
        Terminal256Formatter.__init__(self, *args, **kwargs)

        # patch for subclass to go through accessors.
        if self.debug:
            self.style_string = debugWrappAccessor(self.style_string)
        else:
            self.style_string = wrappAccessor(self.style_string)
    
        
    def single_fmt(self, string, ttype):
        """
        Format string with the style of ttype token.
        """
        S = io.StringIO()
        self.format([(ttype,string)], S)
        S.seek(0)
        return S.read()


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
    'header'         : Colors.NoColor,
    token.NUMBER     : Colors.NoColor,
    token.OP         : Colors.NoColor,
    token.STRING     : Colors.NoColor,
    tokenize.COMMENT : Colors.NoColor,
    token.NAME       : Colors.NoColor,
    token.ERRORTOKEN : Colors.NoColor,

    _KEYWORD         : Colors.NoColor,
    _TEXT            : Colors.NoColor,

    'in_prompt'      : InputTermColors.NoColor,  # Input prompt
    'in_number'      : InputTermColors.NoColor,  # Input prompt number
    'in_prompt2'     : InputTermColors.NoColor, # Continuation prompt
    'in_normal'      : InputTermColors.NoColor,  # color off (usu. Colors.Normal)

    'out_prompt'     : Colors.NoColor, # Output prompt
    'out_number'     : Colors.NoColor, # Output prompt number

    'normal'         : Colors.NoColor  # color off (usu. Colors.Normal)
    }  )

LinuxColors = ColorScheme(
    'Linux',{
    'header'         : Colors.LightRed,
    token.NUMBER     : Colors.LightCyan,
    token.OP         : Colors.Yellow,
    token.STRING     : Colors.LightBlue,
    tokenize.COMMENT : Colors.LightRed,
    token.NAME       : Colors.Normal,
    token.ERRORTOKEN : Colors.Red,

    _KEYWORD         : Colors.LightGreen,
    _TEXT            : Colors.Yellow,

    'in_prompt'      : InputTermColors.Green,
    'in_number'      : InputTermColors.LightGreen,
    'in_prompt2'     : InputTermColors.Green,
    'in_normal'      : InputTermColors.Normal,  # color off (usu. Colors.Normal)

    'out_prompt'     : Colors.Red,
    'out_number'     : Colors.LightRed,

    'normal'         : Colors.Normal  # color off (usu. Colors.Normal)
    
    } )

LightBGColors = ColorScheme(
    'LightBG',{
    'header'         : Colors.Red,
    token.NUMBER     : Colors.Cyan,
    token.OP         : Colors.Blue,
    token.STRING     : Colors.Blue,
    tokenize.COMMENT : Colors.Red,
    token.NAME       : Colors.Normal,
    token.ERRORTOKEN : Colors.Red,

    _KEYWORD         : Colors.Green,
    _TEXT            : Colors.Blue,

    'in_prompt'      : InputTermColors.Blue,
    'in_number'      : InputTermColors.LightBlue,
    'in_prompt2'     : InputTermColors.Blue,
    'in_normal'      : InputTermColors.Normal,  # color off (usu. Colors.Normal)

    'out_prompt'     : Colors.Red,
    'out_number'     : Colors.LightRed,

    'normal'         : Colors.Normal  # color off (usu. Colors.Normal)
    }  )

# Build table of color schemes (needed by the parser)
ANSICodeColors = ColorSchemeTable([NoColor,LinuxColors,LightBGColors],
                                  _scheme_default)

class Parser(Colorable):
    """ Format colored Python source.
    """

    style = Unicode(None, allow_none=True)

    def _style_changed(self, name, old, new):
        if new != old:
            self._form = IPythonTerm256Formatter(style=new, parent=self)
            return new
        

    def __init__(self, color_table=None, out=sys.stdout, parent=None, style=None):
        """ Create a parser with a specified color table and output channel.

        color_table: DEPRECATED. Has no effects.

        Call format() to process code.
        """
        super(Parser, self).__init__(parent=parent)
        self.out = out
        self._lex = PythonLexer()
        if style: 
            self.style=style
        else:
            self.style = self.default_style
        self._form = IPythonTerm256Formatter(style=self.style, parent=self)
        
    def _pylight(self, code):
        return highlight(code, self._lex, self._form)

    def format(self, raw, out = None, scheme = ''):
        """
        Format a lost token and return a unicode string with escape sequences..
        """
        return self.format2(raw, out, scheme)[0]

    def format2(self, raw, out = None, scheme = ''):
        """ Parse and send the colored source.

        If out and scheme are not specified, the defaults (given to
        constructor) are used.

        out should be a file-type object. Optionally, out can be given as the
        string 'str' and the parser will automatically return the output in a
        string."""

        string_output = False
        if out == 'str' or self.out == 'str' or \
           isinstance(self.out, StringIO):
            # XXX - I don't really like this state handling logic, but at this
            # point I don't want to make major changes, so adding the
            # isinstance() check is the simplest I can do to ensure correct
            # behavior.
            out_old = self.out
            self.out = StringIO()
            string_output = True
        elif out is not None:
            self.out = out

        # Fast return of the unmodified input for NoColor scheme
        # if scheme == 'NoColor':
        #     error = False
        #     self.out.write(raw)
        #     if string_output:
        #         return raw, error
        #     else:
        #         return None, error

        # Remove trailing whitespace and normalize tabs
        self.raw = raw.expandtabs().rstrip()

        # parse the source and write it
        error = False
        try:
            highlighted = self._pylight(self.raw)
        # TODO: figure out what kind of exception it can throw 
        except Exception :
            error = True

        self.out.write(highlighted)

        if string_output:
            output = self.out.getvalue()
            self.out = out_old
            return (output, error)
        return (None, error)

"""
Module containing filter functions that allow code to be highlighted
from within Jinja templates.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import re

from pygments import highlight as pygements_highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter

# Our own imports
from IPython.nbconvert.utils.lexers import IPythonLexer

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

MULTILINE_OUTPUTS = ['text', 'html', 'svg', 'latex', 'javascript', 'json']

# list of magic language extensions and their associated pygment lexers
magic_languages = {'%%R': 'r',
                   '%%bash': 'bash',
                   '%%octave': 'octave',
                   '%%perl': 'perl',
                   '%%ruby': 'ruby'
                   }

# build a RE to catch language extensions and choose an adequate
# pygments lexer
re_languages = "|".join(magic_languages.keys())
re_magic_language = re.compile(r'^\s*({})\s+'.format(re_languages),
                               re.MULTILINE)

#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------

__all__ = [
    'highlight2html',
    'highlight2latex'
]


def highlight2html(source, language='ipython'):
    """
    Return a syntax-highlighted version of the input source as html output.

    Parameters
    ----------
    source : str
        Source code to highlight the syntax of.
    language : str
        Language to highlight the syntax of.
    """

    return _pygment_highlight(source, HtmlFormatter(), language)


def highlight2latex(source, language='ipython'):
    """
    Return a syntax-highlighted version of the input source as latex output.

    Parameters
    ----------
    source : str
        Source code to highlight the syntax of.
    language : str
        Language to highlight the syntax of.
    """
    return _pygment_highlight(source, LatexFormatter(), language)


def which_magic_language(source):
    """
    When a cell uses another language through a magic extension,
    the other language is returned.
    If no language magic is detected, this function returns None.

    Parameters
    ----------
    source: str
        Source code of the cell to highlight
    """

    m = re_magic_language.search(source)

    if m:
        # By construction of the re, the matched language must be in the
        # language dictionnary
        assert(m.group(1) in magic_languages)
        return magic_languages[m.group(1)]
    else:
        return None


def _pygment_highlight(source, output_formatter, language='ipython'):
    """
    Return a syntax-highlighted version of the input source

    Parameters
    ----------
    source : str
        Source code to highlight the syntax of.
    output_formatter : Pygments formatter
    language : str
        Language to highlight the syntax of.
    """

    magic_language = which_magic_language(source)
    if magic_language:
        language = magic_language

    if language == 'ipython':
        lexer = IPythonLexer()
    else:
        lexer = get_lexer_by_name(language, stripall=True)

    return pygements_highlight(source, lexer, output_formatter)

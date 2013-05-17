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

from  pygments import highlight as pygements_highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter

# Our own imports
from nbconvert.utils.lexers import IPythonLexer

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

MULTILINE_OUTPUTS = ['text', 'html', 'svg', 'latex', 'javascript', 'json']

#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------

def highlight(source, language='ipython'):
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
    
    if language == 'ipython':
        lexer = IPythonLexer()
    else:
        lexer = get_lexer_by_name(language, stripall=True)

    return pygements_highlight(source, lexer, output_formatter) 

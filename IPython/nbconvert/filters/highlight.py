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

#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------

__all__ = [
    'highlight2html',
    'highlight2latex'
]

def highlight2html(source, language='ipython', metadata=None):
    """
    Return a syntax-highlighted version of the input source as html output.

    Parameters
    ----------
    source : str
        source of the cell to highlight.
    language : str
        Language to highlight the syntax of.
    metadata : NotebookNode cell metadata
        metadata of the cell to highlight.
    """

    return _pygment_highlight(source, HtmlFormatter(), language, metadata)


def highlight2latex(source, language='ipython', metadata=None):
    """
    Return a syntax-highlighted version of the input source as latex output.

    Parameters
    ----------
    source : str
        source of the cell to highlight.
    language : str
        Language to highlight the syntax of.
    metadata : NotebookNode cell metadata
        metadata of the cell to highlight.
    """
    return _pygment_highlight(source, LatexFormatter(), language, metadata)



def _pygment_highlight(source, output_formatter, language='ipython', metadata=None):
    """
    Return a syntax-highlighted version of the input source

    Parameters
    ----------
    source : str
        source of the cell to highlight.
    output_formatter : Pygments formatter
    language : str
        Language to highlight the syntax of.
    metadata : NotebookNode cell metadata
        metadata of the cell to highlight.
    """

    # If the cell uses a magic extension language,
    # use the magic language instead.
    if language == 'ipython' \
        and metadata \
        and 'magics_language' in metadata:

        language = metadata['magics_language']

    if language == 'ipython':
        lexer = IPythonLexer()
    else:
        lexer = get_lexer_by_name(language, stripall=True)

    return pygements_highlight(source, lexer, output_formatter)

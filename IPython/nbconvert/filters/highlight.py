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

from pygments import highlight as pygements_highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter


# Our own imports
from IPython.nbconvert.utils.lexers import IPythonLexer
from IPython.nbconvert.utils.base import NbConvertBase

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

MULTILINE_OUTPUTS = ['text', 'html', 'svg', 'latex', 'javascript', 'json']

#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------

__all__ = [
    'Highlight2Html',
    'Highlight2Latex'
]


class Highlight2Html(NbConvertBase):

    def __call__(self, source, language=None, metadata=None):
        """
        Return a syntax-highlighted version of the input source as html output.

        Parameters
        ----------
        source : str
            source of the cell to highlight
        language : str
            language to highlight the syntax of
        metadata : NotebookNode cell metadata
            metadata of the cell to highlight
        """
        if not language:
            language=self.default_language

        return _pygment_highlight(source, HtmlFormatter(), language, metadata)


class Highlight2Latex(NbConvertBase):

    def __call__(self, source, language=None, metadata=None, strip_verbatim=False):
        """
        Return a syntax-highlighted version of the input source as latex output.

        Parameters
        ----------
        source : str
            source of the cell to highlight
        language : str
            language to highlight the syntax of
        metadata : NotebookNode cell metadata
            metadata of the cell to highlight
        strip_verbatim : bool
            remove the Verbatim environment that pygments provides by default
        """
        if not language:
            language=self.default_language

        latex = _pygment_highlight(source, LatexFormatter(), language, metadata)
        if strip_verbatim:
            latex = latex.replace(r'\begin{Verbatim}[commandchars=\\\{\}]' + '\n', '')
            return latex.replace('\n\\end{Verbatim}\n', '')
        else:
            return latex



def _pygment_highlight(source, output_formatter, language='ipython', metadata=None):
    """
    Return a syntax-highlighted version of the input source

    Parameters
    ----------
    source : str
        source of the cell to highlight
    output_formatter : Pygments formatter
    language : str
        language to highlight the syntax of
    metadata : NotebookNode cell metadata
        metadata of the cell to highlight
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

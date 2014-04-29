"""
Module containing filter functions that allow code to be highlighted
from within Jinja templates.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

# pygments must not be imported at the module level
# because errors should be raised at runtime if it's actually needed,
# not import time, when it may not be needed.

from IPython.nbconvert.utils.base import NbConvertBase

MULTILINE_OUTPUTS = ['text', 'html', 'svg', 'latex', 'javascript', 'json']

__all__ = [
    'Highlight2HTML',
    'Highlight2Latex'
]

class Highlight2HTML(NbConvertBase):

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
        from pygments.formatters import HtmlFormatter
        if not language:
            language=self.default_language

        return _pygments_highlight(source if len(source) > 0 else ' ',
                                   # needed to help post processors:
                                   HtmlFormatter(cssclass=" highlight hl-"+language),
                                   language, metadata)


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
        from pygments.formatters import LatexFormatter
        if not language:
            language=self.default_language

        latex = _pygments_highlight(source, LatexFormatter(), language, metadata)
        if strip_verbatim:
            latex = latex.replace(r'\begin{Verbatim}[commandchars=\\\{\}]' + '\n', '')
            return latex.replace('\n\\end{Verbatim}\n', '')
        else:
            return latex



def _pygments_highlight(source, output_formatter, language='ipython', metadata=None):
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
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from IPython.nbconvert.utils.lexers import IPythonLexer

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

    return highlight(source, lexer, output_formatter)

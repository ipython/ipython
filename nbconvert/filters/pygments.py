# Our own imports
from utils.lexers import IPythonLexer

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------
_multiline_outputs = ['text', 'html', 'svg', 'latex', 'javascript', 'json']


#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------
def highlight(src, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source as html output.
    """
    from pygments.formatters import HtmlFormatter
    return pygment_highlight(src, HtmlFormatter(), lang)

def highlight2latex(src, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source as latex output.
    """
    from pygments.formatters import LatexFormatter
    return pygment_highlight(src, LatexFormatter(), lang)

def pygment_highlight(src, output_formatter, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source
    """
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name

    if lang == 'ipython':
        lexer = IPythonLexer()
    else:
        lexer = get_lexer_by_name(lang, stripall=True)

    return highlight(src, lexer, output_formatter) 

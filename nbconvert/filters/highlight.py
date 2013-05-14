
from  pygments import highlight as pygements_highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.formatters import LatexFormatter

# Our own imports
from nbconvert.utils.lexers import IPythonLexer

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
    
    return _pygment_highlight(src, HtmlFormatter(), lang)

def highlight2latex(src, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source as latex output.
    """
    return _pygment_highlight(src, LatexFormatter(), lang)

def _pygment_highlight(src, output_formatter, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source
    """
    if lang == 'ipython':
        lexer = IPythonLexer()
    else:
        lexer = get_lexer_by_name(lang, stripall=True)

    return pygements_highlight(src, lexer, output_formatter) 

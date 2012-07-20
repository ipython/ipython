#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from pygments.lexers import PythonLexer, BashLexer
from pygments.lexer import bygroups, using
from pygments.token import Keyword, Operator, Name, Text

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class IPythonLexer(PythonLexer):
    name = 'IPython'
    aliases = ['ip', 'ipython']
    filenames = ['*.ipy']
    tokens = PythonLexer.tokens.copy()
    tokens['root'] = [
        (r'(\%+)(\w+)\s+(\.*)(\n)', bygroups(Operator, Keyword, using(BashLexer), Text)),
        (r'(\%+)(\w+)\b', bygroups(Operator, Keyword)),
        (r'^(!)(.+)(\n)', bygroups(Operator, using(BashLexer), Text)),
    ] + tokens['root']

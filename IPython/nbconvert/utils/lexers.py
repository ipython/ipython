"""A custom pygments lexer for IPython code cells.

Informs The pygments highlighting library of the quirks of IPython's superset
of Python -- magic commands, !shell commands, etc.
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

# Third-party imports
from pygments.lexers import PythonLexer, BashLexer
from pygments.lexer import bygroups, using
from pygments.token import Keyword, Operator, Text

#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------

class IPythonLexer(PythonLexer):
    """
    Pygments Lexer for use with IPython code.  Inherits from 
    PythonLexer and adds information about IPython specific
    keywords (i.e. magic commands, shell commands, etc.)
    """
    
    #Basic properties
    name = 'IPython'
    aliases = ['ip', 'ipython']
    filenames = ['*.ipy']
    
    #Highlighting information
    tokens = PythonLexer.tokens.copy()
    tokens['root'] = [
        (r'(\%+)(\w+)\s+(\.*)(\n)', bygroups(Operator, Keyword,
                                             using(BashLexer), Text)),
        (r'(\%+)(\w+)\b', bygroups(Operator, Keyword)),
        (r'^(!)(.+)(\n)', bygroups(Operator, using(BashLexer), Text)),
        ] + tokens['root']

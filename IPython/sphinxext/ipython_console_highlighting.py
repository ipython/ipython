"""
reST directive for syntax-highlighting ipython interactive sessions.

"""

from sphinx import highlighting
from ..nbconvert.utils.lexers import IPyLexer

def setup(app):
    """Setup as a sphinx extension."""

    # This is only a lexer, so adding it below to pygments appears sufficient.
    # But if somebody knows what the right API usage should be to do that via
    # sphinx, by all means fix it here.  At least having this setup.py
    # suppresses the sphinx warning we'd get without it.
    pass

# Register the extension as a valid pygments lexerself.
# Alternatively, we could register the lexer with pygments instead. This would
# require using setuptools entrypoints: http://pygments.org/docs/plugins

ipy = IPyLexer(python3=False)
ipy3 = IPyLexer(python3=True)
ipy3.aliases = ['ipy3']

highlighting.lexers['ipy'] = ipy
highlighting.lexers['ipy3'] = ipy3

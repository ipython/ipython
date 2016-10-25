"""This tests that future compiler flags are passed to the embedded IPython."""
from __future__ import barry_as_FLUFL
from IPython import embed
embed(banner1='', header='check 1 <> 2 == True')
embed(banner1='', header='check 1 <> 2 cause SyntaxError', compile_flags=0)

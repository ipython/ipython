"""This tests that future compiler flags are passed to the embedded IPython."""
from IPython import embed
import __future__
embed(banner1='', header='check 1 <> 2 cause SyntaxError')
embed(banner1='', header='check 1 <> 2 == True',
      compile_flags=__future__.barry_as_FLUFL.compiler_flag)

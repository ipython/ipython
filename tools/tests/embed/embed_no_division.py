"""This tests that future compiler flags are passed to the embedded IPython."""
from IPython import embed
import __future__
embed(banner1='', header='check 1/2 == 0 in Python 2')
embed(banner1='', header='check 1/2 == 0.5 in Python 2',
      compile_flags=__future__.division.compiler_flag)

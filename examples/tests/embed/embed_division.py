"""This tests that future compiler flags are passed to the embedded IPython."""
from __future__ import division
from IPython import embed
embed(banner1='', header='check 1/2 == 0.5 in Python 2')
embed(banner1='', header='check 1/2 = 0 in Python 2', compile_flags=0)

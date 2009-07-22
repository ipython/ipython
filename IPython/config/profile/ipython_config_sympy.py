from ipython_config import *

EXECUTE.extend([
    'from __future__ import division'
    'from sympy import *'
    'x, y, z = symbols('xyz')'
    'k, m, n = symbols('kmn', integer=True)'
    'f, g, h = map(Function, 'fgh')'
])

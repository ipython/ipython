c = get_config()
app = c.IPythonApp

# This can be used at any point in a config file to load a sub config
# and merge it into the current one.
import os
load_subconfig(os.path.join('..','profile_default', 'ipython_config.py'))

lines = """
from __future__ import division
from sympy import *
x, y, z = symbols('xyz')
k, m, n = symbols('kmn', integer=True)
f, g, h = map(Function, 'fgh')
"""

# You have to make sure that attributes that are containers already
# exist before using them.  Simple assigning a new list will override
# all previous values.

if hasattr(app, 'exec_lines'):
    app.exec_lines.append(lines)
else:
    app.exec_lines = [lines]

# Load the sympy_printing extension to enable nice printing of sympy expr's.
if hasattr(app, 'extensions'):
    app.extensions.append('sympy_printing')
else:
    app.extensions = ['sympy_printing']


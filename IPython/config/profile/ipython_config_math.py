# This can be used at any point in a config file to load a sub config
# and merge it into the current one.
load_subconfig('ipython_config.py')

lines = """
import cmath
from math import *
"""

# You have to make sure that attributes that are containers already
# exist before using them.  Simple assigning a new list will override
# all previous values.
if hasattr(Global, 'exec_lines'):
    Global.exec_lines.append(lines)
else:
    Global.exec_lines = [lines]


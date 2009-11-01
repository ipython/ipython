c = get_config()

# This can be used at any point in a config file to load a sub config
# and merge it into the current one.
load_subconfig('ipython_config.py')

lines = """
from IPython.kernel.client import *
"""

# You have to make sure that attributes that are containers already
# exist before using them.  Simple assigning a new list will override
# all previous values.
if hasattr(c.Global, 'exec_lines'):
    c.Global.exec_lines.append(lines)
else:
    c.Global.exec_lines = [lines]

# Load the parallelmagic extension to enable %result, %px, %autopx magics.
if hasattr(c.Global, 'extensions'):
    c.Global.extensions.append('parallelmagic')
else:
    c.Global.extensions = ['parallelmagic']


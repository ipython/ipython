c = get_config()
app = c.IPythonApp

# This can be used at any point in a config file to load a sub config
# and merge it into the current one.
import os
load_subconfig(os.path.join('..','profile_default', 'ipython_config.py'))

lines = """
import matplotlib
%gui qt
matplotlib.use('qtagg')
matplotlib.interactive(True)
from matplotlib import pyplot as plt
from matplotlib.pyplot import *
"""

# You have to make sure that attributes that are containers already
# exist before using them.  Simple assigning a new list will override
# all previous values.
if hasattr(app, 'exec_lines'):
    app.exec_lines.append(lines)
else:
    app.exec_lines = [lines]
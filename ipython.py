#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IPython -- An enhanced Interactive Python

The actual ipython script to be installed with 'python setup.py install' is
in './scripts' directory. This file is here (ipython source root directory)
to facilitate non-root 'zero-installation' (just copy the source tree
somewhere and run ipython.py) and development. """

# Start by cleaning up sys.path: Python automatically inserts the script's
# base directory into sys.path, at the front.  This can lead to unpleasant
# surprises.
import sys
sys.path.pop(0)

import IPython

IPython.Shell.start().mainloop()

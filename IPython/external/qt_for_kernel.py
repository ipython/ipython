""" Import Qt in a manner suitable for an IPython kernel.
"""

import sys

# Older versions of matplotlib do not support PyQt4 v2 APIs or PySide, so we
# cannot go through the preferred mechanism.
matplotlib = sys.modules.get('matplotlib')
if matplotlib and matplotlib.__version__ <= '1.0.1':
    from PyQt4 import QtCore, QtGui
else:
    from IPython.external.qt import QtCore, QtGui

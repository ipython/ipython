""" Import Qt in a manner suitable for an IPython kernel.

This is the import used for the `gui=qt` or `pylab=qt` initialization.

Priority:

if matplotlib has been imported:
    # get here with pylab=qt
    if matplotlib doesn't support v2 (<= 1.0.1):
        use PyQt4 @v1
    else:
        ask matplotlib which Qt it's using
        if it said PyQt:
            use PyQt4 @v1
        elif it said PySide:
            use PySide

if matplotlib had nothing to say, or matplotlib not imported:
    # get here with gui=qt, or if matplotlib didn't tell us anything
    ask ETS' QT_API env variable

    if QT_API not set:
        # this is the *default* path - no information was given
        try:
            PyQt @v1
        except:
            fallback on PySide
    else:
        use PyQt @v2 or PySide, depending on QT_API
        because ETS doesn't work with v1.
"""

import os
import sys

matplotlib = sys.modules.get('matplotlib')
if matplotlib:
    # ask matplotlib first (get here with pylab=qt)
    if matplotlib.__version__ <= '1.0.1':
        # 1.0.1 doesn't support pyside or v2, so force PyQt @v1
        mod = 'PyQt4'
    else:
        # this rc option has been proposed, but is yet not in matplotlib master
        # as of writing.
        mod = matplotlib.rcParams.get('backend.qt4', None)
else:
    # get here with `gui=qt`
    mod = None

if mod is None:
    # matplotlib not imported or had nothing to say.
    # ask QT_API ETS variable
    QT_API = os.environ.get('QT_API', None)
    if QT_API is None:
        try:
            # default to unconfigured PyQt4
            from PyQt4 import QtCore, QtGui
        except ImportError:
            # fallback on PySide
            try:
                from PySide import QtCore, QtGui
            except ImportError:
                raise ImportError('Cannot import PySide or PyQt4')
    else:
        # QT_API specified, use PySide or PyQt+v2 API from external.qt
        # this means ETS is likely to be used, which requires v2
        from IPython.external.qt import QtCore, QtGui

elif mod.lower() == 'pyqt4':
    # import PyQt4 unconfigured
    from PyQt4 import QtCore, QtGui
elif mod.lower() == 'pyside':
    from PySide import QtCore, QtGui
else:
    raise ImportError("unhandled value for backend.qt4 from matplotlib: %r"%mod)
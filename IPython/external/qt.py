""" A Qt API selector that can be used to switch between PyQt and PySide.
"""

import os

# Use PyQt by default until PySide is stable.
qt_api = os.environ.get('QT_API', 'pyqt')

if qt_api == 'pyqt':
    # For PySide compatibility, use the new string API that automatically
    # converts QStrings to unicode Python strings.
    import sip
    sip.setapi('QString', 2)

    from PyQt4 import QtCore, QtGui, QtSvg

    # Alias PyQt-specific functions for PySide compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

else:
    from PySide import QtCore, QtGui, QtSvg

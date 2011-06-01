""" A Qt API selector that can be used to switch between PyQt and PySide.
"""

import os

# Available APIs.
QT_API_PYQT = 'pyqt'
QT_API_PYSIDE = 'pyside'

def prepare_pyqt4():
    # For PySide compatibility, use the new-style string API that automatically
    # converts QStrings to Unicode Python strings. Also, automatically unpack
    # QVariants to their underlying objects.
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)

# Select Qt binding, using the QT_API environment variable if available.
QT_API = os.environ.get('QT_API')
if QT_API is None:
    try:
        import PySide
        QT_API = QT_API_PYSIDE
    except ImportError:
        try:
            prepare_pyqt4()
            import PyQt4
            QT_API = QT_API_PYQT
        except ImportError:
            raise ImportError('Cannot import PySide or PyQt4')
        
elif QT_API == QT_API_PYQT:
    # Note: This must be called *before* PyQt4 is imported.
    prepare_pyqt4()

# Now peform the imports.
if QT_API == QT_API_PYQT:
    from PyQt4 import QtCore, QtGui, QtSvg

    # Alias PyQt-specific functions for PySide compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

elif QT_API == QT_API_PYSIDE:
    from PySide import QtCore, QtGui, QtSvg

else:
    raise RuntimeError('Invalid Qt API %r, valid values are: %r or %r' % 
                       (QT_API, QT_API_PYQT, QT_API_PYSIDE))

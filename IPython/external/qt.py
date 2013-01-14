""" A Qt API selector that can be used to switch between PyQt and PySide.

This uses the ETS 4.0 selection pattern of:
PySide first, PyQt with API v2. second.

Do not use this if you need PyQt with the old QString/QVariant API.
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
    pyside_found = False
    try:
        import PySide
        if PySide.__version__ < '1.0.3':
            # old PySide, fallback on PyQt
            raise ImportError
        # we can't import an incomplete pyside and pyqt4
        # this will cause a crash in sip (#1431)
        # check for complete presence before importing
        import imp
        imp.find_module("QtCore", PySide.__path__)
        imp.find_module("QtGui", PySide.__path__)
        imp.find_module("QtSvg", PySide.__path__)
        pyside_found = True
        from PySide import QtCore, QtGui, QtSvg
        QT_API = QT_API_PYSIDE
    except ImportError:
        try:
            prepare_pyqt4()
            import PyQt4
            from PyQt4 import QtCore, QtGui, QtSvg
            if pyside_found:
                print "WARNING: PySide installation incomplete and PyQt4 " \
                      "present.\nThis will likely crash, please install " \
                      "PySide completely, remove PySide or PyQt4 or set " \
                      "the QT_API environment variable to pyqt or pyside"
            if QtCore.PYQT_VERSION_STR < '4.7':
                # PyQt 4.6 has issues with null strings returning as None
                raise ImportError
            QT_API = QT_API_PYQT
        except ImportError:
            raise ImportError('Cannot import PySide >= 1.0.3 or PyQt4 >= 4.7')

elif QT_API == QT_API_PYQT:
    # Note: This must be called *before* PyQt4 is imported.
    prepare_pyqt4()

# Now peform the imports.
if QT_API == QT_API_PYQT:
    from PyQt4 import QtCore, QtGui, QtSvg
    if QtCore.PYQT_VERSION_STR < '4.7':
        raise ImportError("IPython requires PyQt4 >= 4.7, found %s"%QtCore.PYQT_VERSION_STR)

    # Alias PyQt-specific functions for PySide compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

elif QT_API == QT_API_PYSIDE:
    import PySide
    if PySide.__version__ < '1.0.3':
        raise ImportError("IPython requires PySide >= 1.0.3, found %s"%PySide.__version__)
    from PySide import QtCore, QtGui, QtSvg

else:
    raise RuntimeError('Invalid Qt API %r, valid values are: %r or %r' %
                       (QT_API, QT_API_PYQT, QT_API_PYSIDE))

""" Import Qt in a manner suitable for an IPython kernel.

This is the import used for the `gui=qt` or `pylab=qt` initialization.

Import Priority:

if matplotlib has been imported and doesn't support v2 (<= 1.0.1):
    use PyQt4 @v1

Next, ask ETS' QT_API env variable

if QT_API not set:
    ask matplotlib via rcParams['backend.qt4']
    if it said PyQt:
        use PyQt4 @v1
    elif it said PySide:
        use PySide

    else: (matplotlib said nothing)
        # this is the default path - nobody told us anything
        try:
            PyQt @v1
        except:
            fallback on PySide
else:
    use PyQt @v2 or PySide, depending on QT_API
    because ETS doesn't work with PyQt @v1.

"""

import os
import sys

from IPython.utils.warn import warn

matplotlib = sys.modules.get('matplotlib')
if matplotlib and matplotlib.__version__ <= '1.0.1':
    # 1.0.1 doesn't support pyside or v2, so stick with PyQt @v1,
    # and ignore everything else
    from PyQt4 import QtCore, QtGui
else:
    # ask QT_API ETS variable *first*
    QT_API = os.environ.get('QT_API', None)
    if QT_API is None:
        # QT_API not set, ask matplotlib if it was imported (e.g. `pylab=qt`)
        if matplotlib:
            mpqt = matplotlib.rcParams.get('backend.qt4', None)
        else:
            mpqt = None
        if mpqt is None:
            # matplotlib not imported or had nothing to say.
            try:
                # default to unconfigured PyQt4
                from PyQt4 import QtCore, QtGui
            except ImportError:
                # fallback on PySide
                try:
                    from PySide import QtCore, QtGui
                except ImportError:
                    raise ImportError('Cannot import PySide or PyQt4')
        elif mpqt.lower() == 'pyqt4':
            # import PyQt4 unconfigured
            from PyQt4 import QtCore, QtGui
        elif mpqt.lower() == 'pyside':
            from PySide import QtCore, QtGui
        else:
            raise ImportError("unhandled value for backend.qt4 from matplotlib: %r"%mpqt)
    else:
        # QT_API specified, use PySide or PyQt+v2 API from external.qt
        # this means ETS is likely to be used, which requires v2
        try:
            from IPython.external.qt import QtCore, QtGui
        except ValueError as e:
            if 'API' in str(e):
                # PyQt4 already imported, and APIv2 couldn't be set
                # Give more meaningful message, and warn instead of raising
                warn("""
    Assigning the ETS variable `QT_API=pyqt` implies PyQt's v2 API for
    QString and QVariant, but PyQt has already been imported
    with v1 APIs.  You should unset QT_API to work with PyQt4
    in its default mode.
""")
                # allow it to still work
                from PyQt4 import QtCore, QtGui
            else:
                raise


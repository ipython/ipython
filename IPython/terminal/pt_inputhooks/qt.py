import sys
import os
from IPython.external.qt_for_kernel import QtCore, QtGui
from IPython import get_ipython

# If we create a QApplication, keep a reference to it so that it doesn't get
# garbage collected.
_appref = None
_already_warned = False


def _reclaim_excepthook():
    shell = get_ipython()
    if shell is not None:
        sys.excepthook = shell.excepthook


def inputhook(context):
    global _appref
    app = QtCore.QCoreApplication.instance()
    if not app:
        if sys.platform == 'linux':
            if not os.environ.get('DISPLAY') \
                    and not os.environ.get('WAYLAND_DISPLAY'):
                import warnings
                global _already_warned
                if not _already_warned:
                    _already_warned = True
                    warnings.warn(
                        'The DISPLAY or WAYLAND_DISPLAY environment variable is '
                        'not set or empty and Qt5 requires this environment '
                        'variable. Deactivate Qt5 code.'
                    )
                return
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        _appref = app = QtGui.QApplication([" "])

        # "reclaim" IPython sys.excepthook after event loop starts
        # without this, it defaults back to BaseIPythonApplication.excepthook
        # and exceptions in the Qt event loop are rendered without traceback
        # formatting and look like "bug in IPython".
        QtCore.QTimer.singleShot(0, _reclaim_excepthook)

    event_loop = QtCore.QEventLoop(app)

    if sys.platform == 'win32':
        # The QSocketNotifier method doesn't appear to work on Windows.
        # Use polling instead.
        timer = QtCore.QTimer()
        timer.timeout.connect(event_loop.quit)
        while not context.input_is_ready():
            timer.start(50)  # 50 ms
            event_loop.exec_()
            timer.stop()
    else:
        # On POSIX platforms, we can use a file descriptor to quit the event
        # loop when there is input ready to read.
        notifier = QtCore.QSocketNotifier(context.fileno(),
                                          QtCore.QSocketNotifier.Read)
        try:
            # connect the callback we care about before we turn it on
            notifier.activated.connect(lambda: event_loop.exit())
            notifier.setEnabled(True)
            # only start the event loop we are not already flipped
            if not context.input_is_ready():
                event_loop.exec_()
        finally:
            notifier.setEnabled(False)

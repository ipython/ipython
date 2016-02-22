from IPython.external.qt_for_kernel import QtCore, QtGui

def inputhook(context):
    app = QtCore.QCoreApplication.instance()
    if not app:
        return
    event_loop = QtCore.QEventLoop(app)
    notifier = QtCore.QSocketNotifier(context.fileno(), QtCore.QSocketNotifier.Read)
    notifier.setEnabled(True)
    notifier.activated.connect(event_loop.exit)
    event_loop.exec_()

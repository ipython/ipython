from IPython.external.qt_for_kernel import QtCore, QtGui

import threading
import time

import select
watched_fd = set({})

def _stop_qt_ev_on_redable(fd, ev):
    """QtNotifier seem to not work on windows, we manually watch the file"""
    while True:
        ready, _, _ = select.select((fd,), (), (), .1)
        time.sleep(0.05)
        if ready:
            watched_fd.remove(fd)
            ev.exit()
            break


def inputhook(context):
    app = QtCore.QCoreApplication.instance()
    if not app:
        return
    event_loop = QtCore.QEventLoop(app)
    fd = context.fileno()

    if sys.platform == 'win32':
        if fd and (fd not in watched_fd):
            watched_fd.add(fd)
            t = threading.Thread(target=_stop_qt_ev_on_redable, args=(fd, event_loop))
            t.start()
    else:
        notifier = QtCore.QSocketNotifier(fd, QtCore.QSocketNotifier.Read)
        notifier.setEnabled(True)
        notifier.activated.connect(event_loop.exit)
        event_loop.exec_()

    


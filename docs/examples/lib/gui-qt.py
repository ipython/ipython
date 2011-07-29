#!/usr/bin/env python
"""Simple Qt4 example to manually test event loop integration.

This is meant to run tests manually in ipython as:

In [5]: %gui qt

In [6]: %run gui-qt.py

Ref: Modified from http://zetcode.com/tutorials/pyqt4/firstprograms/
"""

import sys
from PyQt4 import QtGui, QtCore

class SimpleWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(300, 300, 200, 80)
        self.setWindowTitle('Hello World')

        quit = QtGui.QPushButton('Close', self)
        quit.setGeometry(10, 10, 60, 35)

        self.connect(quit, QtCore.SIGNAL('clicked()'),
                     self, QtCore.SLOT('close()'))

if __name__ == '__main__':
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtGui.QApplication([])

    sw = SimpleWindow()
    sw.show()

    try:
        from IPython.lib.guisupport import start_event_loop_qt4
        start_event_loop_qt4(app)
    except ImportError:
        app.exec_()

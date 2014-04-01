#!/usr/bin/env python
"""Example integrating an IPython kernel into a GUI App.

This trivial GUI application internally starts an IPython kernel, to which Qt
consoles can be connected either by the user at the command line or started
from the GUI itself, via a button.  The GUI can also manipulate one variable in
the kernel's namespace, and print the namespace to the console.

Play with it by running the script and then opening one or more consoles, and
pushing the 'Counter++' and 'Namespace' buttons.

Upon exit, it should automatically close all consoles opened from the GUI.

Consoles attached separately from a terminal will not be terminated, though
they will notice that their kernel died.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from PyQt4 import Qt

from internal_ipkernel import InternalIPKernel

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------
class SimpleWindow(Qt.QWidget, InternalIPKernel):

    def __init__(self, app):
        Qt.QWidget.__init__(self)
        self.app = app
        self.add_widgets()
        self.init_ipkernel('qt')

    def add_widgets(self):
        self.setGeometry(300, 300, 400, 70)
        self.setWindowTitle('IPython in your app')

        # Add simple buttons:
        console = Qt.QPushButton('Qt Console', self)
        console.setGeometry(10, 10, 100, 35)
        self.connect(console, Qt.SIGNAL('clicked()'), self.new_qt_console)

        namespace = Qt.QPushButton('Namespace', self)
        namespace.setGeometry(120, 10, 100, 35)
        self.connect(namespace, Qt.SIGNAL('clicked()'), self.print_namespace)

        count = Qt.QPushButton('Count++', self)
        count.setGeometry(230, 10, 80, 35)
        self.connect(count, Qt.SIGNAL('clicked()'), self.count)

        # Quit and cleanup
        quit = Qt.QPushButton('Quit', self)
        quit.setGeometry(320, 10, 60, 35)
        self.connect(quit, Qt.SIGNAL('clicked()'), Qt.qApp, Qt.SLOT('quit()'))

        self.app.connect(self.app, Qt.SIGNAL("lastWindowClosed()"),
                         self.app, Qt.SLOT("quit()"))

        self.app.aboutToQuit.connect(self.cleanup_consoles)

#-----------------------------------------------------------------------------
# Main script
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    app = Qt.QApplication([]) 
    # Create our window
    win = SimpleWindow(app)
    win.show()
    
    # Very important, IPython-specific step: this gets GUI event loop
    # integration going, and it replaces calling app.exec_()
    win.ipkernel.start()

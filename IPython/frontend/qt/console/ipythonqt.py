""" A minimal application using the Qt console-style IPython frontend.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Systemm library imports
from PyQt4 import QtGui

# Local imports
from IPython.external.argparse import ArgumentParser
from IPython.frontend.qt.console.frontend_widget import FrontendWidget
from IPython.frontend.qt.console.ipython_widget import IPythonWidget
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.kernelmanager import QtKernelManager

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

LOCALHOST = '127.0.0.1'

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class MainWindow(QtGui.QMainWindow):

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, app, frontend, existing=False):
        """ Create a MainWindow for the specified FrontendWidget.
        
        If existing is True, then this Window does not own the Kernel.
        """
        super(MainWindow, self).__init__()
        self._app = app
        self._frontend = frontend
        self._existing = existing
        self._frontend.exit_requested.connect(self.close)
        self.setCentralWidget(frontend)
    
    #---------------------------------------------------------------------------
    # QWidget interface
    #---------------------------------------------------------------------------
    
    def closeEvent(self, event):
        """ Reimplemented to prompt the user and close the kernel cleanly.
        """
        kernel_manager = self._frontend.kernel_manager
        if kernel_manager and kernel_manager.channels_running:
            title = self.window().windowTitle()
            reply = QtGui.QMessageBox.question(self, title,
                "Close just this console, or shutdown the kernel and close "+
                "all windows attached to it?", 
                'Cancel', 'Close Console', 'Close All')
            if reply == 2:
                kernel_manager.shutdown_kernel()
                #kernel_manager.stop_channels()
                event.accept()
            elif reply == 1:
                if self._existing:
                    # I don't have the Kernel, I can shutdown
                    event.accept()
                else:
                    # only destroy the Window, save the Kernel
                    self._app.setQuitOnLastWindowClosed(False)
                    self.deleteLater()
                    event.ignore()
            else:
                event.ignore()

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def main():
    """ Entry point for application.
    """
    # Parse command line arguments.
    parser = ArgumentParser()
    kgroup = parser.add_argument_group('kernel options')
    kgroup.add_argument('-e', '--existing', action='store_true',
                        help='connect to an existing kernel')
    kgroup.add_argument('--ip', type=str, default=LOCALHOST,
                        help='set the kernel\'s IP address [default localhost]')
    kgroup.add_argument('--xreq', type=int, metavar='PORT', default=0,
                        help='set the XREQ channel port [default random]')
    kgroup.add_argument('--sub', type=int, metavar='PORT', default=0,
                        help='set the SUB channel port [default random]')
    kgroup.add_argument('--rep', type=int, metavar='PORT', default=0,
                        help='set the REP channel port [default random]')
    kgroup.add_argument('--hb', type=int, metavar='PORT', default=0,
                        help='set the heartbeat port [default: random]')

    egroup = kgroup.add_mutually_exclusive_group()
    egroup.add_argument('--pure', action='store_true', help = \
                        'use a pure Python kernel instead of an IPython kernel')
    egroup.add_argument('--pylab', type=str, metavar='GUI', nargs='?', 
                       const='auto', help = \
        "Pre-load matplotlib and numpy for interactive use. If GUI is not \
         given, the GUI backend is matplotlib's, otherwise use one of: \
         ['tk', 'gtk', 'qt', 'wx', 'inline'].")

    wgroup = parser.add_argument_group('widget options')
    wgroup.add_argument('--paging', type=str, default='inside',
                        choices = ['inside', 'hsplit', 'vsplit', 'none'],
                        help='set the paging style [default inside]')
    wgroup.add_argument('--rich', action='store_true',
                        help='enable rich text support')
    wgroup.add_argument('--gui-completion', action='store_true',
                        help='use a GUI widget for tab completion')

    args = parser.parse_args()

    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager and start a kernel.
    kernel_manager = QtKernelManager(xreq_address=(args.ip, args.xreq),
                                     sub_address=(args.ip, args.sub),
                                     rep_address=(args.ip, args.rep),
                                     hb_address=(args.ip, args.hb))
    if args.ip == LOCALHOST and not args.existing:
        if args.pure:
            kernel_manager.start_kernel(ipython=False)
        elif args.pylab:
            kernel_manager.start_kernel(pylab=args.pylab)
        else:
            kernel_manager.start_kernel()
    kernel_manager.start_channels()

    # Create the widget.
    app = QtGui.QApplication([])
    if args.pure:
        kind = 'rich' if args.rich else 'plain'
        widget = FrontendWidget(kind=kind, paging=args.paging)
    elif args.rich or args.pylab:
        widget = RichIPythonWidget(paging=args.paging)
    else:
        widget = IPythonWidget(paging=args.paging)
    widget.gui_completion = args.gui_completion
    widget.kernel_manager = kernel_manager

    # Create the main window.
    window = MainWindow(app, widget, args.existing)
    window.setWindowTitle('Python' if args.pure else 'IPython')
    window.show()

    # Start the application main loop.
    app.exec_()


if __name__ == '__main__':
    main()

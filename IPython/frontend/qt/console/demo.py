""" A demo of the Qt console-style IPython frontend.
"""

# Systemm library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.external.argparse import ArgumentParser
from IPython.frontend.qt.kernelmanager import QtKernelManager


def main():
    """ Entry point for demo.
    """
    # Parse command line arguments.
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--pure', action='store_true', help = \
                       'use a pure Python kernel instead of an IPython kernel')
    group.add_argument('--pylab', action='store_true',
                        help='use a kernel with PyLab enabled')
    parser.add_argument('--rich', action='store_true',
                        help='use a rich text frontend')
    namespace = parser.parse_args()
    
    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager and start a kernel.
    kernel_manager = QtKernelManager()
    if namespace.pure:
        kernel_manager.start_kernel(ipython=False)
    elif namespace.pylab:
        if namespace.rich:
            kernel_manager.start_kernel(pylab='payload-svg')
        else:
            kernel_manager.start_kernel(pylab='qt4')
    else:
        kernel_manager.start_kernel()
    kernel_manager.start_channels()

    # Launch the application.
    app = QtGui.QApplication([])
    if namespace.pure:
        from frontend_widget import FrontendWidget
        kind = 'rich' if namespace.rich else 'plain'
        widget = FrontendWidget(kind=kind)
    else:
        if namespace.rich:
            from rich_ipython_widget import RichIPythonWidget
            widget = RichIPythonWidget()
        else:
            from ipython_widget import IPythonWidget
            widget = IPythonWidget()
    widget.kernel_manager = kernel_manager
    widget.setWindowTitle('Python')
    widget.show()
    app.exec_()


if __name__ == '__main__':
    main()

#!/usr/bin/env python

""" A minimal application using the Qt console-style IPython frontend.
"""

# Systemm library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.external.argparse import ArgumentParser
from IPython.frontend.qt.console.frontend_widget import FrontendWidget
from IPython.frontend.qt.console.ipython_widget import IPythonWidget
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.kernelmanager import QtKernelManager

# Constants
LOCALHOST = '127.0.0.1'


def main():
    """ Entry point for application.
    """
    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument('-r', '--rich', action='store_true',
                        help='use a rich text frontend')
    parser.add_argument('-t', '--tab-simple', action='store_true',
                        help='do tab completion ala a Unix terminal')

    parser.add_argument('--existing', action='store_true',
                        help='connect to an existing kernel')
    parser.add_argument('--ip', type=str, default=LOCALHOST,
                        help='set the kernel\'s IP address [default localhost]')
    parser.add_argument('--xreq', type=int, metavar='PORT', default=0,
                        help='set the XREQ channel port [default random]')
    parser.add_argument('--sub', type=int, metavar='PORT', default=0,
                        help='set the SUB channel port [default random]')
    parser.add_argument('--rep', type=int, metavar='PORT', default=0,
                        help='set the REP channel port [default random]')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--pure', action='store_true', help = \
                       'use a pure Python kernel instead of an IPython kernel')
    group.add_argument('--pylab', action='store_true',
                        help='use a kernel with PyLab enabled')
    
    args = parser.parse_args()
    
    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager and start a kernel.
    kernel_manager = QtKernelManager(xreq_address=(args.ip, args.xreq),
                                     sub_address=(args.ip, args.sub),
                                     rep_address=(args.ip, args.rep))
    if args.ip == LOCALHOST and not args.existing:
        if args.pure:
            kernel_manager.start_kernel(ipython=False)
        elif args.pylab:
            if args.rich:
                kernel_manager.start_kernel(pylab='payload-svg')
            else:
                kernel_manager.start_kernel(pylab='qt4')
        else:
            kernel_manager.start_kernel()
    kernel_manager.start_channels()

    # Create the widget.
    app = QtGui.QApplication([])
    if args.pure:
        kind = 'rich' if args.rich else 'plain'
        widget = FrontendWidget(kind=kind)
    elif args.rich:
        widget = RichIPythonWidget()
    else:
        widget = IPythonWidget()
    widget.gui_completion = not args.tab_simple
    widget.kernel_manager = kernel_manager
    widget.setWindowTitle('Python' if args.pure else 'IPython')
    widget.show()

    # FIXME: This is a hack: set colors to lightbg by default in qt terminal
    # unconditionally, regardless of user settings in config files.
    widget.execute("%colors lightbg", hidden=True)

    # Start the application main loop.
    app.exec_()


if __name__ == '__main__':
    main()

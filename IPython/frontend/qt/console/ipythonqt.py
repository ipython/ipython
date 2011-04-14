""" A minimal application using the Qt console-style IPython frontend.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Systemm library imports
from IPython.external.qt import QtGui
from pygments.styles import get_all_styles

# Local imports
from IPython.external.argparse import ArgumentParser
from IPython.frontend.qt.console.frontend_widget import FrontendWidget
from IPython.frontend.qt.console.ipython_widget import IPythonWidget
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.console import styles
from IPython.frontend.qt.kernelmanager import QtKernelManager

#-----------------------------------------------------------------------------
# Network Constants
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class MainWindow(QtGui.QMainWindow):

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, app, frontend, existing=False, may_close=True):
        """ Create a MainWindow for the specified FrontendWidget.
        
        The app is passed as an argument to allow for different
        closing behavior depending on whether we are the Kernel's parent.
        
        If existing is True, then this Console does not own the Kernel.
        
        If may_close is True, then this Console is permitted to close the kernel
        """
        super(MainWindow, self).__init__()
        self._app = app
        self._frontend = frontend
        self._existing = existing
        if existing:
            self._may_close = may_close
        else:
            self._may_close = True
        self._frontend.exit_requested.connect(self.close)
        self.setCentralWidget(frontend)
    
    #---------------------------------------------------------------------------
    # QWidget interface
    #---------------------------------------------------------------------------
    
    def closeEvent(self, event):
        """ Close the window and the kernel (if necessary).
        
        This will prompt the user if they are finished with the kernel, and if
        so, closes the kernel cleanly. Alternatively, if the exit magic is used,
        it closes without prompt.
        """
        keepkernel = None #Use the prompt by default
        if hasattr(self._frontend,'_keep_kernel_on_exit'): #set by exit magic
            keepkernel = self._frontend._keep_kernel_on_exit
        
        kernel_manager = self._frontend.kernel_manager
        
        if keepkernel is None: #show prompt
            if kernel_manager and kernel_manager.channels_running:
                title = self.window().windowTitle()
                cancel = QtGui.QMessageBox.Cancel
                okay = QtGui.QMessageBox.Ok
                if self._may_close:
                    msg = "You are closing this Console window."
                    info = "Would you like to quit the Kernel and all attached Consoles as well?"
                    justthis = QtGui.QPushButton("&No, just this Console", self)
                    justthis.setShortcut('N')
                    closeall = QtGui.QPushButton("&Yes, quit everything", self)
                    closeall.setShortcut('Y')
                    box = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                            title, msg)
                    box.setInformativeText(info)
                    box.addButton(cancel)
                    box.addButton(justthis, QtGui.QMessageBox.NoRole)
                    box.addButton(closeall, QtGui.QMessageBox.YesRole)
                    box.setDefaultButton(closeall)
                    box.setEscapeButton(cancel)
                    reply = box.exec_()
                    if reply == 1: # close All
                        kernel_manager.shutdown_kernel()
                        #kernel_manager.stop_channels()
                        event.accept()
                    elif reply == 0: # close Console
                        if not self._existing:
                            # Have kernel: don't quit, just close the window
                            self._app.setQuitOnLastWindowClosed(False)
                            self.deleteLater()
                        event.accept()
                    else:
                        event.ignore()
                else:
                    reply = QtGui.QMessageBox.question(self, title,
                        "Are you sure you want to close this Console?"+
                        "\nThe Kernel and other Consoles will remain active.",
                        okay|cancel,
                        defaultButton=okay
                        )
                    if reply == okay:
                        event.accept()
                    else:
                        event.ignore()
        elif keepkernel: #close console but leave kernel running (no prompt)
            if kernel_manager and kernel_manager.channels_running:
                if not self._existing:
                    # I have the kernel: don't quit, just close the window
                    self._app.setQuitOnLastWindowClosed(False)
                event.accept()
        else: #close console and kernel (no prompt)
            if kernel_manager and kernel_manager.channels_running:
                kernel_manager.shutdown_kernel()
                event.accept()

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
                        help=\
            "set the kernel\'s IP address [default localhost].\
            If the IP address is something other than localhost, then \
            Consoles on other machines will be able to connect\
            to the Kernel, so be careful!")
    kgroup.add_argument('--xreq', type=int, metavar='PORT', default=0,
                        help='set the XREQ channel port [default random]')
    kgroup.add_argument('--sub', type=int, metavar='PORT', default=0,
                        help='set the SUB channel port [default random]')
    kgroup.add_argument('--rep', type=int, metavar='PORT', default=0,
                        help='set the REP channel port [default random]')
    kgroup.add_argument('--hb', type=int, metavar='PORT', default=0,
                        help='set the heartbeat port [default random]')

    egroup = kgroup.add_mutually_exclusive_group()
    egroup.add_argument('--pure', action='store_true', help = \
                        'use a pure Python kernel instead of an IPython kernel')
    egroup.add_argument('--pylab', type=str, metavar='GUI', nargs='?',
                       const='auto', help = \
        "Pre-load matplotlib and numpy for interactive use. If GUI is not \
         given, the GUI backend is matplotlib's, otherwise use one of: \
         ['tk', 'gtk', 'qt', 'wx', 'inline_svg', 'inline_png'].")

    wgroup = parser.add_argument_group('widget options')
    wgroup.add_argument('--paging', type=str, default='inside',
                        choices = ['inside', 'hsplit', 'vsplit', 'none'],
                        help='set the paging style [default inside]')
    wgroup.add_argument('--rich', action='store_true',
                        help='enable rich text support')
    wgroup.add_argument('--gui-completion', action='store_true',
                        help='use a GUI widget for tab completion')
    wgroup.add_argument('--style', type=str,
                        choices = list(get_all_styles()),
                        help='specify a pygments style for by name.')
    wgroup.add_argument('--stylesheet', type=str,
                        help="path to a custom CSS stylesheet.")
    wgroup.add_argument('--colors', type=str,
                        help="Set the color scheme (LightBG,Linux,NoColor). This is guessed\
                        based on the pygments style if not set.")

    args = parser.parse_args()

    # parse the colors arg down to current known labels
    if args.colors:
        colors=args.colors.lower()
        if colors in ('lightbg', 'light'):
            colors='lightbg'
        elif colors in ('dark', 'linux'):
            colors='linux'
        else:
            colors='nocolor'
    elif args.style:
        if args.style=='bw':
            colors='nocolor'
        elif styles.dark_style(args.style):
            colors='linux'
        else:
            colors='lightbg'
    else:
        colors=None

    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager and start a kernel.
    kernel_manager = QtKernelManager(xreq_address=(args.ip, args.xreq),
                                     sub_address=(args.ip, args.sub),
                                     rep_address=(args.ip, args.rep),
                                     hb_address=(args.ip, args.hb))
    if not args.existing:
        # if not args.ip in LOCAL_IPS+ALL_ALIAS:
        #     raise ValueError("Must bind a local ip, such as: %s"%LOCAL_IPS)

        kwargs = dict(ip=args.ip)
        if args.pure:
            kwargs['ipython']=False
        else:
            kwargs['colors']=colors
            if args.pylab:
                kwargs['pylab']=args.pylab

        kernel_manager.start_kernel(**kwargs)
    kernel_manager.start_channels()

    local_kernel = (not args.existing) or args.ip in LOCAL_IPS
    # Create the widget.
    app = QtGui.QApplication([])
    if args.pure:
        kind = 'rich' if args.rich else 'plain'
        widget = FrontendWidget(kind=kind, paging=args.paging, local_kernel=local_kernel)
    elif args.rich or args.pylab:
        widget = RichIPythonWidget(paging=args.paging, local_kernel=local_kernel)
    else:
        widget = IPythonWidget(paging=args.paging, local_kernel=local_kernel)
    widget.gui_completion = args.gui_completion
    widget.kernel_manager = kernel_manager

    # configure the style:
    if not args.pure: # only IPythonWidget supports styles
        if args.style:
            widget.syntax_style = args.style
            widget.style_sheet = styles.sheet_from_template(args.style, colors)
            widget._syntax_style_changed()
            widget._style_sheet_changed()
        elif colors:
            # use a default style
            widget.set_default_style(colors=colors)
        else:
            # this is redundant for now, but allows the widget's
            # defaults to change
            widget.set_default_style()

        if args.stylesheet:
            # we got an expicit stylesheet
            if os.path.isfile(args.stylesheet):
                with open(args.stylesheet) as f:
                    sheet = f.read()
                widget.style_sheet = sheet
                widget._style_sheet_changed()
            else:
                raise IOError("Stylesheet %r not found."%args.stylesheet)

    # Create the main window.
    window = MainWindow(app, widget, args.existing, may_close=local_kernel)
    window.setWindowTitle('Python' if args.pure else 'IPython')
    window.show()

    # Start the application main loop.
    app.exec_()


if __name__ == '__main__':
    main()

""" A minimal application using the Qt console-style IPython frontend.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# stdlib imports
import os
import signal
import sys

# System library imports
from IPython.external.qt import QtGui
from pygments.styles import get_all_styles

# Local imports
from IPython.core.newapplication import ProfileDir, BaseIPythonApplication
from IPython.frontend.qt.console.frontend_widget import FrontendWidget
from IPython.frontend.qt.console.ipython_widget import IPythonWidget
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.console import styles
from IPython.frontend.qt.kernelmanager import QtKernelManager
from IPython.utils.traitlets import (
    Dict, List, Unicode, Int, CaselessStrEnum, Bool, Any
)
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
    IPKernelApp
)
from IPython.zmq.zmqshell import ZMQInteractiveShell


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
# Aliases and Flags
#-----------------------------------------------------------------------------

flags = dict(ipkernel_flags)

flags.update({
    'existing' : ({'IPythonQtConsoleApp' : {'existing' : True}},
            "Connect to an existing kernel."),
    'pure' : ({'IPythonQtConsoleApp' : {'pure' : True}},
            "Use a pure Python kernel instead of an IPython kernel."),
    'plain' : ({'ConsoleWidget' : {'kind' : 'plain'}},
            "Disable rich text support."),
    'gui-completion' : ({'FrontendWidget' : {'gui_completion' : True}},
            "use a GUI widget for tab completion"),
})

qt_flags = ['existing', 'pure', 'plain', 'gui-completion']

aliases = dict(ipkernel_aliases)

aliases.update(dict(
    hb = 'IPythonQtConsoleApp.hb_port',
    shell = 'IPythonQtConsoleApp.shell_port',
    iopub = 'IPythonQtConsoleApp.iopub_port',
    stdin = 'IPythonQtConsoleApp.stdin_port',
    ip = 'IPythonQtConsoleApp.ip',

    plain = 'IPythonQtConsoleApp.plain',
    pure = 'IPythonQtConsoleApp.pure',
    gui_completion = 'FrontendWidget.gui_completion',
    style = 'IPythonWidget.syntax_style',
    stylesheet = 'IPythonQtConsoleApp.stylesheet',
    colors = 'ZMQInteractiveShell.colors',

    editor = 'IPythonWidget.editor',
    pi = 'IPythonWidget.in_prompt',
    po = 'IPythonWidget.out_prompt',
    si = 'IPythonWidget.input_sep',
    so = 'IPythonWidget.output_sep',
    so2 = 'IPythonWidget.output_sep2',
))

#-----------------------------------------------------------------------------
# IPythonQtConsole
#-----------------------------------------------------------------------------

class IPythonQtConsoleApp(BaseIPythonApplication):
    name = 'ipython-qtconsole'
    default_config_file_name='ipython_config.py'
    classes = [IPKernelApp, IPythonWidget, ZMQInteractiveShell, ProfileDir]
    flags = Dict(flags)
    aliases = Dict(aliases)

    kernel_argv = List(Unicode)

    # connection info:
    ip = Unicode(LOCALHOST, config=True,
        help="""Set the kernel\'s IP address [default localhost].
        If the IP address is something other than localhost, then
        Consoles on other machines will be able to connect
        to the Kernel, so be careful!"""
    )
    hb_port = Int(0, config=True,
        help="set the heartbeat port [default: random]")
    shell_port = Int(0, config=True,
        help="set the shell (XREP) port [default: random]")
    iopub_port = Int(0, config=True,
        help="set the iopub (PUB) port [default: random]")
    stdin_port = Int(0, config=True,
        help="set the stdin (XREQ) port [default: random]")

    existing = Bool(False, config=True,
        help="Whether to connect to an already running Kernel.")

    stylesheet = Unicode('', config=True,
        help="path to a custom CSS stylesheet")

    pure = Bool(False, config=True,
        help="Use a pure Python kernel instead of an IPython kernel.")
    plain = Bool(False, config=True,
        help="Use a plaintext widget instead of rich text (plain can't print/save).")

    def _pure_changed(self, name, old, new):
        kind = 'plain' if self.plain else 'rich'
        self.config.ConsoleWidget.kind = kind
        if self.pure:
            self.widget_factory = FrontendWidget
        elif self.plain:
            self.widget_factory = IPythonWidget
        else:
            self.widget_factory = RichIPythonWidget

    _plain_changed = _pure_changed

    # the factory for creating a widget
    widget_factory = Any(RichIPythonWidget)

    def parse_command_line(self, argv=None):
        super(IPythonQtConsoleApp, self).parse_command_line(argv)
        if argv is None:
            argv = sys.argv[1:]

        self.kernel_argv = list(argv) # copy

        # scrub frontend-specific flags
        for a in argv:
            if a.startswith('--') and a[2:] in qt_flags:
                self.kernel_argv.remove(a)

    def init_kernel_manager(self):
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Create a KernelManager and start a kernel.
        self.kernel_manager = QtKernelManager(
                                shell_address=(self.ip, self.shell_port),
                                sub_address=(self.ip, self.iopub_port),
                                stdin_address=(self.ip, self.stdin_port),
                                hb_address=(self.ip, self.hb_port)
        )
        # start the kernel
        if not self.existing:
            kwargs = dict(ip=self.ip, ipython=not self.pure)
            kwargs['extra_arguments'] = self.kernel_argv
            self.kernel_manager.start_kernel(**kwargs)
        self.kernel_manager.start_channels()


    def init_qt_elements(self):
        # Create the widget.
        self.app = QtGui.QApplication([])
        local_kernel = (not self.existing) or self.ip in LOCAL_IPS
        self.widget = self.widget_factory(config=self.config,
                                        local_kernel=local_kernel)
        self.widget.kernel_manager = self.kernel_manager
        self.window = MainWindow(self.app, self.widget, self.existing,
                                may_close=local_kernel)
        self.window.setWindowTitle('Python' if self.pure else 'IPython')

    def init_colors(self):
        """Configure the coloring of the widget"""
        # Note: This will be dramatically simplified when colors
        # are removed from the backend.

        if self.pure:
            # only IPythonWidget supports styling
            return

        # parse the colors arg down to current known labels
        try:
            colors = self.config.ZMQInteractiveShell.colors
        except AttributeError:
            colors = None
        try:
            style = self.config.IPythonWidget.colors
        except AttributeError:
            style = None

        # find the value for colors:
        if colors:
            colors=colors.lower()
            if colors in ('lightbg', 'light'):
                colors='lightbg'
            elif colors in ('dark', 'linux'):
                colors='linux'
            else:
                colors='nocolor'
        elif style:
            if style=='bw':
                colors='nocolor'
            elif styles.dark_style(style):
                colors='linux'
            else:
                colors='lightbg'
        else:
            colors=None

        # Configure the style.
        widget = self.widget
        if style:
            widget.style_sheet = styles.sheet_from_template(style, colors)
            widget.syntax_style = style
            widget._syntax_style_changed()
            widget._style_sheet_changed()
        elif colors:
            # use a default style
            widget.set_default_style(colors=colors)
        else:
            # this is redundant for now, but allows the widget's
            # defaults to change
            widget.set_default_style()

        if self.stylesheet:
            # we got an expicit stylesheet
            if os.path.isfile(self.stylesheet):
                with open(self.stylesheet) as f:
                    sheet = f.read()
                widget.style_sheet = sheet
                widget._style_sheet_changed()
            else:
                raise IOError("Stylesheet %r not found."%self.stylesheet)

    def initialize(self, argv=None):
        super(IPythonQtConsoleApp, self).initialize(argv)
        self.init_kernel_manager()
        self.init_qt_elements()
        self.init_colors()

    def start(self):

        # draw the window
        self.window.show()

        # Start the application main loop.
        self.app.exec_()

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def main():
    app = IPythonQtConsoleApp()
    app.initialize()
    app.start()


if __name__ == '__main__':
    main()

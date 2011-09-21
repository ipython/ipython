""" A minimal application using the Qt console-style IPython frontend.

This is not a complete console app, as subprocess will not be able to receive
input, there is no real readline support, among other limitations.

Authors:

* Evan Patterson
* Min RK
* Erik Tollerud
* Fernando Perez

"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# stdlib imports
import json
import os
import signal
import sys

# System library imports
from IPython.external.qt import QtGui,QtCore
from pygments.styles import get_all_styles

# Local imports
from IPython.config.application import boolean_flag
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.lib.kernel import tunnel_to_kernel, find_connection_file
from IPython.frontend.qt.console.frontend_widget import FrontendWidget
from IPython.frontend.qt.console.ipython_widget import IPythonWidget
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.console import styles
from IPython.frontend.qt.kernelmanager import QtKernelManager
from IPython.utils.path import filefind
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import (
    Dict, List, Unicode, Int, CaselessStrEnum, CBool, Any
)
from IPython.zmq.ipkernel import (
    flags as ipkernel_flags,
    aliases as ipkernel_aliases,
    IPKernelApp
)
from IPython.zmq.session import Session, default_secure
from IPython.zmq.zmqshell import ZMQInteractiveShell

import application_rc

#-----------------------------------------------------------------------------
# Network Constants
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

_examples = """
ipython qtconsole                 # start the qtconsole
ipython qtconsole --pylab=inline  # start with pylab in inline plotting mode
"""

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class MainWindow(QtGui.QMainWindow):

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, app, frontend, existing=False, may_close=True,
                    confirm_exit=True):
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
        self._confirm_exit = confirm_exit
        self.setCentralWidget(frontend)

        # MenuBar is always present on Mac Os, so let's populate
        # it with possible action, don't do it on other platform
        # as some user might not want the menu bar, or give them
        # an option to remove it
        if sys.platform == 'darwin':
            #create menu in the order they should appear in the menu bar
            self.fileMenu = self.menuBar().addMenu("File")
            self.editMenu = self.menuBar().addMenu("Edit")
            self.fontMenu = self.menuBar().addMenu("Font")
            self.windowMenu = self.menuBar().addMenu("Window")
            self.magicMenu = self.menuBar().addMenu("Magic")

            # please keep the Help menu in Mac Os even if empty. It will
            # automatically contain a search field to search inside menus and
            # please keep it spelled in English, as long as Qt Doesn't support
            # a QAction.MenuRole like HelpMenuRole otherwise it will loose
            # this search field fonctionnality

            self.helpMenu = self.menuBar().addMenu("Help")

            # sould wrap every line of the following block into a try/except,
            # as we are not sure of instanciating a _frontend which support all
            # theses actions, but there might be a better way

            self.fileMenu.addAction(self._frontend.print_action)
            self.fileMenu.addAction(self._frontend.export_action)
            self.fileMenu.addAction(self._frontend.select_all_action)

            self.editMenu.addAction(self._frontend.undo_action)
            self.editMenu.addAction(self._frontend.redo_action)

            self.fontMenu.addAction(self._frontend.increase_font_size)
            self.fontMenu.addAction(self._frontend.decrease_font_size)
            self.fontMenu.addAction(self._frontend.reset_font_size)

            self.magicMenu.addAction(self._frontend.reset_action)
            self.magicMenu.addAction(self._frontend.history_action)
            self.magicMenu.addAction(self._frontend.save_action)
            self.magicMenu.addAction(self._frontend.clear_action)
            self.magicMenu.addAction(self._frontend.who_action)
            self.magicMenu.addAction(self._frontend.who_ls_action)
            self.magicMenu.addAction(self._frontend.whos_action)

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
        
        if keepkernel is None and not self._confirm_exit:
            # don't prompt, just terminate the kernel if we own it
            # or leave it alone if we don't
            keepkernel = not self._existing
        
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
                    pixmap = QtGui.QPixmap(':/icon/IPythonConsole.png')
                    scaledpixmap = pixmap.scaledToWidth(64,mode=QtCore.Qt.SmoothTransformation)
                    box.setIconPixmap(scaledpixmap)
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
qt_flags = {
    'existing' : ({'IPythonQtConsoleApp' : {'existing' : 'kernel*.json'}},
            "Connect to an existing kernel. If no argument specified, guess most recent"),
    'pure' : ({'IPythonQtConsoleApp' : {'pure' : True}},
            "Use a pure Python kernel instead of an IPython kernel."),
    'plain' : ({'ConsoleWidget' : {'kind' : 'plain'}},
            "Disable rich text support."),
}
qt_flags.update(boolean_flag(
    'gui-completion', 'ConsoleWidget.gui_completion',
    "use a GUI widget for tab completion",
    "use plaintext output for completion"
))
qt_flags.update(boolean_flag(
    'confirm-exit', 'IPythonQtConsoleApp.confirm_exit',
    """Set to display confirmation dialog on exit. You can always use 'exit' or 'quit',
       to force a direct exit without any confirmation.
    """,
    """Don't prompt the user when exiting. This will terminate the kernel
       if it is owned by the frontend, and leave it alive if it is external.
    """
))
flags.update(qt_flags)

aliases = dict(ipkernel_aliases)

qt_aliases = dict(
    hb = 'IPythonQtConsoleApp.hb_port',
    shell = 'IPythonQtConsoleApp.shell_port',
    iopub = 'IPythonQtConsoleApp.iopub_port',
    stdin = 'IPythonQtConsoleApp.stdin_port',
    ip = 'IPythonQtConsoleApp.ip',
    existing = 'IPythonQtConsoleApp.existing',
    f = 'IPythonQtConsoleApp.connection_file',

    style = 'IPythonWidget.syntax_style',
    stylesheet = 'IPythonQtConsoleApp.stylesheet',
    colors = 'ZMQInteractiveShell.colors',

    editor = 'IPythonWidget.editor',
    paging = 'ConsoleWidget.paging',
    ssh = 'IPythonQtConsoleApp.sshserver',
)
aliases.update(qt_aliases)


#-----------------------------------------------------------------------------
# IPythonQtConsole
#-----------------------------------------------------------------------------


class IPythonQtConsoleApp(BaseIPythonApplication):
    name = 'ipython-qtconsole'
    default_config_file_name='ipython_config.py'
    
    description = """
        The IPython QtConsole.
        
        This launches a Console-style application using Qt.  It is not a full
        console, in that launched terminal subprocesses will not be able to accept
        input.
        
        The QtConsole supports various extra features beyond the Terminal IPython
        shell, such as inline plotting with matplotlib, via:
        
            ipython qtconsole --pylab=inline
        
        as well as saving your session as HTML, and printing the output.
        
    """
    examples = _examples

    classes = [IPKernelApp, IPythonWidget, ZMQInteractiveShell, ProfileDir, Session]
    flags = Dict(flags)
    aliases = Dict(aliases)

    kernel_argv = List(Unicode)

    # create requested profiles by default, if they don't exist:
    auto_create = CBool(True)
    # connection info:
    ip = Unicode(LOCALHOST, config=True,
        help="""Set the kernel\'s IP address [default localhost].
        If the IP address is something other than localhost, then
        Consoles on other machines will be able to connect
        to the Kernel, so be careful!"""
    )
    
    sshserver = Unicode('', config=True,
        help="""The SSH server to use to connect to the kernel.""")
    sshkey = Unicode('', config=True,
        help="""Path to the ssh key to use for logging in to the ssh server.""")
    
    hb_port = Int(0, config=True,
        help="set the heartbeat port [default: random]")
    shell_port = Int(0, config=True,
        help="set the shell (XREP) port [default: random]")
    iopub_port = Int(0, config=True,
        help="set the iopub (PUB) port [default: random]")
    stdin_port = Int(0, config=True,
        help="set the stdin (XREQ) port [default: random]")
    connection_file = Unicode('', config=True,
        help="""JSON file in which to store connection info [default: kernel-<pid>.json]

        This file will contain the IP, ports, and authentication key needed to connect
        clients to this kernel. By default, this file will be created in the security-dir
        of the current profile, but can be specified by absolute path.
        """)
    def _connection_file_default(self):
        return 'kernel-%i.json' % os.getpid()

    existing = Unicode('', config=True,
        help="""Connect to an already running kernel""")

    stylesheet = Unicode('', config=True,
        help="path to a custom CSS stylesheet")

    pure = CBool(False, config=True,
        help="Use a pure Python kernel instead of an IPython kernel.")
    plain = CBool(False, config=True,
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

    confirm_exit = CBool(True, config=True,
        help="""
        Set to display confirmation dialog on exit. You can always use 'exit' or 'quit',
        to force a direct exit without any confirmation.""",
    )
    
    # the factory for creating a widget
    widget_factory = Any(RichIPythonWidget)

    def parse_command_line(self, argv=None):
        super(IPythonQtConsoleApp, self).parse_command_line(argv)
        if argv is None:
            argv = sys.argv[1:]

        self.kernel_argv = list(argv) # copy
        # kernel should inherit default config file from frontend
        self.kernel_argv.append("--KernelApp.parent_appname='%s'"%self.name)
        # Scrub frontend-specific flags
        for a in argv:
            if a.startswith('-') and a.lstrip('-') in qt_flags:
                self.kernel_argv.remove(a)
        swallow_next = False
        for a in argv:
            if swallow_next:
                self.kernel_argv.remove(a)
                swallow_next = False
                continue
            if a.startswith('-'):
                split = a.lstrip('-').split('=')
                alias = split[0]
                if alias in qt_aliases:
                    self.kernel_argv.remove(a)
                    if len(split) == 1:
                        # alias passed with arg via space
                        swallow_next = True
    
    def init_connection_file(self):
        """find the connection file, and load the info if found.
        
        The current working directory and the current profile's security
        directory will be searched for the file if it is not given by
        absolute path.
        
        When attempting to connect to an existing kernel and the `--existing`
        argument does not match an existing file, it will be interpreted as a
        fileglob, and the matching file in the current profile's security dir
        with the latest access time will be used.
        """
        if self.existing:
            try:
                cf = find_connection_file(self.existing)
            except Exception:
                self.log.critical("Could not find existing kernel connection file %s", self.existing)
                self.exit(1)
            self.log.info("Connecting to existing kernel: %s" % cf)
            self.connection_file = cf
        # should load_connection_file only be used for existing?
        # as it is now, this allows reusing ports if an existing
        # file is requested
        try:
            self.load_connection_file()
        except Exception:
            self.log.error("Failed to load connection file: %r", self.connection_file, exc_info=True)
            self.exit(1)
    
    def load_connection_file(self):
        """load ip/port/hmac config from JSON connection file"""
        # this is identical to KernelApp.load_connection_file
        # perhaps it can be centralized somewhere?
        try:
            fname = filefind(self.connection_file, ['.', self.profile_dir.security_dir])
        except IOError:
            self.log.debug("Connection File not found: %s", self.connection_file)
            return
        self.log.debug(u"Loading connection file %s", fname)
        with open(fname) as f:
            s = f.read()
        cfg = json.loads(s)
        if self.ip == LOCALHOST and 'ip' in cfg:
            # not overridden by config or cl_args
            self.ip = cfg['ip']
        for channel in ('hb', 'shell', 'iopub', 'stdin'):
            name = channel + '_port'
            if getattr(self, name) == 0 and name in cfg:
                # not overridden by config or cl_args
                setattr(self, name, cfg[name])
        if 'key' in cfg:
            self.config.Session.key = str_to_bytes(cfg['key'])
    
    def init_ssh(self):
        """set up ssh tunnels, if needed."""
        if not self.sshserver and not self.sshkey:
            return
        
        if self.sshkey and not self.sshserver:
            # specifying just the key implies that we are connecting directly
            self.sshserver = self.ip
            self.ip = LOCALHOST
        
        # build connection dict for tunnels:
        info = dict(ip=self.ip,
                    shell_port=self.shell_port,
                    iopub_port=self.iopub_port,
                    stdin_port=self.stdin_port,
                    hb_port=self.hb_port
        )
        
        self.log.info("Forwarding connections to %s via %s"%(self.ip, self.sshserver))
        
        # tunnels return a new set of ports, which will be on localhost:
        self.ip = LOCALHOST
        try:
            newports = tunnel_to_kernel(info, self.sshserver, self.sshkey)
        except:
            # even catch KeyboardInterrupt
            self.log.error("Could not setup tunnels", exc_info=True)
            self.exit(1)
        
        self.shell_port, self.iopub_port, self.stdin_port, self.hb_port = newports
        
        cf = self.connection_file
        base,ext = os.path.splitext(cf)
        base = os.path.basename(base)
        self.connection_file = os.path.basename(base)+'-ssh'+ext
        self.log.critical("To connect another client via this tunnel, use:")
        self.log.critical("--existing %s" % self.connection_file)

    def init_kernel_manager(self):
        # Don't let Qt or ZMQ swallow KeyboardInterupts.
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sec = self.profile_dir.security_dir
        try:
            cf = filefind(self.connection_file, ['.', sec])
        except IOError:
            # file might not exist
            if self.connection_file == os.path.basename(self.connection_file):
                # just shortname, put it in security dir
                cf = os.path.join(sec, self.connection_file)
            else:
                cf = self.connection_file

        # Create a KernelManager and start a kernel.
        self.kernel_manager = QtKernelManager(
                                ip=self.ip,
                                shell_port=self.shell_port,
                                iopub_port=self.iopub_port,
                                stdin_port=self.stdin_port,
                                hb_port=self.hb_port,
                                connection_file=cf,
                                config=self.config,
        )
        # start the kernel
        if not self.existing:
            kwargs = dict(ipython=not self.pure)
            kwargs['extra_arguments'] = self.kernel_argv
            self.kernel_manager.start_kernel(**kwargs)
        elif self.sshserver:
            # ssh, write new connection file
            self.kernel_manager.write_connection_file()
        self.kernel_manager.start_channels()


    def init_qt_elements(self):
        # Create the widget.
        self.app = QtGui.QApplication([])
        pixmap=QtGui.QPixmap(':/icon/IPythonConsole.png')
        icon=QtGui.QIcon(pixmap)
        QtGui.QApplication.setWindowIcon(icon)

        local_kernel = (not self.existing) or self.ip in LOCAL_IPS
        self.widget = self.widget_factory(config=self.config,
                                        local_kernel=local_kernel)
        self.widget.kernel_manager = self.kernel_manager
        self.window = MainWindow(self.app, self.widget, self.existing,
                                may_close=local_kernel,
                                confirm_exit=self.confirm_exit)
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
        self.init_connection_file()
        default_secure(self.config)
        self.init_ssh()
        self.init_kernel_manager()
        self.init_qt_elements()
        self.init_colors()
        self.init_window_shortcut()

    def init_window_shortcut(self):

        self.fullScreenAct = QtGui.QAction("Full Screen",
            self.window,
            shortcut="Ctrl+Meta+Space",
            statusTip="Toggle between Fullscreen and Normal Size",
            triggered=self.toggleFullScreen)


        # creating shortcut in menubar only for Mac OS as I don't
        # know the shortcut or if the windows manager assign it in
        # other platform.
        if sys.platform == 'darwin':
            self.minimizeAct = QtGui.QAction("Minimize",
                self.window,
                shortcut="Ctrl+m",
                statusTip="Minimize the window/Restore Normal Size",
                triggered=self.toggleMinimized)
            self.maximizeAct = QtGui.QAction("Maximize",
                self.window,
                shortcut="Ctrl+Shift+M",
                statusTip="Maximize the window/Restore Normal Size",
                triggered=self.toggleMaximized)

            self.onlineHelpAct = QtGui.QAction("Open Online Help",
                self.window,
                triggered=self._open_online_help)

            self.windowMenu = self.window.windowMenu
            self.windowMenu.addAction(self.minimizeAct)
            self.windowMenu.addAction(self.maximizeAct)
            self.windowMenu.addSeparator()
            self.windowMenu.addAction(self.fullScreenAct)

            self.window.helpMenu.addAction(self.onlineHelpAct)
        else:
            # if we don't put it in a menu, we add it to the window so
            # that it can still be triggerd by shortcut
            self.window.addAction(self.fullScreenAct)

    def toggleMinimized(self):
        if not self.window.isMinimized():
            self.window.showMinimized()
        else:
            self.window.showNormal()

    def _open_online_help(self):
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl("http://ipython.org/documentation.html",
            QtCore.QUrl.TolerantMode)
            )

    def toggleMaximized(self):
        if not self.window.isMaximized():
            self.window.showMaximized()
        else:
            self.window.showNormal()

    # Min/Max imizing while in full screen give a bug
    # when going out of full screen, at least on OSX
    def toggleFullScreen(self):
        if not self.window.isFullScreen():
            self.window.showFullScreen()
            if sys.platform == 'darwin':
                self.maximizeAct.setEnabled(False)
                self.minimizeAct.setEnabled(False)
        else:
            self.window.showNormal()
            if sys.platform == 'darwin':
                self.maximizeAct.setEnabled(True)
                self.minimizeAct.setEnabled(True)

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

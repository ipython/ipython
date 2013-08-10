""" A minimal application using the Qt console-style IPython frontend.

This is not a complete console app, as subprocess will not be able to receive
input, there is no real readline support, among other limitations.

Authors:

* Evan Patterson
* Min RK
* Erik Tollerud
* Fernando Perez
* Bussonnier Matthias
* Thomas Kluyver
* Paul Ivanov

"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# stdlib imports
import os
import signal
import sys

# If run on Windows, install an exception hook which pops up a
# message box. Pythonw.exe hides the console, so without this
# the application silently fails to load.
#
# We always install this handler, because the expectation is for
# qtconsole to bring up a GUI even if called from the console.
# The old handler is called, so the exception is printed as well.
# If desired, check for pythonw with an additional condition
# (sys.executable.lower().find('pythonw.exe') >= 0).
if os.name == 'nt':
    old_excepthook = sys.excepthook

    def gui_excepthook(exctype, value, tb):
        try:
            import ctypes, traceback
            MB_ICONERROR = 0x00000010L
            title = u'Error starting IPython QtConsole'
            msg = u''.join(traceback.format_exception(exctype, value, tb))
            ctypes.windll.user32.MessageBoxW(0, msg, title, MB_ICONERROR)
        finally:
            # Also call the old exception hook to let it do
            # its thing too.
            old_excepthook(exctype, value, tb)

    sys.excepthook = gui_excepthook

# System library imports
from IPython.external.qt import QtCore, QtGui

# Local imports
from IPython.config.application import catch_config_error
from IPython.core.application import BaseIPythonApplication
from IPython.qt.console.ipython_widget import IPythonWidget
from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.console import styles
from IPython.qt.console.mainwindow import MainWindow
from IPython.qt.client import QtKernelClient
from IPython.qt.manager import QtKernelManager
from IPython.utils.traitlets import (
    Dict, Unicode, CBool, Any
)

from IPython.consoleapp import (
        IPythonConsoleApp, app_aliases, app_flags, flags, aliases
    )

#-----------------------------------------------------------------------------
# Network Constants
#-----------------------------------------------------------------------------

from IPython.utils.localinterfaces import LOCALHOST, LOCAL_IPS

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

_examples = """
ipython qtconsole                      # start the qtconsole
ipython qtconsole --matplotlib=inline  # start with matplotlib inline plotting mode
"""

#-----------------------------------------------------------------------------
# Aliases and Flags
#-----------------------------------------------------------------------------

# start with copy of flags
flags = dict(flags)
qt_flags = {
    'plain' : ({'IPythonQtConsoleApp' : {'plain' : True}},
            "Disable rich text support."),
}

# and app_flags from the Console Mixin
qt_flags.update(app_flags)
# add frontend flags to the full set
flags.update(qt_flags)

# start with copy of front&backend aliases list
aliases = dict(aliases)
qt_aliases = dict(
    style = 'IPythonWidget.syntax_style',
    stylesheet = 'IPythonQtConsoleApp.stylesheet',
    colors = 'ZMQInteractiveShell.colors',

    editor = 'IPythonWidget.editor',
    paging = 'ConsoleWidget.paging',
)
# and app_aliases from the Console Mixin
qt_aliases.update(app_aliases)
qt_aliases.update({'gui-completion':'ConsoleWidget.gui_completion'})
# add frontend aliases to the full set
aliases.update(qt_aliases)

# get flags&aliases into sets, and remove a couple that
# shouldn't be scrubbed from backend flags:
qt_aliases = set(qt_aliases.keys())
qt_aliases.remove('colors')
qt_flags = set(qt_flags.keys())

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# IPythonQtConsole
#-----------------------------------------------------------------------------


class IPythonQtConsoleApp(BaseIPythonApplication, IPythonConsoleApp):
    name = 'ipython-qtconsole'

    description = """
        The IPython QtConsole.
        
        This launches a Console-style application using Qt.  It is not a full
        console, in that launched terminal subprocesses will not be able to accept
        input.
        
        The QtConsole supports various extra features beyond the Terminal IPython
        shell, such as inline plotting with matplotlib, via:
        
            ipython qtconsole --matplotlib=inline
        
        as well as saving your session as HTML, and printing the output.
        
    """
    examples = _examples

    classes = [IPythonWidget] + IPythonConsoleApp.classes
    flags = Dict(flags)
    aliases = Dict(aliases)
    frontend_flags = Any(qt_flags)
    frontend_aliases = Any(qt_aliases)
    kernel_client_class = QtKernelClient
    kernel_manager_class = QtKernelManager

    stylesheet = Unicode('', config=True,
        help="path to a custom CSS stylesheet")

    hide_menubar = CBool(False, config=True,
        help="Start the console window with the menu bar hidden.")

    maximize = CBool(False, config=True,
        help="Start the console window maximized.")

    plain = CBool(False, config=True,
        help="Use a plaintext widget instead of rich text (plain can't print/save).")

    def _plain_changed(self, name, old, new):
        kind = 'plain' if new else 'rich'
        self.config.ConsoleWidget.kind = kind
        if new:
            self.widget_factory = IPythonWidget
        else:
            self.widget_factory = RichIPythonWidget

    # the factory for creating a widget
    widget_factory = Any(RichIPythonWidget)

    def parse_command_line(self, argv=None):
        super(IPythonQtConsoleApp, self).parse_command_line(argv)
        self.build_kernel_argv(argv)


    def new_frontend_master(self):
        """ Create and return new frontend attached to new kernel, launched on localhost.
        """
        kernel_manager = self.kernel_manager_class(
                                connection_file=self._new_connection_file(),
                                parent=self,
                                autorestart=True,
        )
        # start the kernel
        kwargs = dict()
        kwargs['extra_arguments'] = self.kernel_argv
        kernel_manager.start_kernel(**kwargs)
        kernel_manager.client_factory = self.kernel_client_class
        kernel_client = kernel_manager.client()
        kernel_client.start_channels(shell=True, iopub=True)
        widget = self.widget_factory(config=self.config,
                                   local_kernel=True)
        self.init_colors(widget)
        widget.kernel_manager = kernel_manager
        widget.kernel_client = kernel_client
        widget._existing = False
        widget._may_close = True
        widget._confirm_exit = self.confirm_exit
        return widget

    def new_frontend_slave(self, current_widget):
        """Create and return a new frontend attached to an existing kernel.
        
        Parameters
        ----------
        current_widget : IPythonWidget
            The IPythonWidget whose kernel this frontend is to share
        """
        kernel_client = self.kernel_client_class(
                                connection_file=current_widget.kernel_client.connection_file,
                                config = self.config,
        )
        kernel_client.load_connection_file()
        kernel_client.start_channels()
        widget = self.widget_factory(config=self.config,
                                local_kernel=False)
        self.init_colors(widget)
        widget._existing = True
        widget._may_close = False
        widget._confirm_exit = False
        widget.kernel_client = kernel_client
        widget.kernel_manager = current_widget.kernel_manager
        return widget

    def init_qt_app(self):
        # separate from qt_elements, because it must run first
        self.app = QtGui.QApplication([])

    def init_qt_elements(self):
        # Create the widget.

        base_path = os.path.abspath(os.path.dirname(__file__))
        icon_path = os.path.join(base_path, 'resources', 'icon', 'IPythonConsole.svg')
        self.app.icon = QtGui.QIcon(icon_path)
        QtGui.QApplication.setWindowIcon(self.app.icon)

        ip = self.ip
        local_kernel = (not self.existing) or ip in LOCAL_IPS
        self.widget = self.widget_factory(config=self.config,
                                        local_kernel=local_kernel)
        self.init_colors(self.widget)
        self.widget._existing = self.existing
        self.widget._may_close = not self.existing
        self.widget._confirm_exit = self.confirm_exit

        self.widget.kernel_manager = self.kernel_manager
        self.widget.kernel_client = self.kernel_client
        self.window = MainWindow(self.app,
                                confirm_exit=self.confirm_exit,
                                new_frontend_factory=self.new_frontend_master,
                                slave_frontend_factory=self.new_frontend_slave,
                                )
        self.window.log = self.log
        self.window.add_tab_with_frontend(self.widget)
        self.window.init_menu_bar()

        # Ignore on OSX, where there is always a menu bar
        if sys.platform != 'darwin' and self.hide_menubar:
            self.window.menuBar().setVisible(False)

        self.window.setWindowTitle('IPython')

    def init_colors(self, widget):
        """Configure the coloring of the widget"""
        # Note: This will be dramatically simplified when colors
        # are removed from the backend.

        # parse the colors arg down to current known labels
        try:
            colors = self.config.ZMQInteractiveShell.colors
        except AttributeError:
            colors = None
        try:
            style = self.config.IPythonWidget.syntax_style
        except AttributeError:
            style = None
        try:
            sheet = self.config.IPythonWidget.style_sheet
        except AttributeError:
            sheet = None

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

        # Configure the style
        if style:
            widget.style_sheet = styles.sheet_from_template(style, colors)
            widget.syntax_style = style
            widget._syntax_style_changed()
            widget._style_sheet_changed()
        elif colors:
            # use a default dark/light/bw style
            widget.set_default_style(colors=colors)

        if self.stylesheet:
            # we got an explicit stylesheet
            if os.path.isfile(self.stylesheet):
                with open(self.stylesheet) as f:
                    sheet = f.read()
            else:
                raise IOError("Stylesheet %r not found." % self.stylesheet)
        if sheet:
            widget.style_sheet = sheet
            widget._style_sheet_changed()
            

    def init_signal(self):
        """allow clean shutdown on sigint"""
        signal.signal(signal.SIGINT, lambda sig, frame: self.exit(-2))
        # need a timer, so that QApplication doesn't block until a real
        # Qt event fires (can require mouse movement)
        # timer trick from http://stackoverflow.com/q/4938723/938949
        timer = QtCore.QTimer()
         # Let the interpreter run each 200 ms:
        timer.timeout.connect(lambda: None)
        timer.start(200)
        # hold onto ref, so the timer doesn't get cleaned up
        self._sigint_timer = timer

    @catch_config_error
    def initialize(self, argv=None):
        self.init_qt_app()
        super(IPythonQtConsoleApp, self).initialize(argv)
        IPythonConsoleApp.initialize(self,argv)
        self.init_qt_elements()
        self.init_signal()

    def start(self):

        # draw the window
        if self.maximize:
            self.window.showMaximized()
        else:
            self.window.show()
        self.window.raise_()

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

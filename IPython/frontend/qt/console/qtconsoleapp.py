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
import json
import os
import signal
import sys
import uuid

# System library imports
from IPython.external.qt import QtGui

# Local imports
from IPython.config.application import boolean_flag, catch_config_error
from IPython.core.application import BaseIPythonApplication
from IPython.core.profiledir import ProfileDir
from IPython.lib.kernel import tunnel_to_kernel, find_connection_file
from IPython.frontend.qt.console.frontend_widget import FrontendWidget
from IPython.frontend.qt.console.ipython_widget import IPythonWidget
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.console import styles
from IPython.frontend.qt.console.mainwindow import MainWindow
from IPython.frontend.qt.kernelmanager import QtKernelManager
from IPython.utils.path import filefind
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import (
    Dict, List, Unicode, Integer, CaselessStrEnum, CBool, Any
)
from IPython.zmq.ipkernel import IPKernelApp
from IPython.zmq.session import Session, default_secure
from IPython.zmq.zmqshell import ZMQInteractiveShell
from IPython.frontend.kernelmixinapp import (
        IPythonMixinConsoleApp, app_aliases, app_flags
    )

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
# Aliases and Flags
#-----------------------------------------------------------------------------

flags = dict(app_flags)
qt_flags = {
    #'existing' : ({'IPythonQtConsoleApp' : {'existing' : 'kernel*.json'}},
    #        "Connect to an existing kernel. If no argument specified, guess most recent"),
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
flags.update(qt_flags)

aliases = dict(app_aliases)

qt_aliases = dict(
    existing = 'IPythonQtConsoleApp.existing',
    f = 'IPythonQtConsoleApp.connection_file',

    style = 'IPythonWidget.syntax_style',
    stylesheet = 'IPythonQtConsoleApp.stylesheet',
    colors = 'ZMQInteractiveShell.colors',

    editor = 'IPythonWidget.editor',
    paging = 'ConsoleWidget.paging',
)
aliases.update(qt_aliases)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# IPythonQtConsole
#-----------------------------------------------------------------------------


class IPythonQtConsoleApp(BaseIPythonApplication, IPythonMixinConsoleApp):
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
    kernel_manager_class = QtKernelManager

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
        swallow_next = False
        was_flag = False
        # copy again, in case some aliases have the same name as a flag
        # argv = list(self.kernel_argv)
        for a in argv:
            if swallow_next:
                swallow_next = False
                # last arg was an alias, remove the next one
                # *unless* the last alias has a no-arg flag version, in which
                # case, don't swallow the next arg if it's also a flag:
                if not (was_flag and a.startswith('-')):
                    self.kernel_argv.remove(a)
                    continue
            if a.startswith('-'):
                split = a.lstrip('-').split('=')
                alias = split[0]
                if alias in qt_aliases:
                    self.kernel_argv.remove(a)
                    if len(split) == 1:
                        # alias passed with arg via space
                        swallow_next = True
                        # could have been a flag that matches an alias, e.g. `existing`
                        # in which case, we might not swallow the next arg
                        was_flag = alias in qt_flags
                elif alias in qt_flags:
                    # strip flag, but don't swallow next, as flags don't take args
                    self.kernel_argv.remove(a)
    


    def new_frontend_master(self):
        """ Create and return new frontend attached to new kernel, launched on localhost.
        """
        ip = self.ip if self.ip in LOCAL_IPS else LOCALHOST
        kernel_manager = QtKernelManager(
                                ip=ip,
                                connection_file=self._new_connection_file(),
                                config=self.config,
        )
        # start the kernel
        kwargs = dict(ipython=not self.pure)
        kwargs['extra_arguments'] = self.kernel_argv
        kernel_manager.start_kernel(**kwargs)
        kernel_manager.start_channels()
        widget = self.widget_factory(config=self.config,
                                   local_kernel=True)
        widget.kernel_manager = kernel_manager
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
        kernel_manager = QtKernelManager(
                                connection_file=current_widget.kernel_manager.connection_file,
                                config = self.config,
        )
        kernel_manager.load_connection_file()
        kernel_manager.start_channels()
        widget = self.widget_factory(config=self.config,
                                local_kernel=False)
        widget._existing = True
        widget._may_close = False
        widget._confirm_exit = False
        widget.kernel_manager = kernel_manager
        return widget

    def init_qt_elements(self):
        # Create the widget.
        self.app = QtGui.QApplication([])

        base_path = os.path.abspath(os.path.dirname(__file__))
        icon_path = os.path.join(base_path, 'resources', 'icon', 'IPythonConsole.svg')
        self.app.icon = QtGui.QIcon(icon_path)
        QtGui.QApplication.setWindowIcon(self.app.icon)

        local_kernel = (not self.existing) or self.ip in LOCAL_IPS
        self.widget = self.widget_factory(config=self.config,
                                        local_kernel=local_kernel)
        self.widget._existing = self.existing
        self.widget._may_close = not self.existing
        self.widget._confirm_exit = self.confirm_exit

        self.widget.kernel_manager = self.kernel_manager
        self.window = MainWindow(self.app,
                                confirm_exit=self.confirm_exit,
                                new_frontend_factory=self.new_frontend_master,
                                slave_frontend_factory=self.new_frontend_slave,
                                )
        self.window.log = self.log
        self.window.add_tab_with_frontend(self.widget)
        self.window.init_menu_bar()

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
            style = self.config.IPythonWidget.syntax_style
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

    @catch_config_error
    def initialize(self, argv=None):
        super(IPythonQtConsoleApp, self).initialize(argv)
        self.init_connection_file()
        default_secure(self.config)
        self.init_ssh()
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

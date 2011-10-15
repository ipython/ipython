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
import webbrowser
from getpass import getpass

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

        self.tab_widget = QtGui.QTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested[int].connect(self.close_tab)

        self.setCentralWidget(self.tab_widget)
        self.update_tab_bar_visibility()

    def update_tab_bar_visibility(self):
        """ update visibility of the tabBar depending of the number of tab

        0 or 1 tab, tabBar hidden
        2+ tabs, tabBar visible

        send a self.close if number of tab ==0

        need to be called explicitely, or be connected to tabInserted/tabRemoved
        """
        if self.tab_widget.count() <= 1:
            self.tab_widget.tabBar().setVisible(False)
        else:
            self.tab_widget.tabBar().setVisible(True)
        if self.tab_widget.count()==0 :
            self.close()

    @property
    def active_frontend(self):
        return self.tab_widget.currentWidget()

    def close_tab(self,current_tab):
        """ Called when you need to try to close a tab.

        It takes the number of the tab to be closed as argument, or a referece
        to the wiget insite this tab
        """

        # let's be sure "tab" and "closing widget are respectivey the index of the tab to close
        # and a reference to the trontend to close
        if type(current_tab) is not int :
            current_tab = self.tab_widget.indexOf(current_tab)
        closing_widget=self.tab_widget.widget(current_tab)


        # when trying to be closed, widget might re-send a request to be closed again, but will
        # be deleted when event will be processed. So need to check that widget still exist and
        # skip if not. One example of this is when 'exit' is send in a slave tab. 'exit' will be
        # re-send by this fonction on the master widget, which ask all slaves widget to exit
        if closing_widget==None:
            return

        #get a list of all wwidget not owning the kernel.
        slave_tabs=self.find_slaves_tabs(closing_widget)

        keepkernel = None #Use the prompt by default
        if hasattr(closing_widget,'_keep_kernel_on_exit'): #set by exit magic
            keepkernel = closing_widget._keep_kernel_on_exit
            # If signal sent by exist magic (_keep_kernel_on_exit, exist and not None)
            # we set local slave tabs._hidden to True to avoit prompting for kernel
            # restart when they litt get the signal. and the "forward" the 'exit'
            # to the main win
            if keepkernel is not None:
                for tab in slave_tabs:
                    tab._hidden = True
                if closing_widget in slave_tabs :
                    try :
                        self.find_master_tab(closing_widget).execute('exit')
                    except AttributeError:
                        self.log.info("Master already closed or not local, closing only current tab")
                        self.tab_widget.removeTab(current_tab)
                    return

        kernel_manager = closing_widget.kernel_manager

        if keepkernel is None and not closing_widget._confirm_exit:
            # don't prompt, just terminate the kernel if we own it
            # or leave it alone if we don't
            keepkernel = not closing_widget._existing

        if keepkernel is None: #show prompt
            if kernel_manager and kernel_manager.channels_running:
                title = self.window().windowTitle()
                cancel = QtGui.QMessageBox.Cancel
                okay = QtGui.QMessageBox.Ok
                if closing_widget._may_close:
                    msg = "You are closing the tab : "+'"'+self.tab_widget.tabText(current_tab)+'"'
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
                    pixmap = QtGui.QPixmap(self._app.icon.pixmap(QtCore.QSize(64,64)))
                    box.setIconPixmap(pixmap)
                    reply = box.exec_()
                    if reply == 1: # close All
                        for slave in slave_tabs:
                            self.tab_widget.removeTab(self.tab_widget.indexOf(slave))
                        closing_widget.execute("exit")
                        self.tab_widget.removeTab(current_tab)
                    elif reply == 0: # close Console
                        if not closing_widget._existing:
                            # Have kernel: don't quit, just close the window
                            self._app.setQuitOnLastWindowClosed(False)
                            closing_widget.execute("exit True")
                else:
                    reply = QtGui.QMessageBox.question(self, title,
                        "Are you sure you want to close this Console?"+
                        "\nThe Kernel and other Consoles will remain active.",
                        okay|cancel,
                        defaultButton=okay
                        )
                    if reply == okay:
                        self.tab_widget.removeTab(current_tab)
        elif keepkernel: #close console but leave kernel running (no prompt)
            if kernel_manager and kernel_manager.channels_running:
                if not closing_widget._existing:
                    # I have the kernel: don't quit, just close the window
                    self.tab_widget.removeTab(current_tab)
        else: #close console and kernel (no prompt)
            if kernel_manager and kernel_manager.channels_running:
                for slave in slave_tabs:
                    self.tab_widget.removeTab(self.tab_widget.indexOf(slave))
                self.tab_widget.removeTab(current_tab)
                kernel_manager.shutdown_kernel()
        self.update_tab_bar_visibility()

    def add_tab_with_frontend(self,frontend,name=None):
        """ insert a tab with a given frontend in the tab bar, and give it a name

        """
        if not name:
            name=str('kernel '+str(self.tab_widget.count()))
        self.tab_widget.addTab(frontend,name)
        self.update_tab_bar_visibility()
        self.make_frontend_visible(frontend)
        frontend.exit_requested.connect(self.close_tab)

    def next_tab(self):
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex()+1))

    def prev_tab(self):
        self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex()-1))

    def make_frontend_visible(self,frontend):
        widget_index=self.tab_widget.indexOf(frontend)
        if widget_index > 0 :
            self.tab_widget.setCurrentIndex(widget_index)

    def find_master_tab(self,tab,as_list=False):
        """
        Try to return the frontend that own the kernel attached to the given widget/tab.

            Only find frontend owed by the current application. Selection
            based on port of the kernel, might be inacurate if several kernel
            on different ip use same port number.

            This fonction does the conversion tabNumber/widget if needed.
            Might return None if no master widget (non local kernel)
            Will crash IPython if more than 1 masterWidget

            When asList set to True, always return a list of widget(s) owning
            the kernel. The list might be empty or containing several Widget.
        """

        #convert from/to int/richIpythonWidget if needed
        if type(tab) == int:
            tab = self.tab_widget.widget(tab)
        km=tab.kernel_manager;

        #build list of all widgets
        widget_list = [self.tab_widget.widget(i) for i in range(self.tab_widget.count())]

        # widget that are candidate to be the owner of the kernel does have all the same port of the curent widget
        # And should have a _may_close attribute
        filtred_widget_list = [ widget for widget in widget_list if
                                widget.kernel_manager.shell_address == km.shell_address and
                                widget.kernel_manager.sub_address   == km.sub_address and
                                widget.kernel_manager.stdin_address == km.stdin_address and
                                widget.kernel_manager.hb_address    == km.hb_address and
                                hasattr(widget,'_may_close') ]
        # the master widget is the one that may close the kernel
        master_widget= [ widget for widget in filtred_widget_list if widget._may_close]
        if as_list:
            return master_widget
        assert(len(master_widget)<=1 )
        if len(master_widget)==0:
            return None

        return master_widget[0]

    def find_slaves_tabs(self,tab):
        """
        Try to return all the frontend that do not own the kernel attached to the given widget/tab.

            Only find frontend owed by the current application. Selection
            based on port of the kernel, might be innacurate if several kernel
            on different ip use same port number.

            This fonction does the conversion tabNumber/widget if needed.
        """
        #convert from/to int/richIpythonWidget if needed
        if type(tab) == int:
            tab = self.tab_widget.widget(tab)
        km=tab.kernel_manager;

        #build list of all widgets
        widget_list = [self.tab_widget.widget(i) for i in range(self.tab_widget.count())]

        # widget that are candidate not to be the owner of the kernel does have all the same port of the curent widget
        filtered_widget_list = ( widget for widget in widget_list if
                                widget.kernel_manager.shell_address == km.shell_address and
                                widget.kernel_manager.sub_address   == km.sub_address and
                                widget.kernel_manager.stdin_address == km.stdin_address and
                                widget.kernel_manager.hb_address    == km.hb_address)
        # Get a list of all widget owning the same kernel and removed it from
        # the previous cadidate. (better using sets ?)
        master_widget_list = self.find_master_tab(tab,as_list=True)
        slave_list = [widget for widget in filtered_widget_list if widget not in master_widget_list]

        return slave_list

    # MenuBar is always present on Mac Os, so let's populate it with possible
    # action, don't do it on other platform as some user might not want the
    # menu bar, or give them an option to remove it
    def init_menu_bar(self):
        #create menu in the order they should appear in the menu bar
        self.file_menu = self.menuBar().addMenu("&File")
        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.kernel_menu = self.menuBar().addMenu("&Kernel")
        self.window_menu = self.menuBar().addMenu("&Window")
        self.magic_menu = self.menuBar().addMenu("&Magic")
        self.all_magic_menu = self.magic_menu.addMenu("&All Magic")

        # please keep the Help menu in Mac Os even if empty. It will
        # automatically contain a search field to search inside menus and
        # please keep it spelled in English, as long as Qt Doesn't support
        # a QAction.MenuRole like HelpMenuRole otherwise it will loose
        # this search field fonctionnality

        self.help_menu = self.menuBar().addMenu("&Help")

        self.print_action = QtGui.QAction("&Print",
            self,
            shortcut="Ctrl+P",
            triggered=self.print_action_active_frontend)
        self.file_menu.addAction(self.print_action)

        self.export_action=QtGui.QAction("E&xport",
            self,
            shortcut="Ctrl+S",
            triggered=self.export_action_active_frontend
            )
        self.file_menu.addAction(self.export_action)

        self.select_all_action = QtGui.QAction("Select &All",
            self,
            shortcut="Ctrl+A",
            triggered=self.select_all_active_frontend
            )
        self.file_menu.addAction(self.select_all_action)

        self.paste_action = QtGui.QAction("&Paste",
            self,
            shortcut=QtGui.QKeySequence.Paste,
            triggered=self.paste_active_frontend
            )
        self.edit_menu.addAction(self.paste_action)

        self.copy_action = QtGui.QAction("&Copy",
            self,
            shortcut=QtGui.QKeySequence.Copy,
            triggered=self.copy_active_frontend
            )
        self.edit_menu.addAction(self.copy_action)

        self.copy_raw_action = QtGui.QAction("Copy (&Raw Text)",
            self,
            shortcut="Ctrl+Shift+C",
            triggered=self.copy_raw_active_frontend
            )
        self.edit_menu.addAction(self.copy_raw_action)

        self.cut_action = QtGui.QAction("&Cut",
            self,
            shortcut=QtGui.QKeySequence.Cut,
            triggered=self.cut_active_frontend
            )
        self.edit_menu.addAction(self.cut_action)

        self.edit_menu.addSeparator()

        self.undo_action = QtGui.QAction("&Undo",
            self,
            shortcut="Ctrl+Z",
            statusTip="Undo last action if possible",
            triggered=self.undo_active_frontend
            )
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QtGui.QAction("&Redo",
            self,
            shortcut="Ctrl+Shift+Z",
            statusTip="Redo last action if possible",
            triggered=self.redo_active_frontend)
        self.edit_menu.addAction(self.redo_action)

        self.window_menu.addSeparator()

        self.increase_font_size = QtGui.QAction("&Increase Font Size",
            self,
            shortcut="Ctrl++",
            triggered=self.increase_font_size_active_frontend
            )
        self.window_menu.addAction(self.increase_font_size)

        self.decrease_font_size = QtGui.QAction("&Decrease Font Size",
            self,
            shortcut="Ctrl+-",
            triggered=self.decrease_font_size_active_frontend
            )
        self.window_menu.addAction(self.decrease_font_size)

        self.reset_font_size = QtGui.QAction("&Reset Font Size",
            self,
            shortcut="Ctrl+0",
            triggered=self.reset_font_size_active_frontend
            )
        self.window_menu.addAction(self.reset_font_size)

        self.window_menu.addSeparator()

        self.reset_action = QtGui.QAction("&Reset",
            self,
            statusTip="Clear all varible from workspace",
            triggered=self.reset_magic_active_frontend)
        self.magic_menu.addAction(self.reset_action)

        self.history_action = QtGui.QAction("&History",
            self,
            statusTip="show command history",
            triggered=self.history_magic_active_frontend)
        self.magic_menu.addAction(self.history_action)

        self.save_action = QtGui.QAction("E&xport History ",
            self,
            statusTip="Export History as Python File",
            triggered=self.save_magic_active_frontend)
        self.magic_menu.addAction(self.save_action)

        self.clear_action = QtGui.QAction("&Clear Screen",
            self,
            shortcut='Ctrl+L',
            statusTip="Clear the console",
            triggered=self.clear_magic_active_frontend)
        self.window_menu.addAction(self.clear_action)

        self.who_action = QtGui.QAction("&Who",
            self,
            statusTip="List interactive variable",
            triggered=self.who_magic_active_frontend)
        self.magic_menu.addAction(self.who_action)

        self.who_ls_action = QtGui.QAction("Wh&o ls",
            self,
            statusTip="Return a list of interactive variable",
            triggered=self.who_ls_magic_active_frontend)
        self.magic_menu.addAction(self.who_ls_action)

        self.whos_action = QtGui.QAction("Who&s",
            self,
            statusTip="List interactive variable with detail",
            triggered=self.whos_magic_active_frontend)
        self.magic_menu.addAction(self.whos_action)

        self.intro_active_frontend_action = QtGui.QAction("Intro",
            self,
            triggered=self.intro_active_frontend
            )
        self.help_menu.addAction(self.intro_active_frontend_action)

        self.guiref_active_frontend_action = QtGui.QAction("Gui references",
            self,
            triggered=self.guiref_active_frontend
            )
        self.help_menu.addAction(self.guiref_active_frontend_action)

        self.quickref_active_frontend_action = QtGui.QAction("Quick references",
            self,
            triggered=self.quickref_active_frontend
            )
        self.help_menu.addAction(self.quickref_active_frontend_action)

        self.interrupt_kernel_action = QtGui.QAction("Interrupt current Kernel",
            self,
            triggered=self.interrupt_kernel_active_frontend
            )
        self.kernel_menu.addAction(self.interrupt_kernel_action)

        self.restart_kernel_action = QtGui.QAction("Restart current  Kernel",
            self,
            triggered=self.restart_kernel_active_frontend
            )
        self.kernel_menu.addAction(self.restart_kernel_action)
        self.kernel_menu.addSeparator()

        #for now this is just a copy and paste, but we should get this dynamically
        magiclist=["%alias", "%autocall", "%automagic", "%bookmark", "%cd", "%clear",
            "%colors", "%debug", "%dhist", "%dirs", "%doctest_mode", "%ed", "%edit", "%env", "%gui",
            "%guiref", "%hist", "%history", "%install_default_config", "%install_profiles",
            "%less", "%load_ext", "%loadpy", "%logoff", "%logon", "%logstart", "%logstate",
            "%logstop", "%lsmagic", "%macro", "%magic", "%man", "%more", "%notebook", "%page",
            "%pastebin", "%pdb", "%pdef", "%pdoc", "%pfile", "%pinfo", "%pinfo2", "%popd", "%pprint",
            "%precision", "%profile", "%prun", "%psearch", "%psource", "%pushd", "%pwd", "%pycat",
            "%pylab", "%quickref", "%recall", "%rehashx", "%reload_ext", "%rep", "%rerun",
            "%reset", "%reset_selective", "%run", "%save", "%sc", "%sx", "%tb", "%time", "%timeit",
            "%unalias", "%unload_ext", "%who", "%who_ls", "%whos", "%xdel", "%xmode"]

        def make_dynamic_magic(i):
                def inner_dynamic_magic():
                    self.active_frontend.execute(i)
                inner_dynamic_magic.__name__ = "dynamics_magic_%s" % i
                return inner_dynamic_magic

        for magic in magiclist:
            xaction = QtGui.QAction(magic,
                self,
                triggered=make_dynamic_magic(magic)
                )
            self.all_magic_menu.addAction(xaction)

    def restart_kernel_active_frontend(self):
        self.active_frontend.request_restart_kernel()

    def interrupt_kernel_active_frontend(self):
        self.active_frontend.request_interrupt_kernel()

    def cut_active_frontend(self):
        self.active_frontend.cut_action.trigger()

    def copy_active_frontend(self):
        self.active_frontend.copy_action.trigger()

    def copy_raw_active_frontend(self):
        self.active_frontend._copy_raw_action.trigger()

    def paste_active_frontend(self):
        self.active_frontend.paste_action.trigger()

    def undo_active_frontend(self):
        self.active_frontend.undo()

    def redo_active_frontend(self):
        self.active_frontend.redo()

    def reset_magic_active_frontend(self):
        self.active_frontend.execute("%reset")

    def history_magic_active_frontend(self):
        self.active_frontend.execute("%history")

    def save_magic_active_frontend(self):
        self.active_frontend.save_magic()

    def clear_magic_active_frontend(self):
        self.active_frontend.execute("%clear")

    def who_magic_active_frontend(self):
        self.active_frontend.execute("%who")

    def who_ls_magic_active_frontend(self):
        self.active_frontend.execute("%who_ls")

    def whos_magic_active_frontend(self):
        self.active_frontend.execute("%whos")

    def print_action_active_frontend(self):
        self.active_frontend.print_action.trigger()

    def export_action_active_frontend(self):
        self.active_frontend.export_action.trigger()

    def select_all_active_frontend(self):
        self.active_frontend.select_all_action.trigger()

    def increase_font_size_active_frontend(self):
        self.active_frontend.increase_font_size.trigger()

    def decrease_font_size_active_frontend(self):
        self.active_frontend.decrease_font_size.trigger()

    def reset_font_size_active_frontend(self):
        self.active_frontend.reset_font_size.trigger()

    def guiref_active_frontend(self):
        self.active_frontend.execute("%guiref")

    def intro_active_frontend(self):
        self.active_frontend.execute("?")

    def quickref_active_frontend(self):
        self.active_frontend.execute("%quickref")
    #---------------------------------------------------------------------------
    # QWidget interface
    #---------------------------------------------------------------------------

    def closeEvent(self, event):
        """ Forward the close event to every tabs contained by the windows
        """
        # Do Not loop on the widget count as it change while closing
        widget_list=[ self.tab_widget.widget(i) for i in  range(self.tab_widget.count())]
        for widget in widget_list:
            self.close_tab(widget)
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

    def create_tab_with_new_frontend(self):
        """ Create new tab attached to new kernel, launched on localhost.
        """
        kernel_manager = QtKernelManager(
                                shell_address=(LOCALHOST,0 ),
                                sub_address=(LOCALHOST, 0),
                                stdin_address=(LOCALHOST, 0),
                                hb_address=(LOCALHOST, 0),
                                config=self.config
        )
        # start the kernel
        kwargs = dict(ip=LOCALHOST, ipython=not self.pure)
        kwargs['extra_arguments'] = self.kernel_argv
        kernel_manager.start_kernel(**kwargs)
        kernel_manager.start_channels()
        local_kernel = (not False) or self.ip in LOCAL_IPS
        widget = self.widget_factory(config=self.config,
                                   local_kernel=local_kernel)
        widget.kernel_manager = kernel_manager
        widget._existing=False;
        widget._confirm_exit=True;
        widget._may_close=True;
        self.window.add_tab_with_frontend(widget)

    def create_tab_attached_to_current_tab_kernel(self):
        current_widget = self.window.tab_widget.currentWidget()
        current_widget_index = self.window.tab_widget.indexOf(current_widget)
        current_widget.kernel_manager = current_widget.kernel_manager;
        current_widget_name = self.window.tab_widget.tabText(current_widget_index);
        kernel_manager = QtKernelManager(
                                shell_address = current_widget.kernel_manager.shell_address,
                                sub_address = current_widget.kernel_manager.sub_address,
                                stdin_address = current_widget.kernel_manager.stdin_address,
                                hb_address = current_widget.kernel_manager.hb_address,
                                config = self.config
        )
        kernel_manager.start_channels()
        local_kernel = (not self.existing) or self.ip in LOCAL_IPS
        widget = self.widget_factory(config=self.config,
                                   local_kernel=False)
        widget._confirm_exit=True;
        widget._may_close=False;
        widget.kernel_manager = kernel_manager
        self.window.add_tab_with_frontend(widget,name=str('('+current_widget_name+') slave'))

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
        self.widget._existing = self.existing;
        self.widget._may_close = not self.existing;
        self.widget._confirm_exit = not self.existing;

        self.widget.kernel_manager = self.kernel_manager
        self.window = MainWindow(self.app, self.widget, self.existing,
                                may_close=local_kernel,
                                confirm_exit=self.confirm_exit)
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

        self.prev_tab_act = QtGui.QAction("Pre&vious Tab",
            self.window,
            shortcut="Ctrl+PgDown",
            statusTip="Cahange to next tab",
            triggered=self.window.prev_tab)

        self.next_tab_act = QtGui.QAction("Ne&xt Tab",
            self.window,
            shortcut="Ctrl+PgUp",
            statusTip="Cahange to next tab",
            triggered=self.window.next_tab)

        self.fullScreenAct = QtGui.QAction("&Full Screen",
            self.window,
            shortcut="Ctrl+Meta+Space",
            statusTip="Toggle between Fullscreen and Normal Size",
            triggered=self.toggleFullScreen)



        self.tabAndNewKernelAct =QtGui.QAction("Tab with &New kernel",
            self.window,
            shortcut="Ctrl+T",
            triggered=self.create_tab_with_new_frontend)
        self.window.kernel_menu.addAction(self.tabAndNewKernelAct)

        self.tabSameKernalAct =QtGui.QAction("Tab with Sa&me kernel",
            self.window,
            shortcut="Ctrl+Shift+T",
            triggered=self.create_tab_attached_to_current_tab_kernel)
        self.window.kernel_menu.addAction(self.tabSameKernalAct)
        self.window.kernel_menu.addSeparator()

        self.onlineHelpAct = QtGui.QAction("Open Online &Help",
            self.window,
            triggered=self._open_online_help)
        self.window.help_menu.addAction(self.onlineHelpAct)
        # creating shortcut in menubar only for Mac OS as I don't
        # know the shortcut or if the windows manager assign it in
        # other platform.
        if sys.platform == 'darwin':
            self.minimizeAct = QtGui.QAction("Mini&mize",
                self.window,
                shortcut="Ctrl+m",
                statusTip="Minimize the window/Restore Normal Size",
                triggered=self.toggleMinimized)
            self.maximizeAct = QtGui.QAction("Ma&ximize",
                self.window,
                shortcut="Ctrl+Shift+M",
                statusTip="Maximize the window/Restore Normal Size",
                triggered=self.toggleMaximized)


            self.window_menu = self.window.window_menu
            self.kernel_menu = self.window.kernel_menu

            self.kernel_menu.addAction(self.next_tab_act)
            self.kernel_menu.addAction(self.prev_tab_act)
            self.window_menu.addSeparator()
            self.window_menu.addAction(self.minimizeAct)
            self.window_menu.addAction(self.maximizeAct)
            self.window_menu.addSeparator()
            self.window_menu.addAction(self.fullScreenAct)

        else:
            # if we don't put it in a menu, we add it to the window so
            # that it can still be triggerd by shortcut
            self.window.addAction(self.fullScreenAct)

            # Don't activate toggleMenubar on mac, doen't work,
            # as toolbar always here
            self.toggle_menu_bar_act = QtGui.QAction("&Toggle Menu Bar",
                self.window,
                shortcut="Ctrl+Meta+H",
                statusTip="Toggle menubar betwin visible and not",
                triggered=self.toggle_menu_bar)
            self.window_menu.addAction(self.toggle_menu_bar_act)

    def toggle_menu_bar(self):
        menu_bar = self.window.menuBar();
        if not menu_bar.isVisible():
            menu_bar.setVisible(False)
        else:
            menu_bar.setVisible(True)

    def toggleMinimized(self):
        if not self.window.isMinimized():
            self.window.showMinimized()
        else:
            self.window.showNormal()

    def _open_online_help(self):
        filename="http://ipython.org/ipython-doc/stable/index.html"
        webbrowser.open(filename, new=1, autoraise=True)

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

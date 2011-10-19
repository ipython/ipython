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
import uuid
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
                    confirm_exit=True,
                    new_frontend_factory=None, slave_frontend_factory=None,
                ):
        """ Create a tabbed MainWindow for managing IPython FrontendWidgets
        
        Parameters
        ----------
        
        app : reference to QApplication parent
        frontend : IPythonWidget
            The first IPython frontend to start with
        existing : bool, optional
            Whether the first frontend is connected to en existing Kernel,
            or if we own it.
        may_close : bool, optional
            Whether we are permitted to close the kernel (determines close dialog behavior)
        confirm_exit : bool, optional
            Whether we should prompt on close of tabs
        new_frontend_factory : callable
            A callable that returns a new IPythonWidget instance, attached to
            its own running kernel.
        slave_frontend_factory : callable
            A callable that takes an existing IPythonWidget, and  returns a new 
            IPythonWidget instance, attached to the same kernel.
        """

        super(MainWindow, self).__init__()
        self._app = app
        self.new_frontend_factory = new_frontend_factory
        self.slave_frontend_factory = slave_frontend_factory

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
    
    def create_tab_with_new_frontend(self):
        """create a new frontend and attach it to a new tab"""
        widget = self.new_frontend_factory()
        self.add_tab_with_frontend(widget)
    
    def create_tab_with_current_kernel(self):
        """create a new frontend attached to the same kernel as the current tab"""
        current_widget = self.tab_widget.currentWidget()
        current_widget_index = self.tab_widget.indexOf(current_widget)
        current_widget_name = self.tab_widget.tabText(current_widget_index)
        widget = self.slave_frontend_factory(current_widget)
        if 'slave' in current_widget_name:
            # don't keep stacking slaves
            name = current_widget_name
        else:
            name = str('('+current_widget_name+') slave')
        self.add_tab_with_frontend(widget,name=name)

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
                                widget.kernel_manager.connection_file == km.connection_file and
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
                                widget.kernel_manager.connection_file == km.connection_file)
        # Get a list of all widget owning the same kernel and removed it from
        # the previous cadidate. (better using sets ?)
        master_widget_list = self.find_master_tab(tab,as_list=True)
        slave_list = [widget for widget in filtered_widget_list if widget not in master_widget_list]

        return slave_list

    # Populate the menu bar with common actions and shortcuts
    def add_menu_action(self, menu, action):
        """Add action to menu as well as self
        
        So that when the menu bar is invisible, its actions are still available.
        """
        menu.addAction(action)
        self.addAction(action)
    
    def init_menu_bar(self):
        #create menu in the order they should appear in the menu bar
        self.init_file_menu()
        self.init_edit_menu()
        self.init_view_menu()
        self.init_kernel_menu()
        self.init_magic_menu()
        self.init_window_menu()
        self.init_help_menu()
    
    def init_file_menu(self):
        self.file_menu = self.menuBar().addMenu("&File")
        
        self.new_kernel_tab_act = QtGui.QAction("New Tab with &New kernel",
            self,
            shortcut="Ctrl+T",
            triggered=self.create_tab_with_new_frontend)
        self.add_menu_action(self.file_menu, self.new_kernel_tab_act)

        self.slave_kernel_tab_act = QtGui.QAction("New Tab with Sa&me kernel",
            self,
            shortcut="Ctrl+Shift+T",
            triggered=self.create_tab_with_current_kernel)
        self.add_menu_action(self.file_menu, self.slave_kernel_tab_act)
        
        self.file_menu.addSeparator()

        self.close_action=QtGui.QAction("&Close Tab",
            self,
            shortcut="Ctrl+W",
            triggered=self.close_active_frontend
            )
        self.add_menu_action(self.file_menu, self.close_action)

        self.export_action=QtGui.QAction("&Save to HTML/XHTML",
            self,
            shortcut="Ctrl+S",
            triggered=self.export_action_active_frontend
            )
        self.add_menu_action(self.file_menu, self.export_action)

        self.file_menu.addSeparator()
        
        # Ctrl actually maps to Cmd on OSX, which avoids conflict with history
        # action, which is already bound to true Ctrl+P
        print_shortcut = "Ctrl+P" if sys.platform == 'darwin' else 'Ctrl+Shift+P'
        self.print_action = QtGui.QAction("&Print",
            self,
            shortcut=print_shortcut,
            triggered=self.print_action_active_frontend)
        self.add_menu_action(self.file_menu, self.print_action)
        
        if sys.platform == 'darwin':
            # OSX always has Quit in the Application menu, only add it
            # to the File menu elsewhere.

            self.file_menu.addSeparator()

            self.quit_action = QtGui.QAction("&Quit",
                self,
                shortcut=QtGui.QKeySequence.Quit,
                triggered=self.close,
            )
            self.add_menu_action(self.file_menu, self.quit_action)

    
    def init_edit_menu(self):
        self.edit_menu = self.menuBar().addMenu("&Edit")
        
        self.undo_action = QtGui.QAction("&Undo",
            self,
            shortcut="Ctrl+Z",
            statusTip="Undo last action if possible",
            triggered=self.undo_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.undo_action)

        self.redo_action = QtGui.QAction("&Redo",
            self,
            shortcut="Ctrl+Shift+Z",
            statusTip="Redo last action if possible",
            triggered=self.redo_active_frontend)
        self.add_menu_action(self.edit_menu, self.redo_action)

        self.edit_menu.addSeparator()

        self.cut_action = QtGui.QAction("&Cut",
            self,
            shortcut=QtGui.QKeySequence.Cut,
            triggered=self.cut_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.cut_action)

        self.copy_action = QtGui.QAction("&Copy",
            self,
            shortcut=QtGui.QKeySequence.Copy,
            triggered=self.copy_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.copy_action)

        self.copy_raw_action = QtGui.QAction("Copy (&Raw Text)",
            self,
            shortcut="Ctrl+Shift+C",
            triggered=self.copy_raw_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.copy_raw_action)

        self.paste_action = QtGui.QAction("&Paste",
            self,
            shortcut=QtGui.QKeySequence.Paste,
            triggered=self.paste_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.paste_action)

        self.edit_menu.addSeparator()

        self.select_all_action = QtGui.QAction("Select &All",
            self,
            shortcut="Ctrl+A",
            triggered=self.select_all_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.select_all_action)

    
    def init_view_menu(self):
        self.view_menu = self.menuBar().addMenu("&View")

        if sys.platform != 'darwin':
            # disable on OSX, where there is always a menu bar
            self.toggle_menu_bar_act = QtGui.QAction("Toggle &Menu Bar",
                self,
                shortcut="Ctrl+Meta+M",
                statusTip="Toggle visibility of menubar",
                triggered=self.toggle_menu_bar)
            self.add_menu_action(self.view_menu, self.toggle_menu_bar_act)
        
        fs_key = "Ctrl+Meta+F" if sys.platform == 'darwin' else "F11"
        self.full_screen_act = QtGui.QAction("&Full Screen",
            self,
            shortcut=fs_key,
            statusTip="Toggle between Fullscreen and Normal Size",
            triggered=self.toggleFullScreen)
        self.add_menu_action(self.view_menu, self.full_screen_act)

        self.view_menu.addSeparator()

        self.increase_font_size = QtGui.QAction("Zoom &In",
            self,
            shortcut="Ctrl++",
            triggered=self.increase_font_size_active_frontend
            )
        self.add_menu_action(self.view_menu, self.increase_font_size)

        self.decrease_font_size = QtGui.QAction("Zoom &Out",
            self,
            shortcut="Ctrl+-",
            triggered=self.decrease_font_size_active_frontend
            )
        self.add_menu_action(self.view_menu, self.decrease_font_size)

        self.reset_font_size = QtGui.QAction("Zoom &Reset",
            self,
            shortcut="Ctrl+0",
            triggered=self.reset_font_size_active_frontend
            )
        self.add_menu_action(self.view_menu, self.reset_font_size)

        self.view_menu.addSeparator()

        self.clear_action = QtGui.QAction("&Clear Screen",
            self,
            shortcut='Ctrl+L',
            statusTip="Clear the console",
            triggered=self.clear_magic_active_frontend)
        self.add_menu_action(self.view_menu, self.clear_action)
    
    def init_kernel_menu(self):
        self.kernel_menu = self.menuBar().addMenu("&Kernel")
        # Qt on OSX maps Ctrl to Cmd, and Meta to Ctrl
        # keep the signal shortcuts to ctrl, rather than 
        # platform-default like we do elsewhere.

        ctrl = "Meta" if sys.platform == 'darwin' else "Ctrl"

        self.interrupt_kernel_action = QtGui.QAction("Interrupt current Kernel",
            self,
            triggered=self.interrupt_kernel_active_frontend,
            shortcut=ctrl+"+C",
            )
        self.add_menu_action(self.kernel_menu, self.interrupt_kernel_action)

        self.restart_kernel_action = QtGui.QAction("Restart current Kernel",
            self,
            triggered=self.restart_kernel_active_frontend,
            shortcut=ctrl+"+.",
            )
        self.add_menu_action(self.kernel_menu, self.restart_kernel_action)

        self.kernel_menu.addSeparator()

    def init_magic_menu(self):
        self.magic_menu = self.menuBar().addMenu("&Magic")
        self.all_magic_menu = self.magic_menu.addMenu("&All Magics")
        
        self.reset_action = QtGui.QAction("&Reset",
            self,
            statusTip="Clear all varible from workspace",
            triggered=self.reset_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.reset_action)

        self.history_action = QtGui.QAction("&History",
            self,
            statusTip="show command history",
            triggered=self.history_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.history_action)

        self.save_action = QtGui.QAction("E&xport History ",
            self,
            statusTip="Export History as Python File",
            triggered=self.save_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.save_action)

        self.who_action = QtGui.QAction("&Who",
            self,
            statusTip="List interactive variable",
            triggered=self.who_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.who_action)

        self.who_ls_action = QtGui.QAction("Wh&o ls",
            self,
            statusTip="Return a list of interactive variable",
            triggered=self.who_ls_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.who_ls_action)

        self.whos_action = QtGui.QAction("Who&s",
            self,
            statusTip="List interactive variable with detail",
            triggered=self.whos_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.whos_action)
        
        # allmagics submenu:
        
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
    
    def init_window_menu(self):
        self.window_menu = self.menuBar().addMenu("&Window")
        if sys.platform == 'darwin':
            # add min/maximize actions to OSX, which lacks default bindings.
            self.minimizeAct = QtGui.QAction("Mini&mize",
                self,
                shortcut="Ctrl+m",
                statusTip="Minimize the window/Restore Normal Size",
                triggered=self.toggleMinimized)
            # maximize is called 'Zoom' on OSX for some reason
            self.maximizeAct = QtGui.QAction("&Zoom",
                self,
                shortcut="Ctrl+Shift+M",
                statusTip="Maximize the window/Restore Normal Size",
                triggered=self.toggleMaximized)

            self.add_menu_action(self.window_menu, self.minimizeAct)
            self.add_menu_action(self.window_menu, self.maximizeAct)
            self.window_menu.addSeparator()

        prev_key = "Ctrl+Shift+Left" if sys.platform == 'darwin' else "Ctrl+PgDown"
        self.prev_tab_act = QtGui.QAction("Pre&vious Tab",
            self,
            shortcut=prev_key,
            statusTip="Select previous tab",
            triggered=self.prev_tab)
        self.add_menu_action(self.window_menu, self.prev_tab_act)

        next_key = "Ctrl+Shift+Right" if sys.platform == 'darwin' else "Ctrl+PgUp"
        self.next_tab_act = QtGui.QAction("Ne&xt Tab",
            self,
            shortcut=next_key,
            statusTip="Select next tab",
            triggered=self.next_tab)
        self.add_menu_action(self.window_menu, self.next_tab_act)
    
    def init_help_menu(self):
        # please keep the Help menu in Mac Os even if empty. It will
        # automatically contain a search field to search inside menus and
        # please keep it spelled in English, as long as Qt Doesn't support
        # a QAction.MenuRole like HelpMenuRole otherwise it will loose
        # this search field fonctionality

        self.help_menu = self.menuBar().addMenu("&Help")
        

        # Help Menu

        self.intro_active_frontend_action = QtGui.QAction("&Intro to IPython",
            self,
            triggered=self.intro_active_frontend
            )
        self.add_menu_action(self.help_menu, self.intro_active_frontend_action)

        self.quickref_active_frontend_action = QtGui.QAction("IPython &Cheat Sheet",
            self,
            triggered=self.quickref_active_frontend
            )
        self.add_menu_action(self.help_menu, self.quickref_active_frontend_action)

        self.guiref_active_frontend_action = QtGui.QAction("&Qt Console",
            self,
            triggered=self.guiref_active_frontend
            )
        self.add_menu_action(self.help_menu, self.guiref_active_frontend_action)

        self.onlineHelpAct = QtGui.QAction("Open Online &Help",
            self,
            triggered=self._open_online_help)
        self.add_menu_action(self.help_menu, self.onlineHelpAct)

    # minimize/maximize/fullscreen actions:

    def toggle_menu_bar(self):
        menu_bar = self.menuBar();
        if menu_bar.isVisible():
            menu_bar.setVisible(False)
        else:
            menu_bar.setVisible(True)

    def toggleMinimized(self):
        if not self.isMinimized():
            self.showMinimized()
        else:
            self.showNormal()

    def _open_online_help(self):
        filename="http://ipython.org/ipython-doc/stable/index.html"
        webbrowser.open(filename, new=1, autoraise=True)

    def toggleMaximized(self):
        if not self.isMaximized():
            self.showMaximized()
        else:
            self.showNormal()

    # Min/Max imizing while in full screen give a bug
    # when going out of full screen, at least on OSX
    def toggleFullScreen(self):
        if not self.isFullScreen():
            self.showFullScreen()
            if sys.platform == 'darwin':
                self.maximizeAct.setEnabled(False)
                self.minimizeAct.setEnabled(False)
        else:
            self.showNormal()
            if sys.platform == 'darwin':
                self.maximizeAct.setEnabled(True)
                self.minimizeAct.setEnabled(True)

    def close_active_frontend(self):
        self.close_tab(self.active_frontend)

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
    
    def _new_connection_file(self):
        return os.path.join(self.profile_dir.security_dir, 'kernel-%s.json' % uuid.uuid4())

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
        widget._existing=False
        widget._confirm_exit=True
        widget._may_close=True
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
        widget._confirm_exit=True;
        widget._may_close=False;
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
        self.widget._existing = self.existing;
        self.widget._may_close = not self.existing;
        self.widget._confirm_exit = not self.existing;

        self.widget.kernel_manager = self.kernel_manager
        self.window = MainWindow(self.app, self.widget, self.existing,
                                may_close=local_kernel,
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

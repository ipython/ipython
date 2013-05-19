"""The Qt MainWindow for the QtConsole

This is a tabbed pseudo-terminal of IPython sessions, with a menu bar for
common actions.

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
import re
import sys
import webbrowser
from threading import Thread

# System library imports
from IPython.external.qt import QtGui,QtCore

def background(f):
    """call a function in a simple thread, to prevent blocking"""
    t = Thread(target=f)
    t.start()
    return t

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class MainWindow(QtGui.QMainWindow):

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    _magic_menu_dict = {}

    def __init__(self, app,
                    confirm_exit=True,
                    new_frontend_factory=None, slave_frontend_factory=None,
                ):
        """ Create a tabbed MainWindow for managing IPython FrontendWidgets
        
        Parameters
        ----------
        
        app : reference to QApplication parent
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
        self._kernel_counter = 0
        self._app = app
        self.confirm_exit = confirm_exit
        self.new_frontend_factory = new_frontend_factory
        self.slave_frontend_factory = slave_frontend_factory

        self.tab_widget = QtGui.QTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested[int].connect(self.close_tab)

        self.setCentralWidget(self.tab_widget)
        # hide tab bar at first, since we have no tabs:
        self.tab_widget.tabBar().setVisible(False)
        # prevent focus in tab bar
        self.tab_widget.setFocusPolicy(QtCore.Qt.NoFocus)

    def update_tab_bar_visibility(self):
        """ update visibility of the tabBar depending of the number of tab

        0 or 1 tab, tabBar hidden
        2+ tabs, tabBar visible

        send a self.close if number of tab ==0

        need to be called explicitly, or be connected to tabInserted/tabRemoved
        """
        if self.tab_widget.count() <= 1:
            self.tab_widget.tabBar().setVisible(False)
        else:
            self.tab_widget.tabBar().setVisible(True)
        if self.tab_widget.count()==0 :
            self.close()

    @property
    def next_kernel_id(self):
        """constantly increasing counter for kernel IDs"""
        c = self._kernel_counter
        self._kernel_counter += 1
        return c

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
            name = '(%s) slave' % current_widget_name
        self.add_tab_with_frontend(widget,name=name)

    def close_tab(self,current_tab):
        """ Called when you need to try to close a tab.

        It takes the number of the tab to be closed as argument, or a reference
        to the widget inside this tab
        """

        # let's be sure "tab" and "closing widget" are respectively the index
        # of the tab to close and a reference to the frontend to close
        if type(current_tab) is not int :
            current_tab = self.tab_widget.indexOf(current_tab)
        closing_widget=self.tab_widget.widget(current_tab)


        # when trying to be closed, widget might re-send a request to be
        # closed again, but will be deleted when event will be processed. So
        # need to check that widget still exists and skip if not. One example
        # of this is when 'exit' is sent in a slave tab. 'exit' will be
        # re-sent by this function on the master widget, which ask all slave
        # widgets to exit
        if closing_widget==None:
            return

        #get a list of all slave widgets on the same kernel.
        slave_tabs = self.find_slave_widgets(closing_widget)

        keepkernel = None #Use the prompt by default
        if hasattr(closing_widget,'_keep_kernel_on_exit'): #set by exit magic
            keepkernel = closing_widget._keep_kernel_on_exit
            # If signal sent by exit magic (_keep_kernel_on_exit, exist and not None)
            # we set local slave tabs._hidden to True to avoid prompting for kernel
            # restart when they get the signal. and then "forward" the 'exit'
            # to the main window
            if keepkernel is not None:
                for tab in slave_tabs:
                    tab._hidden = True
                if closing_widget in slave_tabs:
                    try :
                        self.find_master_tab(closing_widget).execute('exit')
                    except AttributeError:
                        self.log.info("Master already closed or not local, closing only current tab")
                        self.tab_widget.removeTab(current_tab)
                    self.update_tab_bar_visibility()
                    return

        kernel_client = closing_widget.kernel_client
        kernel_manager = closing_widget.kernel_manager

        if keepkernel is None and not closing_widget._confirm_exit:
            # don't prompt, just terminate the kernel if we own it
            # or leave it alone if we don't
            keepkernel = closing_widget._existing
        if keepkernel is None: #show prompt
            if kernel_client and kernel_client.channels_running:
                title = self.window().windowTitle()
                cancel = QtGui.QMessageBox.Cancel
                okay = QtGui.QMessageBox.Ok
                if closing_widget._may_close:
                    msg = "You are closing the tab : "+'"'+self.tab_widget.tabText(current_tab)+'"'
                    info = "Would you like to quit the Kernel and close all attached Consoles as well?"
                    justthis = QtGui.QPushButton("&No, just this Tab", self)
                    justthis.setShortcut('N')
                    closeall = QtGui.QPushButton("&Yes, close all", self)
                    closeall.setShortcut('Y')
                    # allow ctrl-d ctrl-d exit, like in terminal
                    closeall.setShortcut('Ctrl+D')
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
                            background(slave.kernel_client.stop_channels)
                            self.tab_widget.removeTab(self.tab_widget.indexOf(slave))
                        closing_widget.execute("exit")
                        self.tab_widget.removeTab(current_tab)
                        background(kernel_client.stop_channels)
                    elif reply == 0: # close Console
                        if not closing_widget._existing:
                            # Have kernel: don't quit, just close the tab
                            closing_widget.execute("exit True")
                        self.tab_widget.removeTab(current_tab)
                        background(kernel_client.stop_channels)
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
            self.tab_widget.removeTab(current_tab)
            background(kernel_client.stop_channels)
        else: #close console and kernel (no prompt)
            self.tab_widget.removeTab(current_tab)
            if kernel_client and kernel_client.channels_running:
                for slave in slave_tabs:
                    background(slave.kernel_client.stop_channels)
                    self.tab_widget.removeTab(self.tab_widget.indexOf(slave))
                if kernel_manager:
                    kernel_manager.shutdown_kernel()
                background(kernel_client.stop_channels)
        
        self.update_tab_bar_visibility()

    def add_tab_with_frontend(self,frontend,name=None):
        """ insert a tab with a given frontend in the tab bar, and give it a name

        """
        if not name:
            name = 'kernel %i' % self.next_kernel_id
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
        Try to return the frontend that owns the kernel attached to the given widget/tab.

            Only finds frontend owned by the current application. Selection
            based on port of the kernel might be inaccurate if several kernel
            on different ip use same port number.

            This function does the conversion tabNumber/widget if needed.
            Might return None if no master widget (non local kernel)
            Will crash IPython if more than 1 masterWidget

            When asList set to True, always return a list of widget(s) owning
            the kernel. The list might be empty or containing several Widget.
        """

        #convert from/to int/richIpythonWidget if needed
        if isinstance(tab, int):
            tab = self.tab_widget.widget(tab)
        km=tab.kernel_client

        #build list of all widgets
        widget_list = [self.tab_widget.widget(i) for i in range(self.tab_widget.count())]

        # widget that are candidate to be the owner of the kernel does have all the same port of the curent widget
        # And should have a _may_close attribute
        filtered_widget_list = [ widget for widget in widget_list if
                                widget.kernel_client.connection_file == km.connection_file and
                                hasattr(widget,'_may_close') ]
        # the master widget is the one that may close the kernel
        master_widget= [ widget for widget in filtered_widget_list if widget._may_close]
        if as_list:
            return master_widget
        assert(len(master_widget)<=1 )
        if len(master_widget)==0:
            return None

        return master_widget[0]

    def find_slave_widgets(self,tab):
        """return all the frontends that do not own the kernel attached to the given widget/tab.

            Only find frontends owned by the current application. Selection
            based on connection file of the kernel.

            This function does the conversion tabNumber/widget if needed.
        """
        #convert from/to int/richIpythonWidget if needed
        if isinstance(tab, int):
            tab = self.tab_widget.widget(tab)
        km=tab.kernel_client

        #build list of all widgets
        widget_list = [self.tab_widget.widget(i) for i in range(self.tab_widget.count())]

        # widget that are candidate not to be the owner of the kernel does have all the same port of the curent widget
        filtered_widget_list = ( widget for widget in widget_list if
                                widget.kernel_client.connection_file == km.connection_file)
        # Get a list of all widget owning the same kernel and removed it from
        # the previous cadidate. (better using sets ?)
        master_widget_list = self.find_master_tab(tab, as_list=True)
        slave_list = [widget for widget in filtered_widget_list if widget not in master_widget_list]

        return slave_list

    # Populate the menu bar with common actions and shortcuts
    def add_menu_action(self, menu, action, defer_shortcut=False):
        """Add action to menu as well as self
        
        So that when the menu bar is invisible, its actions are still available.
        
        If defer_shortcut is True, set the shortcut context to widget-only,
        where it will avoid conflict with shortcuts already bound to the
        widgets themselves.
        """
        menu.addAction(action)
        self.addAction(action)

        if defer_shortcut:
            action.setShortcutContext(QtCore.Qt.WidgetShortcut)
    
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
            shortcut=QtGui.QKeySequence.Close,
            triggered=self.close_active_frontend
            )
        self.add_menu_action(self.file_menu, self.close_action)

        self.export_action=QtGui.QAction("&Save to HTML/XHTML",
            self,
            shortcut=QtGui.QKeySequence.Save,
            triggered=self.export_action_active_frontend
            )
        self.add_menu_action(self.file_menu, self.export_action, True)

        self.file_menu.addSeparator()
        
        printkey = QtGui.QKeySequence(QtGui.QKeySequence.Print)
        if printkey.matches("Ctrl+P") and sys.platform != 'darwin':
            # Only override the default if there is a collision.
            # Qt ctrl = cmd on OSX, so the match gets a false positive on OSX.
            printkey = "Ctrl+Shift+P"
        self.print_action = QtGui.QAction("&Print",
            self,
            shortcut=printkey,
            triggered=self.print_action_active_frontend)
        self.add_menu_action(self.file_menu, self.print_action, True)
        
        if sys.platform != 'darwin':
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
            shortcut=QtGui.QKeySequence.Undo,
            statusTip="Undo last action if possible",
            triggered=self.undo_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.undo_action)

        self.redo_action = QtGui.QAction("&Redo",
            self,
            shortcut=QtGui.QKeySequence.Redo,
            statusTip="Redo last action if possible",
            triggered=self.redo_active_frontend)
        self.add_menu_action(self.edit_menu, self.redo_action)

        self.edit_menu.addSeparator()

        self.cut_action = QtGui.QAction("&Cut",
            self,
            shortcut=QtGui.QKeySequence.Cut,
            triggered=self.cut_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.cut_action, True)

        self.copy_action = QtGui.QAction("&Copy",
            self,
            shortcut=QtGui.QKeySequence.Copy,
            triggered=self.copy_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.copy_action, True)

        self.copy_raw_action = QtGui.QAction("Copy (&Raw Text)",
            self,
            shortcut="Ctrl+Shift+C",
            triggered=self.copy_raw_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.copy_raw_action, True)

        self.paste_action = QtGui.QAction("&Paste",
            self,
            shortcut=QtGui.QKeySequence.Paste,
            triggered=self.paste_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.paste_action, True)

        self.edit_menu.addSeparator()
        
        selectall = QtGui.QKeySequence(QtGui.QKeySequence.SelectAll)
        if selectall.matches("Ctrl+A") and sys.platform != 'darwin':
            # Only override the default if there is a collision.
            # Qt ctrl = cmd on OSX, so the match gets a false positive on OSX.
            selectall = "Ctrl+Shift+A"
        self.select_all_action = QtGui.QAction("Select &All",
            self,
            shortcut=selectall,
            triggered=self.select_all_active_frontend
            )
        self.add_menu_action(self.edit_menu, self.select_all_action, True)

    
    def init_view_menu(self):
        self.view_menu = self.menuBar().addMenu("&View")

        if sys.platform != 'darwin':
            # disable on OSX, where there is always a menu bar
            self.toggle_menu_bar_act = QtGui.QAction("Toggle &Menu Bar",
                self,
                shortcut="Ctrl+Shift+M",
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
            shortcut=QtGui.QKeySequence.ZoomIn,
            triggered=self.increase_font_size_active_frontend
            )
        self.add_menu_action(self.view_menu, self.increase_font_size, True)

        self.decrease_font_size = QtGui.QAction("Zoom &Out",
            self,
            shortcut=QtGui.QKeySequence.ZoomOut,
            triggered=self.decrease_font_size_active_frontend
            )
        self.add_menu_action(self.view_menu, self.decrease_font_size, True)

        self.reset_font_size = QtGui.QAction("Zoom &Reset",
            self,
            shortcut="Ctrl+0",
            triggered=self.reset_font_size_active_frontend
            )
        self.add_menu_action(self.view_menu, self.reset_font_size, True)

        self.view_menu.addSeparator()

        self.clear_action = QtGui.QAction("&Clear Screen",
            self,
            shortcut='Ctrl+L',
            statusTip="Clear the console",
            triggered=self.clear_magic_active_frontend)
        self.add_menu_action(self.view_menu, self.clear_action)

        self.pager_menu = self.view_menu.addMenu("&Pager")

        hsplit_action = QtGui.QAction(".. &Horizontal Split",
            self,
            triggered=lambda: self.set_paging_active_frontend('hsplit'))

        vsplit_action = QtGui.QAction(" : &Vertical Split",
            self,
            triggered=lambda: self.set_paging_active_frontend('vsplit'))

        inside_action = QtGui.QAction("   &Inside Pager",
            self,
            triggered=lambda: self.set_paging_active_frontend('inside'))

        self.pager_menu.addAction(hsplit_action)
        self.pager_menu.addAction(vsplit_action)
        self.pager_menu.addAction(inside_action)

    def init_kernel_menu(self):
        self.kernel_menu = self.menuBar().addMenu("&Kernel")
        # Qt on OSX maps Ctrl to Cmd, and Meta to Ctrl
        # keep the signal shortcuts to ctrl, rather than 
        # platform-default like we do elsewhere.

        ctrl = "Meta" if sys.platform == 'darwin' else "Ctrl"

        self.interrupt_kernel_action = QtGui.QAction("&Interrupt current Kernel",
            self,
            triggered=self.interrupt_kernel_active_frontend,
            shortcut=ctrl+"+C",
            )
        self.add_menu_action(self.kernel_menu, self.interrupt_kernel_action)

        self.restart_kernel_action = QtGui.QAction("&Restart current Kernel",
            self,
            triggered=self.restart_kernel_active_frontend,
            shortcut=ctrl+"+.",
            )
        self.add_menu_action(self.kernel_menu, self.restart_kernel_action)

        self.kernel_menu.addSeparator()

        self.confirm_restart_kernel_action = QtGui.QAction("&Confirm kernel restart",
            self,
            checkable=True,
            checked=self.active_frontend.confirm_restart,
            triggered=self.toggle_confirm_restart_active_frontend
            )

        self.add_menu_action(self.kernel_menu, self.confirm_restart_kernel_action)
        self.tab_widget.currentChanged.connect(self.update_restart_checkbox)

    def _make_dynamic_magic(self,magic):
        """Return a function `fun` that will execute `magic` on active frontend.

        Parameters
        ----------
        magic : string
            string that will be executed as is when the returned function is called

        Returns
        -------
        fun : function
            function with no parameters, when called will execute `magic` on the
            current active frontend at call time

        See Also
        --------
        populate_all_magic_menu : generate the "All Magics..." menu

        Notes
        -----
        `fun` executes `magic` in active frontend at the moment it is triggered,
        not the active frontend at the moment it was created.

        This function is mostly used to create the "All Magics..." Menu at run time.
        """
        # need two level nested function to be sure to pass magic
        # to active frontend **at run time**.
        def inner_dynamic_magic():
            self.active_frontend.execute(magic)
        inner_dynamic_magic.__name__ = "dynamics_magic_s"
        return inner_dynamic_magic

    def populate_all_magic_menu(self, display_data=None):
        """Clean "All Magics..." menu and repopulate it with `display_data`

        Parameters
        ----------
        display_data : dict,
            dict of display_data for the magics list.
            Expects json data, as the result of MagicsManager.lsmagic_json()

        """
        for k,v in self._magic_menu_dict.items():
            v.clear()
        self.all_magic_menu.clear()
        
        if not display_data:
            return

        mlist = json.loads(display_data['data'].get('application/json', []))

        for magic in mlist:
            cell = (magic['type'] == 'cell')
            name = magic['name']
            mclass = magic['class']
            if cell :
                prefix='%%'
            else :
                prefix='%'
            magic_menu = self._get_magic_menu(mclass)

            pmagic = '%s%s'%(prefix,name)

            xaction = QtGui.QAction(pmagic,
                self,
                triggered=self._make_dynamic_magic(pmagic)
                )
            magic_menu.addAction(xaction)
            self.all_magic_menu.addAction(xaction)

    def update_all_magic_menu(self):
        """ Update the list of magics in the "All Magics..." Menu

        Request the kernel with the list of available magics and populate the
        menu with the list received back

        """
        self.active_frontend._silent_exec_callback('get_ipython().magics_manager.lsmagic_json()',
                self.populate_all_magic_menu)

    def _get_magic_menu(self,menuidentifier, menulabel=None):
        """return a submagic menu by name, and create it if needed
       
        parameters:
        -----------

        menulabel : str
            Label for the menu

        Will infere the menu name from the identifier at creation if menulabel not given.
        To do so you have too give menuidentifier as a CamelCassedString
        """
        menu = self._magic_menu_dict.get(menuidentifier,None)
        if not menu :
            if not menulabel:
                menulabel = re.sub("([a-zA-Z]+)([A-Z][a-z])","\g<1> \g<2>",menuidentifier)
            menu = QtGui.QMenu(menulabel,self.magic_menu)
            self._magic_menu_dict[menuidentifier]=menu
            self.magic_menu.insertMenu(self.magic_menu_separator,menu)
        return menu


        
    def init_magic_menu(self):
        self.magic_menu = self.menuBar().addMenu("&Magic")
        self.magic_menu_separator = self.magic_menu.addSeparator()
        
        self.all_magic_menu = self._get_magic_menu("AllMagics", menulabel="&All Magics...")

        # This action should usually not appear as it will be cleared when menu
        # is updated at first kernel response. Though, it is necessary when
        # connecting through X-forwarding, as in this case, the menu is not
        # auto updated, SO DO NOT DELETE.
        self.pop = QtGui.QAction("&Update All Magic Menu ",
            self, triggered=self.update_all_magic_menu)
        self.add_menu_action(self.all_magic_menu, self.pop)
        # we need to populate the 'Magic Menu' once the kernel has answer at
        # least once let's do it immediately, but it's assured to works
        self.pop.trigger()

        self.reset_action = QtGui.QAction("&Reset",
            self,
            statusTip="Clear all variables from workspace",
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
            statusTip="List interactive variables",
            triggered=self.who_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.who_action)

        self.who_ls_action = QtGui.QAction("Wh&o ls",
            self,
            statusTip="Return a list of interactive variables",
            triggered=self.who_ls_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.who_ls_action)

        self.whos_action = QtGui.QAction("Who&s",
            self,
            statusTip="List interactive variables with details",
            triggered=self.whos_magic_active_frontend)
        self.add_menu_action(self.magic_menu, self.whos_action)

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

        prev_key = "Ctrl+Shift+Left" if sys.platform == 'darwin' else "Ctrl+PgUp"
        self.prev_tab_act = QtGui.QAction("Pre&vious Tab",
            self,
            shortcut=prev_key,
            statusTip="Select previous tab",
            triggered=self.prev_tab)
        self.add_menu_action(self.window_menu, self.prev_tab_act)

        next_key = "Ctrl+Shift+Right" if sys.platform == 'darwin' else "Ctrl+PgDown"
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
        # a QAction.MenuRole like HelpMenuRole otherwise it will lose
        # this search field functionality

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
        menu_bar = self.menuBar()
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

    def set_paging_active_frontend(self, paging):
        self.active_frontend._set_paging(paging)

    def close_active_frontend(self):
        self.close_tab(self.active_frontend)

    def restart_kernel_active_frontend(self):
        self.active_frontend.request_restart_kernel()

    def interrupt_kernel_active_frontend(self):
        self.active_frontend.request_interrupt_kernel()

    def toggle_confirm_restart_active_frontend(self):
        widget = self.active_frontend
        widget.confirm_restart = not widget.confirm_restart
        self.confirm_restart_kernel_action.setChecked(widget.confirm_restart)

    def update_restart_checkbox(self):
        if self.active_frontend is None:
            return
        widget = self.active_frontend
        self.confirm_restart_kernel_action.setChecked(widget.confirm_restart)

    def cut_active_frontend(self):
        widget = self.active_frontend
        if widget.can_cut():
            widget.cut()

    def copy_active_frontend(self):
        widget = self.active_frontend
        widget.copy()

    def copy_raw_active_frontend(self):
        self.active_frontend._copy_raw_action.trigger()

    def paste_active_frontend(self):
        widget = self.active_frontend
        if widget.can_paste():
            widget.paste()

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
        if self.tab_widget.count() == 0:
            # no tabs, just close
            event.accept()
            return
        # Do Not loop on the widget count as it change while closing
        title = self.window().windowTitle()
        cancel = QtGui.QMessageBox.Cancel
        okay = QtGui.QMessageBox.Ok
        
        if self.confirm_exit:
            if self.tab_widget.count() > 1:
                msg = "Close all tabs, stop all kernels, and Quit?"
            else:
                msg = "Close console, stop kernel, and Quit?"
            info = "Kernels not started here (e.g. notebooks) will be left alone."
            closeall = QtGui.QPushButton("&Quit", self)
            closeall.setShortcut('Q')
            box = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                    title, msg)
            box.setInformativeText(info)
            box.addButton(cancel)
            box.addButton(closeall, QtGui.QMessageBox.YesRole)
            box.setDefaultButton(closeall)
            box.setEscapeButton(cancel)
            pixmap = QtGui.QPixmap(self._app.icon.pixmap(QtCore.QSize(64,64)))
            box.setIconPixmap(pixmap)
            reply = box.exec_()
        else:
            reply = okay
        
        if reply == cancel:
            event.ignore()
            return
        if reply == okay:
            while self.tab_widget.count() >= 1:
                # prevent further confirmations:
                widget = self.active_frontend
                widget._confirm_exit = False
                self.close_tab(widget)
            event.accept()


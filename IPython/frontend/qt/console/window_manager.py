# -*- coding: utf-8 -*-
"""The Qt MainWindow Manager for the QtConsole

Proxy to be able to have only one QApplication dealing with several windows and
be able to pass tabs from one window to another, create windows, keep a
monotonic kernel number etc

"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# stdlib imports
import sys

# System library imports
from IPython.external.qt import QtGui
from IPython.frontend.qt.console.mainwindow import MainWindow

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class WindowManager:

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, app,
                    confirm_exit=True,
                    new_frontend_factory=None,
                    slave_frontend_factory=None,
                    init_widget = None,
                ):
        """Create a MainWindow Manager for managing IPython FrontendWidgets
        
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
        init_widget :  IPython.frontend.qt.console.MainWindow
            Widget used to init the first window

        """
        #TODO : list availlable kernel from secure/kernel
        #TODO : Support init_widget=None ?

        self._kernel_counter = 0
        self._app = app
        self._title = 'IPython'
        self.confirm_exit = confirm_exit
        self.new_frontend_factory = new_frontend_factory
        self.slave_frontend_factory = slave_frontend_factory

        #reference to last detached frontend to be able to reattach it
        self.last_d_frontend = None

        self.windows = []
        win = self._spawn_new_window()
        if not init_widget:
            raise NotImplementedError,"For now you have to build the first widget yourself"
        win.add_tab_with_frontend(init_widget);
        win.show()
        win.raise_()

    @property
    def next_kernel_id(self):
        """constantly increasing counter for kernel IDs"""
        c = self._kernel_counter
        self._kernel_counter += 1
        return c

    @property
    def active_frontend(self):
        """frontmost active frontend across all window
        
        Return the active frontened of the active window if any
        """
        #TODO return none if no window ?
        return self.active_window.active_frontend

    #TODO : support none if no windows ?
    @property
    def active_window(self):
        """return the current active window

        Return the current active window if any, otherwise return the first
        window created
        """
        windows = [w for w in self.windows if w.isActiveWindow()]
        if len(windows) is not 1 :
            print "probleme de longueur (",len(windows),")";
            return self.windows[0]
        else :
            return windows[0]

    def setTitle(self,title):
        self._title = title
        for w in self.windows:
            w.setTitle(self._title)

    def closing_windows(self,win):
	self.windows.remove(win)

    def _spawn_new_window(self):
        """create a new window and return it"""
        win = MainWindow(self._app,
                confirm_exit=self.confirm_exit,
                new_frontend_factory=self.new_frontend_factory,
                slave_frontend_factory=self.slave_frontend_factory,
                windows_manager=self
                )
        win.setTitle(self._title)
        win.init_menu_bar()
        #TODO register closing with removing from self.windows
        self.windows.append(win)
        return win

    def _owning_window(self,frontend):
        """return the window that own the given frontend"""
        for w in self.windows :
            if w.tab_widget.indexOf(frontend) is not -1:
                return w
        return None


    def _move_frontend(self,frontend,toWindow):
        """move taget frontend to given window """
        detach_win = self._owning_window(frontend)
        if detach_win == toWindow or not detach_win :
            #return if already on current window, or if
            #doesn't know how to detach
            return
        current_tab = detach_win.tab_widget.indexOf(frontend)
        tab_name = detach_win.tab_widget.tabText(current_tab)

        detach_win.tab_widget.removeTab(current_tab)
        detach_win.update_tab_bar_visibility()

        toWindow.add_tab_with_frontend(frontend,name=tab_name)


    def detach_frontend(self):
        """detach the current frontend in a new window

        Try to detach the current active frontend.
        Abort if only one frontend in current window

        last frontend to tried to be detached will be the one reattachable
        """
        self.last_d_frontend = self.active_frontend
        if (self.active_window.tab_widget.count() <= 1):
            #don't try to detach if only one
            return
        frontend = self.active_frontend

        win = self._spawn_new_window()
        self._move_frontend(frontend,win)
        win.show()

    def reattach_frontend(self):
        """pull the last widget in current window

        Try to pull the last widget on which detach has been called into the
        current window, don't do anything if last widget has been closed
        """
        if not self.last_d_frontend:
            return
        self._move_frontend(self.last_d_frontend,self.active_window)


    def create_window_with_new_frontend(self):
        """create a new frontend and attach it to a new tab of new window """
        widget = self.new_frontend_factory()
        win = self._spawn_new_window()
        win.add_tab_with_frontend(widget)
        win.show()

    def create_window_with_current_kernel(self):
        """create a slave frontend and attach it to a new tab of new window """
        current_widget = self.active_frontend
        current_widget_index = self.active_window.tab_widget.indexOf(current_widget)
        current_widget_name = self.active_window.tab_widget.tabText(current_widget_index)
        widget = self.slave_frontend_factory(current_widget)
        if 'slave' in current_widget_name:
            # don't keep stacking slaves
            name = current_widget_name
        else:
            name = '(%s) slave' % current_widget_name

        win = self._spawn_new_window()
        win.add_tab_with_frontend(widget,name=name)
        win.show()

    def remove_tab_of_widget(self,frontend):
        """Ask every winows to try to remove a tab with `frontend`"""
        for w in self.windows:
            w.remove_tab_of_widget(frontend)

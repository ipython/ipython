#!/usr/bin/env python
# coding: utf-8
"""
Inputhook management for GUI event loop integration.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import ctypes
import sys

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# Constants for identifying the GUI toolkits.
GUI_WX = 'wx'
GUI_QT = 'qt'
GUI_QT4 = 'qt4'
GUI_GTK = 'gtk'
GUI_TK = 'tk'

#-----------------------------------------------------------------------------
# Utility classes
#-----------------------------------------------------------------------------


class _DummyMainloop(object):
    """A special manager to hijack GUI mainloops that is mostly a no-op.

    We are not using this class currently as it breaks GUI code that calls 
    a mainloop function after the app has started to process pending events.
    """
    def __init__(self, ml, ihm, gui_type):
        self.ml = ml
        self.ihm = ihm
        self.gui_type = gui_type

    def __call__(self, *args, **kw):
        if self.ihm.current_gui() == self.gui_type:
            pass
        else:
            self.ml(*args, **kw)


#-----------------------------------------------------------------------------
# Appstart and spin functions
#-----------------------------------------------------------------------------


def appstart_qt4(app):
    """Start the qt4 event loop in a way that plays with IPython.

    When a qt4 app is run interactively in IPython, the event loop should
    not be started.  This function checks to see if IPython's qt4 integration
    is activated and if so, it passes.  If not, it will call the :meth:`exec_`
    method of the main qt4 app.

    This function should be used by users who want their qt4 scripts to work
    both at the command line and in IPython.  These users should put the 
    following logic at the bottom on their script, after they create a
    :class:`QApplication` instance (called ``app`` here)::

    try:
        from IPython.lib.inputhook import appstart_qt4
        appstart_qt4(app)
    except ImportError:
        app.exec_()
    """
    from PyQt4 import QtCore

    assert isinstance(app, QtCore.QCoreApplication)
    if app is not None:
        if current_gui() == GUI_QT4:
            pass
        else:
            app.exec_()


def appstart_wx(app):
    """Start the wx event loop in a way that plays with IPython.

    When a wx app is run interactively in IPython, the event loop should
    not be started.  This function checks to see if IPython's wx integration
    is activated and if so, it passes.  If not, it will call the 
    :meth:`MainLoop` method of the main qt4 app.

    This function should be used by users who want their wx scripts to work
    both at the command line and in IPython.  These users should put the 
    following logic at the bottom on their script, after they create a
    :class:`App` instance (called ``app`` here)::

    try:
        from IPython.lib.inputhook import appstart_wx
        appstart_wx(app)
    except ImportError:
        app.MainLoop()
    """
    import wx

    assert isinstance(app, wx.App)
    if app is not None:
        if current_gui() == GUI_WX:
            pass
        else:
            app.MainLoop()


def appstart_tk(app):
    """Start the tk event loop in a way that plays with IPython.

    When a tk app is run interactively in IPython, the event loop should
    not be started.  This function checks to see if IPython's tk integration
    is activated and if so, it passes.  If not, it will call the 
    :meth:`mainloop` method of the tk object passed to this method.

    This function should be used by users who want their tk scripts to work
    both at the command line and in IPython.  These users should put the 
    following logic at the bottom on their script, after they create a
    :class:`Tk` instance (called ``app`` here)::

    try:
        from IPython.lib.inputhook import appstart_tk
        appstart_tk(app)
    except ImportError:
        app.mainloop()
    """
    if app is not None:
        if current_gui() == GUI_TK:
            pass
        else:
            app.mainloop()

def appstart_gtk():
    """Start the gtk event loop in a way that plays with IPython.

    When a gtk app is run interactively in IPython, the event loop should
    not be started.  This function checks to see if IPython's gtk integration
    is activated and if so, it passes.  If not, it will call 
    :func:`gtk.main`.  Unlike the other appstart implementations, this does
    not take an ``app`` argument.

    This function should be used by users who want their gtk scripts to work
    both at the command line and in IPython.  These users should put the 
    following logic at the bottom on their script::

    try:
        from IPython.lib.inputhook import appstart_gtk
        appstart_gtk()
    except ImportError:
        gtk.main()
    """
    import gtk
    if current_gui() == GUI_GTK:
        pass
    else:
        gtk.main()

#-----------------------------------------------------------------------------
# Main InputHookManager class
#-----------------------------------------------------------------------------


class InputHookManager(object):
    """Manage PyOS_InputHook for different GUI toolkits.

    This class installs various hooks under ``PyOSInputHook`` to handle
    GUI event loop integration.
    """
    
    def __init__(self):
        self.PYFUNC = ctypes.PYFUNCTYPE(ctypes.c_int)
        self._apps = {}
        self._spinner_dict = {
            GUI_QT4 : self._spin_qt4,
            GUI_WX  : self._spin_wx,
            GUI_GTK : self._spin_gtk,
            GUI_TK  : self._spin_tk}
        self._reset()

    def _reset(self):
        self._callback_pyfunctype = None
        self._callback = None
        self._installed = False
        self._current_gui = None

    def _hijack_wx(self):
        """Hijack the wx mainloop so a user calling it won't cause badness.

        We are not currently using this as it breaks GUI code that calls a 
        mainloop at anytime but startup.
        """
        import wx
        if hasattr(wx, '_core_'): core = getattr(wx, '_core_')
        elif hasattr(wx, '_core'): core = getattr(wx, '_core')
        else: raise AttributeError('Could not find wx core module')
        orig_mainloop = core.PyApp_MainLoop
        core.PyApp_MainLoop = _DummyMainloop
        return orig_mainloop

    def _hijack_qt4(self):
        """Hijack the qt4 mainloop so a user calling it won't cause badness.

        We are not currently using this as it breaks GUI code that calls a 
        mainloop at anytime but startup.
        """
        from PyQt4 import QtGui, QtCore
        orig_mainloop = QtGui.qApp.exec_
        dumb_ml = _DummyMainloop(orig_mainloop, self, GUI_QT4)
        QtGui.qApp.exec_ = dumb_ml
        QtGui.QApplication.exec_ = dumb_ml
        QtCore.QCoreApplication.exec_ = dumb_ml
        return orig_mainloop

    def _hijack_gtk(self):
        """Hijack the gtk mainloop so a user calling it won't cause badness.

        We are not currently using this as it breaks GUI code that calls a 
        mainloop at anytime but startup.
        """
        import gtk
        orig_mainloop = gtk.main
        dumb_ml = _DummyMainloop(orig_mainloop, self, GUI_GTK)
        gtk.mainloop = dumb_ml
        gtk.main = dumb_ml
        return orig_mainloop

    def _hijack_tk(self):
        """Hijack the tk mainloop so a user calling it won't cause badness.

        We are not currently using this as it breaks GUI code that calls a 
        mainloop at anytime but startup.
        """
        import Tkinter
        # FIXME: gtk is not imported here and we shouldn't be using gtk.main!
        orig_mainloop = gtk.main
        dumb_ml = _DummyMainloop(orig_mainloop, self, GUI_TK)
        Tkinter.Misc.mainloop = dumb_ml
        Tkinter.mainloop = dumb_ml

    def _spin_qt4(self):
        """Process all pending events in the qt4 event loop.

        This is for internal IPython use only and user code should not call this.
        Instead, they should issue the raw GUI calls themselves.
        """
        from PyQt4 import QtCore

        app = QtCore.QCoreApplication.instance()
        if app is not None:
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)

    def _spin_wx(self):
        """Process all pending events in the wx event loop.

        This is for internal IPython use only and user code should not call this.
        Instead, they should issue the raw GUI calls themselves.
        """
        import wx
        app = wx.GetApp()
        if app is not None and wx.Thread_IsMain():
            evtloop = wx.EventLoop()
            ea = wx.EventLoopActivator(evtloop)
            while evtloop.Pending():
                evtloop.Dispatch()
            app.ProcessIdle()
            del ea

    def _spin_gtk(self):
        """Process all pending events in the gtk event loop.

        This is for internal IPython use only and user code should not call this.
        Instead, they should issue the raw GUI calls themselves.
        """
        import gtk
        gtk.gdk.threads_enter()
        while gtk.events_pending():
            gtk.main_iteration(False)
        gtk.gdk.flush()
        gtk.gdk.threads_leave()

    def _spin_tk(self):
        """Process all pending events in the tk event loop.

        This is for internal IPython use only and user code should not call this.
        Instead, they should issue the raw GUI calls themselves.
        """
        app = self._apps.get(GUI_TK)
        if app is not None:
            app.update()

    def spin(self):
        """Process pending events in the current gui.

        This method is just provided for IPython to use internally if needed
        for things like testing.  Third party projects should not call this
        method, but instead should call the underlying GUI toolkit methods
        that we are calling.
        """
        spinner = self._spinner_dict.get(self._current_gui, lambda: None)
        spinner()

    def get_pyos_inputhook(self):
        """Return the current PyOS_InputHook as a ctypes.c_void_p."""
        return ctypes.c_void_p.in_dll(ctypes.pythonapi,"PyOS_InputHook")

    def get_pyos_inputhook_as_func(self):
        """Return the current PyOS_InputHook as a ctypes.PYFUNCYPE."""
        return self.PYFUNC.in_dll(ctypes.pythonapi,"PyOS_InputHook")

    def set_inputhook(self, callback):
        """Set PyOS_InputHook to callback and return the previous one."""
        self._callback = callback
        self._callback_pyfunctype = self.PYFUNC(callback)
        pyos_inputhook_ptr = self.get_pyos_inputhook()
        original = self.get_pyos_inputhook_as_func()
        pyos_inputhook_ptr.value = \
            ctypes.cast(self._callback_pyfunctype, ctypes.c_void_p).value
        self._installed = True
        return original

    def clear_inputhook(self, app=None):
        """Set PyOS_InputHook to NULL and return the previous one.

        Parameters
        ----------
        app : optional, ignored
          This parameter is allowed only so that clear_inputhook() can be
          called with a similar interface as all the ``enable_*`` methods.  But
          the actual value of the parameter is ignored.  This uniform interface
          makes it easier to have user-level entry points in the main IPython
          app like :meth:`enable_gui`."""
        pyos_inputhook_ptr = self.get_pyos_inputhook()
        original = self.get_pyos_inputhook_as_func()
        pyos_inputhook_ptr.value = ctypes.c_void_p(None).value
        self._reset()
        return original

    def clear_app_refs(self, gui=None):
        """Clear IPython's internal reference to an application instance.

        Whenever we create an app for a user on qt4 or wx, we hold a
        reference to the app.  This is needed because in some cases bad things
        can happen if a user doesn't hold a reference themselves.  This
        method is provided to clear the references we are holding.

        Parameters
        ----------
        gui : None or str
            If None, clear all app references.  If ('wx', 'qt4') clear
            the app for that toolkit.  References are not held for gtk or tk
            as those toolkits don't have the notion of an app.
        """
        if gui is None:
            self._apps = {}
        elif self._apps.has_key(gui):
            del self._apps[gui]

    def enable_wx(self, app=False):
        """Enable event loop integration with wxPython.

        Parameters
        ----------
        app : bool
            Create a running application object or not.

        Notes
        -----
        This methods sets the ``PyOS_InputHook`` for wxPython, which allows
        the wxPython to integrate with terminal based applications like
        IPython.

        If ``app`` is True, we create an :class:`wx.App` as follows::

            import wx
            app = wx.App(redirect=False, clearSigInt=False)

        Both options this constructor are important for things to work
        properly in an interactive context.

        But, we first check to see if an application has already been 
        created.  If so, we simply return that instance.
        """
        from IPython.lib.inputhookwx import inputhook_wx
        self.set_inputhook(inputhook_wx)
        self._current_gui = GUI_WX
        if app:
            import wx
            app = wx.GetApp()
            if app is None:
                app = wx.App(redirect=False, clearSigInt=False)
                self._apps[GUI_WX] = app
            return app

    def disable_wx(self):
        """Disable event loop integration with wxPython.

        This merely sets PyOS_InputHook to NULL.
        """
        self.clear_inputhook()

    def enable_qt4(self, app=False):
        """Enable event loop integration with PyQt4.
        
        Parameters
        ----------
        app : bool
            Create a running application object or not.

        Notes
        -----
        This methods sets the PyOS_InputHook for PyQt4, which allows
        the PyQt4 to integrate with terminal based applications like
        IPython.

        If ``app`` is True, we create an :class:`QApplication` as follows::

            from PyQt4 import QtCore
            app = QtGui.QApplication(sys.argv)

        But, we first check to see if an application has already been 
        created.  If so, we simply return that instance.
        """
        from PyQt4 import QtCore
        # PyQt4 has had this since 4.3.1.  In version 4.2, PyOS_InputHook
        # was set when QtCore was imported, but if it ever got removed,
        # you couldn't reset it.  For earlier versions we can
        # probably implement a ctypes version.
        try:
            QtCore.pyqtRestoreInputHook()
        except AttributeError:
            pass
        self._current_gui = GUI_QT4
        if app:
            from PyQt4 import QtGui
            app = QtCore.QCoreApplication.instance()
            if app is None:
                app = QtGui.QApplication(sys.argv)
                self._apps[GUI_QT4] = app
            return app

    def disable_qt4(self):
        """Disable event loop integration with PyQt4.

        This merely sets PyOS_InputHook to NULL.
        """
        self.clear_inputhook()

    def enable_gtk(self, app=False):
        """Enable event loop integration with PyGTK.

        Parameters
        ----------
        app : bool
            Create a running application object or not.  Because gtk does't
            have an app class, this does nothing.

        Notes
        -----
        This methods sets the PyOS_InputHook for PyGTK, which allows
        the PyGTK to integrate with terminal based applications like
        IPython.
        """
        import gtk
        try:
            gtk.set_interactive(True)
            self._current_gui = GUI_GTK
        except AttributeError:
            # For older versions of gtk, use our own ctypes version
            from IPython.lib.inputhookgtk import inputhook_gtk
            self.set_inputhook(inputhook_gtk)
            self._current_gui = GUI_GTK

    def disable_gtk(self):
        """Disable event loop integration with PyGTK.
        
        This merely sets PyOS_InputHook to NULL.
        """
        self.clear_inputhook()

    def enable_tk(self, app=False):
        """Enable event loop integration with Tk.

        Parameters
        ----------
        app : bool
            Create a running application object or not.

        Notes
        -----
        Currently this is a no-op as creating a :class:`Tkinter.Tk` object 
        sets ``PyOS_InputHook``.
        """
        self._current_gui = GUI_TK
        if app:
            import Tkinter
            app = Tkinter.Tk()
            app.withdraw()
            self._apps[GUI_TK] = app
            return app

    def disable_tk(self):
        """Disable event loop integration with Tkinter.
        
        This merely sets PyOS_InputHook to NULL.
        """
        self.clear_inputhook()

    def current_gui(self):
        """Return a string indicating the currently active GUI or None."""
        return self._current_gui

inputhook_manager = InputHookManager()

enable_wx = inputhook_manager.enable_wx
disable_wx = inputhook_manager.disable_wx
enable_qt4 = inputhook_manager.enable_qt4
disable_qt4 = inputhook_manager.disable_qt4
enable_gtk = inputhook_manager.enable_gtk
disable_gtk = inputhook_manager.disable_gtk
enable_tk = inputhook_manager.enable_tk
disable_tk = inputhook_manager.disable_tk
clear_inputhook = inputhook_manager.clear_inputhook
set_inputhook = inputhook_manager.set_inputhook
current_gui = inputhook_manager.current_gui
clear_app_refs = inputhook_manager.clear_app_refs
spin = inputhook_manager.spin


# Convenience function to switch amongst them
def enable_gui(gui=None, app=True):
    """Switch amongst GUI input hooks by name.

    This is just a utility wrapper around the methods of the InputHookManager
    object.

    Parameters
    ----------
    gui : optional, string or None
      If None, clears input hook, otherwise it must be one of the recognized
      GUI names (see ``GUI_*`` constants in module).

    app : optional, bool
      If true, create an app object and return it.

    Returns
    -------
    The output of the underlying gui switch routine, typically the actual
    PyOS_InputHook wrapper object or the GUI toolkit app created, if there was
    one.
    """
    guis = {None: clear_inputhook,
            GUI_TK: enable_tk,
            GUI_GTK: enable_gtk,
            GUI_WX: enable_wx,
            GUI_QT: enable_qt4, # qt3 not supported
            GUI_QT4: enable_qt4 }
    try:
        gui_hook = guis[gui]
    except KeyError:
        e="Invalid GUI request %r, valid ones are:%s" % (gui, guis.keys())
        raise ValueError(e)
    return gui_hook(app)

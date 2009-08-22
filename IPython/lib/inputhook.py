#!/usr/bin/env python
# encoding: utf-8
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
# Code
#-----------------------------------------------------------------------------

def _dummy_mainloop(*args, **kw):
    pass


class InputHookManager(object):
    """Manage PyOS_InputHook for different GUI toolkits.

    This class installs various hooks under ``PyOSInputHook`` to handle
    GUI event loop integration.
    """
    
    def __init__(self):
        self.PYFUNC = ctypes.PYFUNCTYPE(ctypes.c_int)
        self._apps = {}
        self._reset()

    def _reset(self):
        self._callback_pyfunctype = None
        self._callback = None
        self._installed = False
        self._current_gui = None

    def _hijack_wx(self):
        import wx
        if hasattr(wx, '_core_'): core = getattr(wx, '_core_')
        elif hasattr(wx, '_core'): core = getattr(wx, '_core')
        else: raise AttributeError('Could not find wx core module')
        orig_mainloop = core.PyApp_MainLoop
        core.PyApp_MainLoop = _dummy_mainloop
        return orig_mainloop

    def _hijack_qt4(self):
        from PyQt4 import QtGui, QtCore
        orig_mainloop = QtGui.qApp.exec_
        QtGui.qApp.exec_ = _dummy_mainloop
        QtGui.QApplication.exec_ = _dummy_mainloop
        QtCore.QCoreApplication.exec_ = _dummy_mainloop
        return orig_mainloop

    def _hijack_gtk(self):
        import gtk
        orig_mainloop = gtk.main
        gtk.mainloop = _dummy_mainloop
        gtk.main = _dummy_mainloop
        return orig_mainloop

    def _hijack_tk(self):
        import Tkinter
        Tkinter.Misc.mainloop = _dummy_mainloop
        Tkinter.mainloop = _dummy_mainloop

    def get_pyos_inputhook(self):
        """Return the current PyOS_InputHook as a ctypes.c_void_p.
        """
        return ctypes.c_void_p.in_dll(ctypes.pythonapi,"PyOS_InputHook")

    def get_pyos_inputhook_as_func(self):
        """Return the current PyOS_InputHook as a ctypes.PYFUNCYPE.
        """
        return self.PYFUNC.in_dll(ctypes.pythonapi,"PyOS_InputHook")

    def set_inputhook(self, callback):
        """Set PyOS_InputHook to callback and return the previous one.
        """
        self._callback = callback
        self._callback_pyfunctype = self.PYFUNC(callback)
        pyos_inputhook_ptr = self.get_pyos_inputhook()
        original = self.get_pyos_inputhook_as_func()
        pyos_inputhook_ptr.value = \
            ctypes.cast(self._callback_pyfunctype, ctypes.c_void_p).value
        self._installed = True
        return original

    def clear_inputhook(self):
        """Set PyOS_InputHook to NULL and return the previous one.
        """
        pyos_inputhook_ptr = self.get_pyos_inputhook()
        original = self.get_pyos_inputhook_as_func()
        pyos_inputhook_ptr.value = ctypes.c_void_p(None).value
        self._reset()
        return original

    def clear_app_refs(self, gui=None):
        """Clear IPython's internal reference to an application instance.

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
        This methods sets the PyOS_InputHook for wxPython, which allows
        the wxPython to integrate with terminal based applications like
        IPython.
        
        Once this has been called, you can use wx interactively by doing::
        
            >>> import wx
            >>> app = wx.App(redirect=False, clearSigInt=False)
        
        Both options this constructor are important for things to work
        properly in an interactive context.
        
        But, *don't start the event loop*.  That is handled automatically by
        PyOS_InputHook.
        """
        from IPython.lib.inputhookwx import inputhook_wx
        self.set_inputhook(inputhook_wx)
        self._current_gui = 'wx'
        self._hijack_wx()
        if app:
            import wx
            app = wx.GetApp()
            if app is None:
                app = wx.App(redirect=False, clearSigInt=False)
                self._apps['wx'] = app
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
        This methods sets the PyOS_InputHook for wxPython, which allows
        the PyQt4 to integrate with terminal based applications like
        IPython.
        
        Once this has been called, you can simply create a QApplication and
        use it.  But, *don't start the event loop*.  That is handled
        automatically by PyOS_InputHook.
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
        self._current_gui = 'qt4'
        self._hijack_qt4()
        if app:
            from PyQt4 import QtGui
            app = QtGui.QApplication.instance()
            if app is None:
                app = QtGui.QApplication(sys.argv)
                self._apps['qt4'] = app
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
            Create a running application object or not.

        Notes
        -----
        This methods sets the PyOS_InputHook for PyGTK, which allows
        the PyGTK to integrate with terminal based applications like
        IPython.
        
        Once this has been called, you can simple create PyGTK objects and
        use them.  But, *don't start the event loop*.  That is handled
        automatically by PyOS_InputHook.
        """
        import gtk
        try:
            gtk.set_interactive(True)
            self._current_gui = 'gtk'
        except AttributeError:
            # For older versions of gtk, use our own ctypes version
            from IPython.lib.inputhookgtk import inputhook_gtk
            self.set_inputhook(inputhook_gtk)
            self._current_gui = 'gtk'
        self._hijack_gtk()

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
        self._current_gui = 'tk'
        self._hijack_tk()

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

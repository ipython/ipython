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

def appstart_qt4():
    from PyQt4 import QtCore, QtGui
    
    app = QtCore.QCoreApplication.instance()
    print 'qtapp:', app
    if app is not None:
        if current_gui() == 'qt4':
            pass
        else:
            app.exec_()
    

class _DummyMainloop(object):
    """A special manager to hijack GUI mainloops that is mostly a no-op.

    This does have, however, special logic.
    """
    def __init__(self, ml, ihm, gui_type):
        self.ml = ml
        self.ihm = ihm
        self.gui_type = gui_type
        
        
    def __call__(self, *args, **kw):
        force = kw.pop('force', False)
        force = False
        if force:
            #print 'forced spin'  # dbg
            self.ml(*args, **kw)
            
        if self.ihm.current_gui() == self.gui_type:
            pass
        else:
            self.ml(*args, **kw)


def spin_qt4():
    from PyQt4 import QtCore, QtGui

    app = QtCore.QCoreApplication.instance()    
    if (app is not None) and (app.thread() == QtCore.QThread.currentThread()):
        ## timer = QtCore.QTimer()
        ## QtCore.QObject.connect(timer,
        ##                        QtCore.SIGNAL('timeout()'),
        ##                        app, 
        ##                        QtCore.SLOT('quit()'))
        ## timer.start(100)
        #QtCore.QCoreApplication.exec_(force=True)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        ##timer.stop()


def spin_wx():
    app = wx.GetApp()
    if app is not None and wx.Thread_IsMain():
        evtloop = wx.EventLoop()
        ea = wx.EventLoopActivator(evtloop)
        while evtloop.Pending():
            evtloop.Dispatch()
        app.ProcessIdle()
        del ea


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
        """Hijack the wx mainloop so a user calling it won't cause badness."""
        import wx
        if hasattr(wx, '_core_'): core = getattr(wx, '_core_')
        elif hasattr(wx, '_core'): core = getattr(wx, '_core')
        else: raise AttributeError('Could not find wx core module')
        orig_mainloop = core.PyApp_MainLoop
        core.PyApp_MainLoop = _DummyMainloop
        return orig_mainloop

    def _hijack_qt4(self):
        """Hijack the qt4 mainloop so a user calling it won't cause badness."""
        from PyQt4 import QtGui, QtCore
        orig_mainloop = QtGui.qApp.exec_
        dumb_ml = _DummyMainloop(orig_mainloop, self, 'qt4')
        QtGui.qApp.exec_ = dumb_ml
        QtGui.QApplication.exec_ = dumb_ml
        QtCore.QCoreApplication.exec_ = dumb_ml
        return orig_mainloop

    def _hijack_gtk(self):
        """Hijack the gtk mainloop so a user calling it won't cause badness."""
        import gtk
        orig_mainloop = gtk.main
        gtk.mainloop = _DummyMainloop
        gtk.main = _DummyMainloop
        return orig_mainloop

    def _hijack_tk(self):
        """Hijack the tk mainloop so a user calling it won't cause badness."""
        import Tkinter
        Tkinter.Misc.mainloop = _DummyMainloop
        Tkinter.mainloop = _DummyMainloop

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

    def clear_inputhook(self):
        """Set PyOS_InputHook to NULL and return the previous one."""
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
        self._current_gui = 'qt4'
        #self._hijack_qt4()
        if app:
            from PyQt4 import QtGui
            app = QtCore.QCoreApplication.instance()
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

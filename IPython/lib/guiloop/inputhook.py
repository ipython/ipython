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

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class InputHookManager(object):
    
    def __init__(self):
        self.PYFUNC = ctypes.PYFUNCTYPE(ctypes.c_int)
        self._reset()

    def _reset(self):
        self._callback_pyfunctype = None
        self._callback = None
        self._installed = False

    def get_pyos_inputhook(self):
        return ctypes.c_void_p.in_dll(ctypes.pythonapi,"PyOS_InputHook")

    def get_pyos_inputhook_as_func(self):
        return self.PYFUNC.in_dll(ctypes.pythonapi,"PyOS_InputHook")

    def set_inputhook(callback):
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
        """Set PyOS_InputHook to NULL and return the previous one."""
        pyos_inputhook_ptr = self.get_pyos_inputhook()
        original = self.get_pyos_inputhook_as_func()
        pyos_inputhook_ptr.value = ctypes.c_void_p(None).value
        self._reset()
        return original

    def enable_wx(self):
        from IPython.lib.guiloop.inputhookwx import inputhook_wx
        self.set_inputhook(inputhook_wx)

    def disable_wx(self):
        self.clear_inputhook()

    def enable_qt4(self):
        from PyQt4 import QtCore
        # PyQt4 has had this since 4.3.1.  In version 4.2, PyOS_InputHook
        # was set when QtCore was imported, but if it ever got removed,
        # you couldn't reset it.  For earlier versions we can
        # probably implement a ctypes version.
        try:
            QtCore.pyqtRestoreInputHook()
        except AttributeError:
            pass

    def disable_qt4(self):
        self.clear_inputhook()

    def enable_gtk(self):
        import gtk
        try:
            gtk.set_interactive(True)
        except AttributeError:
            # For older versions of gtk, use our own ctypes version
            from IPython.lib.guiloop.inputhookgtk import inputhook_gtk
            add_inputhook(inputhook_gtk)

    def disable_gtk(self):
        self.clear_inputhook()

    def enable_tk(self):
        # Creating a Tkinter.Tk object sets PyOS_InputHook()
        pass

    def disable_tk(self):
        self.clear_inputhook()

inputhook_manager = InputHookManager()

enable_wx = inputhook_manager.enable_wx
disable_wx = inputhook_manager.disable_wx
enable_qt4 = inputhook_manager.enable_qt4
disable_qt4 = inputhook_manager.disable_qt4
enable_gtk = inputhook_manager.enable_gtk
disable_gtk = inputhook_manager.disable_gtk

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
import warnings

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# Constants for identifying the GUI toolkits.
GUI_WX = 'wx'
GUI_QT = 'qt'
GUI_QT4 = 'qt4'
GUI_GTK = 'gtk'
GUI_TK = 'tk'
GUI_OSX = 'osx'
GUI_GLUT = 'glut'
GUI_PYGLET = 'pyglet'

#-----------------------------------------------------------------------------
# Utility classes
#-----------------------------------------------------------------------------


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
        self._reset()

    def _reset(self):
        self._callback_pyfunctype = None
        self._callback = None
        self._installed = False
        self._current_gui = None

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

    def enable_wx(self, app=None):
        """Enable event loop integration with wxPython.

        Parameters
        ----------
        app : WX Application, optional.
            Running application to use.  If not given, we probe WX for an
            existing application object, and create a new one if none is found.

        Notes
        -----
        This methods sets the ``PyOS_InputHook`` for wxPython, which allows
        the wxPython to integrate with terminal based applications like
        IPython.

        If ``app`` is not given we probe for an existing one, and return it if
        found.  If no existing app is found, we create an :class:`wx.App` as
        follows::

            import wx
            app = wx.App(redirect=False, clearSigInt=False)
        """
        from IPython.lib.inputhookwx import inputhook_wx
        self.set_inputhook(inputhook_wx)
        self._current_gui = GUI_WX
        import wx
        if app is None:
            app = wx.GetApp()
        if app is None:
            app = wx.App(redirect=False, clearSigInt=False)
        app._in_event_loop = True
        self._apps[GUI_WX] = app
        return app

    def disable_wx(self):
        """Disable event loop integration with wxPython.

        This merely sets PyOS_InputHook to NULL.
        """
        if self._apps.has_key(GUI_WX):
            self._apps[GUI_WX]._in_event_loop = False
        self.clear_inputhook()

    def enable_qt4(self, app=None):
        """Enable event loop integration with PyQt4.
        
        Parameters
        ----------
        app : Qt Application, optional.
            Running application to use.  If not given, we probe Qt for an
            existing application object, and create a new one if none is found.

        Notes
        -----
        This methods sets the PyOS_InputHook for PyQt4, which allows
        the PyQt4 to integrate with terminal based applications like
        IPython.

        If ``app`` is not given we probe for an existing one, and return it if
        found.  If no existing app is found, we create an :class:`QApplication`
        as follows::

            from PyQt4 import QtCore
            app = QtGui.QApplication(sys.argv)
        """
        from IPython.external.qt_for_kernel import QtCore, QtGui

        if 'pyreadline' in sys.modules:
            # see IPython GitHub Issue #281 for more info on this issue
            # Similar intermittent behavior has been reported on OSX,
            # but not consistently reproducible
            warnings.warn("""PyReadline's inputhook can conflict with Qt, causing delays
            in interactive input. If you do see this issue, we recommend using another GUI
            toolkit if you can, or disable readline with the configuration option
            'TerminalInteractiveShell.readline_use=False', specified in a config file or
            at the command-line""",
            RuntimeWarning)
        
        # PyQt4 has had this since 4.3.1.  In version 4.2, PyOS_InputHook
        # was set when QtCore was imported, but if it ever got removed,
        # you couldn't reset it.  For earlier versions we can
        # probably implement a ctypes version.
        try:
            QtCore.pyqtRestoreInputHook()
        except AttributeError:
            pass

        self._current_gui = GUI_QT4
        if app is None:
            app = QtCore.QCoreApplication.instance()
        if app is None:
            app = QtGui.QApplication([" "])
        app._in_event_loop = True
        self._apps[GUI_QT4] = app
        return app

    def disable_qt4(self):
        """Disable event loop integration with PyQt4.

        This merely sets PyOS_InputHook to NULL.
        """
        if self._apps.has_key(GUI_QT4):
            self._apps[GUI_QT4]._in_event_loop = False
        self.clear_inputhook()

    def enable_gtk(self, app=None):
        """Enable event loop integration with PyGTK.

        Parameters
        ----------
        app : ignored
           Ignored, it's only a placeholder to keep the call signature of all
           gui activation methods consistent, which simplifies the logic of
           supporting magics.

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

    def enable_tk(self, app=None):
        """Enable event loop integration with Tk.

        Parameters
        ----------
        app : toplevel :class:`Tkinter.Tk` widget, optional.
            Running toplevel widget to use.  If not given, we probe Tk for an
            existing one, and create a new one if none is found.

        Notes
        -----
        If you have already created a :class:`Tkinter.Tk` object, the only
        thing done by this method is to register with the
        :class:`InputHookManager`, since creating that object automatically
        sets ``PyOS_InputHook``.
        """
        self._current_gui = GUI_TK
        if app is None:
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

    def enable_glut(self, app=None):
        """Enable event loop integration with GLUT.

        Parameters
        ----------
        app : ignored
           Ignored, it's only a placeholder to keep the call signature of all
           gui activation methods consistent, which simplifies the logic of
           supporting magics.

        Notes
        -----

        This methods sets the PyOS_InputHook for GLUT, which allows the GLUT to
        integrate with terminal based applications like IPython. Due to GLUT
        limitations, it is currently not possible to start the event loop
        without first creating a window. You should thus not create another
        window but use instead the created one. See 'gui-glut.py' in the
        docs/examples/lib directory.
        
        The default screen mode is set to:

          glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH

        Script integration
        ------------------

          if glut.glutGetWindow() > 0:
              interactive = True
              glut.glutShowWindow()
          else:
              interactive = False
              glut.glutInit(sys.argv)
              glut.glutInitDisplayMode( glut.GLUT_DOUBLE |
                                        glut.GLUT_RGBA   |
                                        glut.GLUT_DEPTH )
          ...
          if not interactive:
              glut.glutMainLoop()
        """
        # GLUT is quite an old library and it is difficult to ensure proper
        # integration within IPython since original GLUT does not allow to handle
        # events one by one. Instead, it requires for the mainloop to be entered
        # and never returned (there is not even a function to exit he
        # mainloop). Fortunately, there are alternatives such as freeglut
        # (available for linux and windows) and the OSX implementation gives
        # access to a glutCheckLoop() function that blocks itself until a new
        # event is received. This means we have to setup a default timer to
        # ensure we got at least one event that will unblock the function. We set
        # a default timer of 60fps.
        #
        # Furthermore, it is not possible to install these handlers without a
        # window being first created. We choose to make this window invisible and
        # the user is supposed to make it visible when needed (see gui-glut.py in
        # the docs/examples/lib directory). This means that display mode options
        # are set at this level and user won't be able to change them later
        # without modifying the code. This should probably be made available via
        # IPython options system.

        import OpenGL
        OpenGL.ERROR_CHECKING = False
        import OpenGL.GLUT as glut
        import OpenGL.platform as platform
        import time


        # Frame per second : 60
        # Should probably be an IPython option
        glut_fps = 60
        

        # Display mode : double buffeed + rgba + depth
        # Should probably be an IPython option
        glut_display_mode = (glut.GLUT_DOUBLE |
                             glut.GLUT_RGBA   |
                             glut.GLUT_DEPTH)

        glut_interrupted = False

        def display():
            ''' Dummy display function '''
            pass

        def timer(fps):
            # We should normally set the active window to 1 and post a
            # redisplay for each window.  The problem is that we do not know
            # how much active windows we have and there is no function in glut
            # to get that number.
            # glut.glutSetWindow(1)
            glut.glutTimerFunc( int(1000.0/fps), timer, fps)
            glut.glutPostRedisplay()

        def close():
            glut.glutHideWindow()

        glutMainLoopEvent = None
        if sys.platform == 'darwin':
            try:
                glutCheckLoop = platform.createBaseFunction( 
                    'glutCheckLoop', dll=platform.GLUT, resultType=None, 
                    argTypes=[],
                    doc='glutCheckLoop(  ) -> None', 
                    argNames=(),
                    )
            except AttributeError:
                raise RuntimeError(
                    '''Your glut implementation does not allow interactive sessions'''
                    '''Consider installing freeglut.''')
            glutMainLoopEvent = glutCheckLoop
        elif glut.HAVE_FREEGLUT:
            glutMainLoopEvent = glut.glutMainLoopEvent
        else:
            raise RuntimeError(
                '''Your glut implementation does not allow interactive sessions. '''
                '''Consider installing freeglut.''')

        def inputhook_glut():
            """ Process pending GLUT events only. """            

            # We need to protect against a user pressing Control-C when IPython
            # is idle and this is running. We should trap KeyboardInterrupt and
            # pass but it does not seem to work with glutMainLoopEvent.
            # Instead, we setup a signal handler on SIGINT and returns after
            # having restored the default python SIGINT handler.
            import signal
            def handler(signum, frame):
                signal.signal(signal.SIGINT, signal.default_int_handler)
                print '\nKeyboardInterrupt'
                # Need to reprint the prompt at this stage

            signal.signal(signal.SIGINT, handler)

            try:
                glutMainLoopEvent()
            except KeyboardInterrupt: # this catch doesn't work for some reasons...
                pass

            return 0
            
        if not self._apps.has_key(GUI_GLUT):
            glut.glutInit(sys.argv)
            # Display mode should be also an Ipython option since user won't be able
            # to change it later
            glut.glutInitDisplayMode(glut_display_mode)
            glut.glutCreateWindow(sys.argv[0])
            glut.glutHideWindow()
            glut.glutWMCloseFunc(close)
            glut.glutDisplayFunc(display)
            glut.glutTimerFunc( int(1000.0/glut_fps), timer, glut_fps)
        else:
            glut.glutWMCloseFunc(close)
            glut.glutDisplayFunc(display)
            glut.glutTimerFunc( int(1000.0/glut_fps), timer, glut_fps)

        self.set_inputhook(inputhook_glut)
        self._current_gui = GUI_GLUT
        self._apps[GUI_GLUT] = True

    def disable_glut(self):
        """Disable event loop integration with glut.
        
        This sets PyOS_InputHook to NULL and set the display function to a
        dummy one and set the timer to a dummy timer that will be triggered
        very far in the future.
        """
        import signal
        import OpenGL
        OpenGL.ERROR_CHECKING = False
        import OpenGL.GLUT as glut
        import OpenGL.platform as platform

        def timer_none(fps):
            ''' Dummy timer function '''
            pass

        glutMainLoopEvent = None
        if sys.platform == 'darwin':
            try:
                glutCheckLoop = platform.createBaseFunction(
                    'glutCheckLoop', dll=platform.GLUT, resultType=None,
                    argTypes=[],
                    doc='glutCheckLoop(  ) -> None',
                    argNames=(),
                    )
            except AttributeError:
                raise RuntimeError(
                    '''Your glut implementation does not allow interactive sessions'''
                    '''Consider installing freeglut.''')
            glutMainLoopEvent = glutCheckLoop
        elif glut.HAVE_FREEGLUT:
            glutMainLoopEvent = glut.glutMainLoopEvent
        else:
            raise RuntimeError(
                '''Your glut implementation does not allow interactive sessions. '''
                '''Consider installing freeglut.''')

        glut.glutHideWindow() # This is an event to be processed below
        glutMainLoopEvent()
        #glut.glutTimerFunc( sys.maxint-1, timer_none, 0)
        self.clear_inputhook()
        #signal.signal(signal.SIGINT, signal.default_int_handler)

    def enable_pyglet(self, app=None):
        """Enable event loop integration with pyglet.

        Parameters
        ----------
        app : ignored
           Ignored, it's only a placeholder to keep the call signature of all
           gui activation methods consistent, which simplifies the logic of
           supporting magics.

        Notes
        -----
        This methods sets the ``PyOS_InputHook`` for pyglet, which allows
        pyglet to integrate with terminal based applications like
        IPython.

        """
        import pyglet
        from IPython.lib.inputhookpyglet import inputhook_pyglet
        self.set_inputhook(inputhook_pyglet)
        self._current_gui = GUI_PYGLET
        return app

    def disable_pyglet(self):
        """Disable event loop integration with pyglet.

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
enable_glut = inputhook_manager.enable_glut
disable_glut = inputhook_manager.disable_glut
enable_pyglet = inputhook_manager.enable_pyglet
disable_pyglet = inputhook_manager.disable_pyglet
clear_inputhook = inputhook_manager.clear_inputhook
set_inputhook = inputhook_manager.set_inputhook
current_gui = inputhook_manager.current_gui
clear_app_refs = inputhook_manager.clear_app_refs


# Convenience function to switch amongst them
def enable_gui(gui=None, app=None):
    """Switch amongst GUI input hooks by name.

    This is just a utility wrapper around the methods of the InputHookManager
    object.

    Parameters
    ----------
    gui : optional, string or None
      If None, clears input hook, otherwise it must be one of the recognized
      GUI names (see ``GUI_*`` constants in module).

    app : optional, existing application object.
      For toolkits that have the concept of a global app, you can supply an
      existing one.  If not given, the toolkit will be probed for one, and if
      none is found, a new one will be created.  Note that GTK does not have
      this concept, and passing an app if `gui`=="GTK" will raise an error.

    Returns
    -------
    The output of the underlying gui switch routine, typically the actual
    PyOS_InputHook wrapper object or the GUI toolkit app created, if there was
    one.
    """
    guis = {None: clear_inputhook,
            GUI_OSX: lambda app=False: None,
            GUI_TK: enable_tk,
            GUI_GTK: enable_gtk,
            GUI_WX: enable_wx,
            GUI_QT: enable_qt4, # qt3 not supported
            GUI_QT4: enable_qt4,
            GUI_GLUT: enable_glut,
            GUI_PYGLET: enable_pyglet,
            }
    try:
        gui_hook = guis[gui]
    except KeyError:
        e = "Invalid GUI request %r, valid ones are:%s" % (gui, guis.keys())
        raise ValueError(e)
    return gui_hook(app)


# -*- coding: utf-8 -*-
"""
Qt4's inputhook support function

Author: Christian Boos
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.interactiveshell import InteractiveShell
from IPython.external.qt_for_kernel import QtCore, QtGui
from IPython.lib.inputhook import allow_CTRL_C, ignore_CTRL_C, stdin_ready

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def create_inputhook_qt4(mgr, app=None):
    """Create an input hook for running the Qt4 application event loop.

    Parameters
    ----------
    mgr : an InputHookManager

    app : Qt Application, optional.
        Running application to use.  If not given, we probe Qt for an
        existing application object, and create a new one if none is found.

    Returns
    -------
    A pair consisting of a Qt Application (either the one given or the
    one found or created) and a inputhook.

    Notes
    -----
    We use a custom input hook instead of PyQt4's default one, as it
    interacts better with the readline packages (issue #481).

    The inputhook function works in tandem with a 'pre_prompt_hook'
    which automatically restores the hook as an inputhook in case the
    latter has been temporarily disabled after having intercepted a
    KeyboardInterrupt.
    """

    if app is None:
        app = QtCore.QCoreApplication.instance()
        if app is None:
            app = QtGui.QApplication([" "])

    # Re-use previously created inputhook if any
    ip = InteractiveShell.instance()
    if hasattr(ip, '_inputhook_qt4'):
        return app, ip._inputhook_qt4

    # Otherwise create the inputhook_qt4/preprompthook_qt4 pair of
    # hooks (they both share the got_kbdint flag)

    got_kbdint = [False]

    def inputhook_qt4():
        """PyOS_InputHook python hook for Qt4.

        Process pending Qt events and if there's no pending keyboard
        input, spend a short slice of time (50ms) running the Qt event
        loop.

        As a Python ctypes callback can't raise an exception, we catch
        the KeyboardInterrupt and temporarily deactivate the hook,
        which will let a *second* CTRL+C be processed normally and go
        back to a clean prompt line.
        """
        try:
            allow_CTRL_C()
            app = QtCore.QCoreApplication.instance()
            if not app: # shouldn't happen, but safer if it happens anyway...
                return 0
            app.processEvents(QtCore.QEventLoop.AllEvents, 300)
            if not stdin_ready():
                # Generally a program would run QCoreApplication::exec()
                # from main() to enter and process the Qt event loop until
                # quit() or exit() is called and the program terminates.
                #
                # For our input hook integration, we need to repeatedly
                # enter and process the Qt event loop for only a short
                # amount of time (say 50ms) to ensure that Python stays
                # responsive to other user inputs.
                #
                # A naive approach would be to repeatedly call
                # QCoreApplication::exec(), using a timer to quit after a
                # short amount of time. Unfortunately, QCoreApplication
                # emits an aboutToQuit signal before stopping, which has
                # the undesirable effect of closing all modal windows.
                #
                # To work around this problem, we instead create a
                # QEventLoop and call QEventLoop::exec(). Other than
                # setting some state variables which do not seem to be
                # used anywhere, the only thing QCoreApplication adds is
                # the aboutToQuit signal which is precisely what we are
                # trying to avoid.
                timer = QtCore.QTimer()
                event_loop = QtCore.QEventLoop()
                timer.timeout.connect(event_loop.quit)
                while not stdin_ready():
                    timer.start(50)
                    event_loop.exec_()
                    timer.stop()
        except KeyboardInterrupt:
            ignore_CTRL_C()
            got_kbdint[0] = True
            print("\nKeyboardInterrupt - Ctrl-C again for new prompt")
            mgr.clear_inputhook()
        except: # NO exceptions are allowed to escape from a ctypes callback
            ignore_CTRL_C()
            from traceback import print_exc
            print_exc()
            print("Got exception from inputhook_qt4, unregistering.")
            mgr.clear_inputhook()
        finally:
            allow_CTRL_C()
        return 0

    def preprompthook_qt4(ishell):
        """'pre_prompt_hook' used to restore the Qt4 input hook

        (in case the latter was temporarily deactivated after a
        CTRL+C)
        """
        if got_kbdint[0]:
            mgr.set_inputhook(inputhook_qt4)
        got_kbdint[0] = False

    ip._inputhook_qt4 = inputhook_qt4
    ip.set_hook('pre_prompt_hook', preprompthook_qt4)

    return app, inputhook_qt4

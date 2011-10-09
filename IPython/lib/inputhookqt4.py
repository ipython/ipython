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

from IPython.core import ipapi
from IPython.external.qt_for_kernel import QtCore, QtGui
from IPython.lib.inputhook import stdin_ready

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
    The inputhook function works in tandem with a 'pre_prompt_hook'
    which automatically restores the hook as an inputhook in case the
    latter has been temporarily disabled after having intercepted a
    KeyboardInterrupt.
    """
    if app is None:
        app = QtCore.QCoreApplication.instance()
        if app is None:
            app = QtGui.QApplication([" "])

    # Always use a custom input hook instead of PyQt4's default
    # one, as it interacts better with readline packages (issue
    # #481).

    # Note that we can't let KeyboardInterrupt escape from that
    # hook, as no exception can be raised from within a ctypes
    # python callback. We need to make a compromise: a trapped
    # KeyboardInterrupt will temporarily disable the input hook
    # until we start over with a new prompt line with a second
    # CTRL+C.

    got_kbdint = [False]

    def inputhook_qt4():
        try:
            app.processEvents(QtCore.QEventLoop.AllEvents, 300)
            if not stdin_ready():
                timer = QtCore.QTimer()
                timer.timeout.connect(app.quit)
                while not stdin_ready():
                    timer.start(50)
                    app.exec_()
                    timer.stop()
        except KeyboardInterrupt:
            got_kbdint[0] = True
            mgr.clear_inputhook()
            print("\n(event loop interrupted - "
                  "hit CTRL+C again to clear the prompt)")
        return 0

    def preprompthook_qt4(ishell):
        if got_kbdint[0]:
            mgr.set_inputhook(inputhook_qt4)
    ipapi.get().set_hook('pre_prompt_hook', preprompthook_qt4)

    return app, inputhook_qt4

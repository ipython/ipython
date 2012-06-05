# encoding: utf-8
"""Event loop integration for the ZeroMQ-based kernels.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team

#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys

# System library imports.
import zmq

# Local imports.
from IPython.config.application import Application
from IPython.utils import io


#------------------------------------------------------------------------------
# Eventloops for integrating the Kernel into different GUIs
#------------------------------------------------------------------------------

def loop_qt4(kernel):
    """Start a kernel with PyQt4 event loop integration."""

    from IPython.external.qt_for_kernel import QtCore
    from IPython.lib.guisupport import get_app_qt4, start_event_loop_qt4

    kernel.app = get_app_qt4([" "])
    kernel.app.setQuitOnLastWindowClosed(False)
    kernel.timer = QtCore.QTimer()
    kernel.timer.timeout.connect(kernel.do_one_iteration)
    # Units for the timer are in milliseconds
    kernel.timer.start(1000*kernel._poll_interval)
    start_event_loop_qt4(kernel.app)


def loop_wx(kernel):
    """Start a kernel with wx event loop support."""

    import wx
    from IPython.lib.guisupport import start_event_loop_wx

    doi = kernel.do_one_iteration
     # Wx uses milliseconds
    poll_interval = int(1000*kernel._poll_interval)

    # We have to put the wx.Timer in a wx.Frame for it to fire properly.
    # We make the Frame hidden when we create it in the main app below.
    class TimerFrame(wx.Frame):
        def __init__(self, func):
            wx.Frame.__init__(self, None, -1)
            self.timer = wx.Timer(self)
            # Units for the timer are in milliseconds
            self.timer.Start(poll_interval)
            self.Bind(wx.EVT_TIMER, self.on_timer)
            self.func = func

        def on_timer(self, event):
            self.func()

    # We need a custom wx.App to create our Frame subclass that has the
    # wx.Timer to drive the ZMQ event loop.
    class IPWxApp(wx.App):
        def OnInit(self):
            self.frame = TimerFrame(doi)
            self.frame.Show(False)
            return True

    # The redirect=False here makes sure that wx doesn't replace
    # sys.stdout/stderr with its own classes.
    kernel.app = IPWxApp(redirect=False)

    # The import of wx on Linux sets the handler for signal.SIGINT
    # to 0.  This is a bug in wx or gtk.  We fix by just setting it
    # back to the Python default.
    import signal
    if not callable(signal.getsignal(signal.SIGINT)):
        signal.signal(signal.SIGINT, signal.default_int_handler)

    start_event_loop_wx(kernel.app)


def loop_tk(kernel):
    """Start a kernel with the Tk event loop."""

    import Tkinter
    doi = kernel.do_one_iteration
    # Tk uses milliseconds
    poll_interval = int(1000*kernel._poll_interval)
    # For Tkinter, we create a Tk object and call its withdraw method.
    class Timer(object):
        def __init__(self, func):
            self.app = Tkinter.Tk()
            self.app.withdraw()
            self.func = func

        def on_timer(self):
            self.func()
            self.app.after(poll_interval, self.on_timer)

        def start(self):
            self.on_timer()  # Call it once to get things going.
            self.app.mainloop()

    kernel.timer = Timer(doi)
    kernel.timer.start()


def loop_gtk(kernel):
    """Start the kernel, coordinating with the GTK event loop"""
    from .gui.gtkembed import GTKEmbed

    gtk_kernel = GTKEmbed(kernel)
    gtk_kernel.start()


def loop_cocoa(kernel):
    """Start the kernel, coordinating with the Cocoa CFRunLoop event loop
    via the matplotlib MacOSX backend.
    """
    import matplotlib
    if matplotlib.__version__ < '1.1.0':
        kernel.log.warn(
        "MacOSX backend in matplotlib %s doesn't have a Timer, "
        "falling back on Tk for CFRunLoop integration.  Note that "
        "even this won't work if Tk is linked against X11 instead of "
        "Cocoa (e.g. EPD).  To use the MacOSX backend in the kernel, "
        "you must use matplotlib >= 1.1.0, or a native libtk."
        )
        return loop_tk(kernel)
    
    from matplotlib.backends.backend_macosx import TimerMac, show

    # scale interval for sec->ms
    poll_interval = int(1000*kernel._poll_interval)

    real_excepthook = sys.excepthook
    def handle_int(etype, value, tb):
        """don't let KeyboardInterrupts look like crashes"""
        if etype is KeyboardInterrupt:
            io.raw_print("KeyboardInterrupt caught in CFRunLoop")
        else:
            real_excepthook(etype, value, tb)

    # add doi() as a Timer to the CFRunLoop
    def doi():
        # restore excepthook during IPython code
        sys.excepthook = real_excepthook
        kernel.do_one_iteration()
        # and back:
        sys.excepthook = handle_int

    t = TimerMac(poll_interval)
    t.add_callback(doi)
    t.start()

    # but still need a Poller for when there are no active windows,
    # during which time mainloop() returns immediately
    poller = zmq.Poller()
    if kernel.control_stream:
        poller.register(kernel.control_stream.socket, zmq.POLLIN)
    for stream in kernel.shell_streams:
        poller.register(stream.socket, zmq.POLLIN)

    while True:
        try:
            # double nested try/except, to properly catch KeyboardInterrupt
            # due to pyzmq Issue #130
            try:
                # don't let interrupts during mainloop invoke crash_handler:
                sys.excepthook = handle_int
                show.mainloop()
                sys.excepthook = real_excepthook
                # use poller if mainloop returned (no windows)
                # scale by extra factor of 10, since it's a real poll
                poller.poll(10*poll_interval)
                kernel.do_one_iteration()
            except:
                raise
        except KeyboardInterrupt:
            # Ctrl-C shouldn't crash the kernel
            io.raw_print("KeyboardInterrupt caught in kernel")
        finally:
            # ensure excepthook is restored
            sys.excepthook = real_excepthook

# mapping of keys to loop functions
loop_map = {
    'qt' : loop_qt4,
    'qt4': loop_qt4,
    'inline': None,
    'osx': loop_cocoa,
    'wx' : loop_wx,
    'tk' : loop_tk,
    'gtk': loop_gtk,
    None : None,
}


def enable_gui(gui, kernel=None):
    """Enable integration with a given GUI"""
    if gui not in loop_map:
        raise ValueError("GUI %r not supported" % gui)
    if kernel is None:
        if Application.initialized():
            kernel = getattr(Application.instance(), 'kernel', None)
        if kernel is None:
            raise RuntimeError("You didn't specify a kernel,"
                " and no IPython Application with a kernel appears to be running."
            )
    loop = loop_map[gui]
    if kernel.eventloop is not None and kernel.eventloop is not loop:
        raise RuntimeError("Cannot activate multiple GUI eventloops")
    kernel.eventloop = loop

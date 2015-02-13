# encoding: utf-8
"""Event loop integration for the ZeroMQ-based kernels."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys

import zmq

from IPython.config.application import Application
from IPython.utils import io


def _on_os_x_10_9():
    import platform
    from distutils.version import LooseVersion as V
    return sys.platform == 'darwin' and V(platform.mac_ver()[0]) >= V('10.9')

def _notify_stream_qt(kernel, stream):
    
    from IPython.external.qt_for_kernel import QtCore
    
    if _on_os_x_10_9() and kernel._darwin_app_nap:
        from IPython.external.appnope import nope_scope as context
    else:
        from IPython.core.interactiveshell import NoOpContext as context

    def process_stream_events():
        while stream.getsockopt(zmq.EVENTS) & zmq.POLLIN:
            with context():
                kernel.do_one_iteration()
    
    fd = stream.getsockopt(zmq.FD)
    notifier = QtCore.QSocketNotifier(fd, QtCore.QSocketNotifier.Read, kernel.app)
    notifier.activated.connect(process_stream_events)

# mapping of keys to loop functions
loop_map = {
    'inline': None,
    'nbagg': None,
    'notebook': None,
    None : None,
}

def register_integration(*toolkitnames):
    """Decorator to register an event loop to integrate with the IPython kernel
    
    The decorator takes names to register the event loop as for the %gui magic.
    You can provide alternative names for the same toolkit.
    
    The decorated function should take a single argument, the IPython kernel
    instance, arrange for the event loop to call ``kernel.do_one_iteration()``
    at least every ``kernel._poll_interval`` seconds, and start the event loop.
    
    :mod:`IPython.kernel.zmq.eventloops` provides and registers such functions
    for a few common event loops.
    """
    def decorator(func):
        for name in toolkitnames:
            loop_map[name] = func
        return func
    
    return decorator


@register_integration('qt', 'qt4')
def loop_qt4(kernel):
    """Start a kernel with PyQt4 event loop integration."""

    from IPython.lib.guisupport import get_app_qt4, start_event_loop_qt4

    kernel.app = get_app_qt4([" "])
    kernel.app.setQuitOnLastWindowClosed(False)
    
    for s in kernel.shell_streams:
        _notify_stream_qt(kernel, s)
    
    start_event_loop_qt4(kernel.app)

@register_integration('qt5')
def loop_qt5(kernel):
    """Start a kernel with PyQt5 event loop integration."""
    os.environ['QT_API'] = 'pyqt5'
    return loop_qt4(kernel)


@register_integration('wx')
def loop_wx(kernel):
    """Start a kernel with wx event loop support."""

    import wx
    from IPython.lib.guisupport import start_event_loop_wx
    
    if _on_os_x_10_9() and kernel._darwin_app_nap:
        # we don't hook up App Nap contexts for Wx,
        # just disable it outright.
        from IPython.external.appnope import nope
        nope()

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


@register_integration('tk')
def loop_tk(kernel):
    """Start a kernel with the Tk event loop."""

    try:
        from tkinter import Tk  # Py 3
    except ImportError:
        from Tkinter import Tk  # Py 2
    doi = kernel.do_one_iteration
    # Tk uses milliseconds
    poll_interval = int(1000*kernel._poll_interval)
    # For Tkinter, we create a Tk object and call its withdraw method.
    class Timer(object):
        def __init__(self, func):
            self.app = Tk()
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


@register_integration('gtk')
def loop_gtk(kernel):
    """Start the kernel, coordinating with the GTK event loop"""
    from .gui.gtkembed import GTKEmbed

    gtk_kernel = GTKEmbed(kernel)
    gtk_kernel.start()


@register_integration('gtk3')
def loop_gtk3(kernel):
    """Start the kernel, coordinating with the GTK event loop"""
    from .gui.gtk3embed import GTKEmbed

    gtk_kernel = GTKEmbed(kernel)
    gtk_kernel.start()


@register_integration('osx')
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



def enable_gui(gui, kernel=None):
    """Enable integration with a given GUI"""
    if gui not in loop_map:
        e = "Invalid GUI request %r, valid ones are:%s" % (gui, loop_map.keys())
        raise ValueError(e)
    if kernel is None:
        if Application.initialized():
            kernel = getattr(Application.instance(), 'kernel', None)
        if kernel is None:
            raise RuntimeError("You didn't specify a kernel,"
                " and no IPython Application with a kernel appears to be running."
            )
    loop = loop_map[gui]
    if loop and kernel.eventloop is not None and kernel.eventloop is not loop:
        raise RuntimeError("Cannot activate multiple GUI eventloops")
    kernel.eventloop = loop

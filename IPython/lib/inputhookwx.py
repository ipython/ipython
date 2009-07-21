#!/usr/bin/env python
# encoding: utf-8

"""
Enable wxPython to be used interacive by setting PyOS_InputHook.

Authors:  Robin Dunn, Brian Granger, Ondrej Certik
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

import os
import sys
import time
from timeit import default_timer as clock
import wx

if os.name == 'posix':
    import select
elif sys.platform == 'win32':
    import msvcrt

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def stdin_ready():
    if os.name == 'posix':
        infds, outfds, erfds = select.select([sys.stdin],[],[],0)
        if infds:
            return True
        else:
            return False
    elif sys.platform == 'win32':
        return msvcrt.kbhit()


def inputhook_wx1():
    """Run the wx event loop by processing pending events only.
    
    This approach seems to work, but its performance is not great as it 
    relies on having PyOS_InputHook called regularly.
    """
    app = wx.GetApp()
    if app is not None:
        assert wx.Thread_IsMain()

        # Make a temporary event loop and process system events until
        # there are no more waiting, then allow idle events (which
        # will also deal with pending or posted wx events.)
        evtloop = wx.EventLoop()
        ea = wx.EventLoopActivator(evtloop)
        while evtloop.Pending():
            evtloop.Dispatch()
        app.ProcessIdle()
        del ea
    return 0

class EventLoopTimer(wx.Timer):

    def __init__(self, func):
        self.func = func
        wx.Timer.__init__(self)

    def Notify(self):
        self.func()

class EventLoopRunner(object):

    def Run(self, time):
        self.evtloop = wx.EventLoop()
        self.timer = EventLoopTimer(self.check_stdin)
        self.timer.Start(time)
        self.evtloop.Run()

    def check_stdin(self):
        if stdin_ready():
            self.timer.Stop()
            self.evtloop.Exit()

def inputhook_wx2():
    """Run the wx event loop, polling for stdin.
    
    This version runs the wx eventloop for an undetermined amount of time,
    during which it periodically checks to see if anything is ready on
    stdin.  If anything is ready on stdin, the event loop exits.
    
    The argument to elr.Run controls how often the event loop looks at stdin.
    This determines the responsiveness at the keyboard.  A setting of 1000
    enables a user to type at most 1 char per second.  I have found that a
    setting of 10 gives good keyboard response.  We can shorten it further, 
    but eventually performance would suffer from calling select/kbhit too 
    often.
    """
    app = wx.GetApp()
    if app is not None:
        assert wx.Thread_IsMain()
        elr = EventLoopRunner()
        # As this time is made shorter, keyboard response improves, but idle
        # CPU load goes up.  10 ms seems like a good compromise.
        elr.Run(time=10)  # CHANGE time here to control polling interval
    return 0

def inputhook_wx3():
    """Run the wx event loop by processing pending events only.
    
    This is like inputhook_wx1, but it keeps processing pending events
    until stdin is ready.  After processing all pending events, a call to 
    time.sleep is inserted.  This is needed, otherwise, CPU usage is at 100%.
    This sleep time should be tuned though for best performance.
    """
    app = wx.GetApp()
    if app is not None:
        assert wx.Thread_IsMain()

        evtloop = wx.EventLoop()
        ea = wx.EventLoopActivator(evtloop)
        t = clock()
        while not stdin_ready():
            while evtloop.Pending():
                t = clock()
                evtloop.Dispatch()
            app.ProcessIdle()
            # We need to sleep at this point to keep the idle CPU load
            # low.  However, if sleep to long, GUI response is poor.  As 
            # a compromise, we watch how often GUI events are being processed
            # and switch between a short and long sleep time.  Here are some
            # stats useful in helping to tune this.
            # time    CPU load
            # 0.001   13%
            # 0.005   3%
            # 0.01    1.5%
            # 0.05    0.5%            
            if clock()-t > 0.1:
                # Few GUI events coming in, so we can sleep longer
                time.sleep(0.05)
            else:
                # Many GUI events coming in, so sleep only very little
                time.sleep(0.001)
        del ea
    return 0

# This is our default implementation
inputhook_wx = inputhook_wx3
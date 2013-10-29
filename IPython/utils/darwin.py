# encoding: utf-8
"""Utilities for working on darwin platforms (OS X)"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import platform
import sys
from distutils.version import LooseVersion as V

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

def on_10_9():
    """Are we on OS X 10.9 or greater?"""
    vs = platform.mac_ver()[0]
    if not vs:
        return False
    if V(vs) >= V('10.9'):
        return True
    return False

def disable_app_nap(log=None):
    """Disable OS X 10.9 App Nap energy saving feature
    
    App Nap can cause problems with interactivity when using GUI eventloops
    in the Kernel, and possibly in other scenarios as well.
    
    Returns the NSActivity object, which can be used to end the condition
    via ``NSProcessInfo.endActivity_(activity)``.
    """
    
    if sys.platform != 'darwin' or not on_10_9():
        return
    
    try:
        from Foundation import NSProcessInfo
    except ImportError:
        if log is not None:
            log("Could not import NSProcessInfo."
                " PyObjC is needed to disable App Nap on OS X 10.9")
        return
    
    # copy constants from CoreFoundation docs
    # these should be imported, but they don't seem to be exposed by PyObjC
    NSActivityIdleSystemSleepDisabled = 1 << 20
    NSActivityUserInitiated = 0x00FFFFFF
    NSActivityUserInitiatedAllowingIdleSystemSleep = (
        NSActivityUserInitiated & 
        ~NSActivityIdleSystemSleepDisabled
    )
    
    info = NSProcessInfo.processInfo()
    activity = info.beginActivityWithOptions_reason_(
        NSActivityUserInitiatedAllowingIdleSystemSleep,
        "because reasons"
    )
    return activity


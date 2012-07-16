# encoding: utf-8
"""
Utilities using Growl on OS X for notifications.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class IPythonGrowlError(Exception):
    pass

class Notifier(object):

    def __init__(self, app_name):
        try:
            import Growl
        except ImportError:
            self.g_notifier = None
        else:
            self.g_notifier =  Growl.GrowlNotifier(app_name, ['kernel', 'core'])
            self.g_notifier.register()

    def _notify(self, title, msg):
        if self.g_notifier is not None:
            self.g_notifier.notify('core', title, msg)

    def notify(self, title, msg):
        self._notify(title, msg)

    def notify_deferred(self, r, msg):
        title = "Deferred Result"
        msg = msg + '\n' + repr(r)
        self._notify(title, msg)
        return r

_notifier = None

def notify(title, msg):
    pass

def notify_deferred(r, msg):
    return r

def start(app_name):
    global _notifier, notify, notify_deferred
    if _notifier is not None:
        raise IPythonGrowlError("this process is already registered with Growl")
    else:
        _notifier = Notifier(app_name)
        notify = _notifier.notify
        notify_deferred = _notifier.notify_deferred



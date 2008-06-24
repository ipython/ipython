#
#  IPython1SandboxAppDelegate.py
#  IPython1Sandbox
#
#  Created by Barry Wark on 3/4/08.
#  Copyright __MyCompanyName__ 2008. All rights reserved.
#

from Foundation import NSObject, NSPredicate
import objc
import threading

from PyObjCTools import AppHelper

from twisted.internet import reactor

class IPython1SandboxAppDelegate(NSObject):
    ipythonController = objc.IBOutlet()
    
    def applicationShouldTerminate_(self, sender):
        if reactor.running:
            reactor.addSystemEventTrigger(
                'after', 'shutdown', AppHelper.stopEventLoop)
            reactor.stop()
            return False
        return True
    
    
    def applicationDidFinishLaunching_(self, sender):
        reactor.interleave(AppHelper.callAfter)
        assert(reactor.running)
    
    
    def workspaceFilterPredicate(self):
        return NSPredicate.predicateWithFormat_("NOT (self.value BEGINSWITH '<')")


    


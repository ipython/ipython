#
#  main.py
#  IPython1Sandbox
#
#  Created by Barry Wark on 3/4/08.
#  Copyright __MyCompanyName__ 2008. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

from twisted.internet import _threadedselect
reactor = _threadedselect.install()

# import modules containing classes required to start application and load MainMenu.nib
import IPython1SandboxAppDelegate
import IPython.frontend.cocoa.cocoa_frontend

# pass control to AppKit
AppHelper.runEventLoop()

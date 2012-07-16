# encoding: utf-8
"""
Provides a namespace for loading the Cocoa frontend via a Cocoa plugin.

Author: Barry Wark
"""
__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from PyObjCTools import AppHelper
from twisted.internet import _threadedselect

#make sure _threadedselect is installed first
reactor = _threadedselect.install()

# load the Cocoa frontend controller
from IPython.frontend.cocoa.cocoa_frontend import IPythonCocoaController
reactor.interleave(AppHelper.callAfter)
assert(reactor.running)

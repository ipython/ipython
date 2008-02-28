# -*- coding: utf-8 -*-
"""
Class which mimics a module.

Needed to allow pickle to correctly resolve namespaces during IPython
sessions.

$Id: FakeModule.py 2754 2007-09-09 10:16:59Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2002-2004 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import types

class FakeModule(types.ModuleType):
    """Simple class with attribute access to fake a module.

    This is not meant to replace a module, but to allow inserting a fake
    module in sys.modules so that systems which rely on run-time module
    importing (like shelve and pickle) work correctly in interactive IPython
    sessions.

    Do NOT use this code for anything other than this IPython private hack."""

    def __init__(self,adict=None):
        
        # tmp to force __dict__ instance creation, else self.__dict__ fails
        self.__iptmp = None
        
        # It seems pydoc (and perhaps others) needs any module instance to
        # implement a __nonzero__ method, so we add it if missing:
        self.__dict__.setdefault('__nonzero__',lambda : True)
        self.__dict__.setdefault('__file__',__file__)

        # cleanup our temp trick
        del self.__iptmp

        if adict is not None:
            self.__dict__.update(adict)

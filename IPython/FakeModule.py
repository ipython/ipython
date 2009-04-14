# -*- coding: utf-8 -*-
"""
Class which mimics a module.

Needed to allow pickle to correctly resolve namespaces during IPython
sessions.
"""

#*****************************************************************************
#       Copyright (C) 2002-2004 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import types

def init_fakemod_dict(fm,adict=None):
    """Initialize a FakeModule instance __dict__.

    Kept as a standalone function and not a method so the FakeModule API can
    remain basically empty.

    This should be considered for private IPython use, used in managing
    namespaces for %run.

    Parameters
    ----------

    fm : FakeModule instance

    adict : dict, optional
    """

    dct = {}
    # It seems pydoc (and perhaps others) needs any module instance to
    # implement a __nonzero__ method, so we add it if missing:
    dct.setdefault('__nonzero__',lambda : True)
    dct.setdefault('__file__',__file__)

    if adict is not None:
        dct.update(adict)

    # Hard assignment of the object's __dict__.  This is nasty but deliberate.
    fm.__dict__.clear()
    fm.__dict__.update(dct)


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
        # cleanup our temp trick
        del self.__iptmp
        # Now, initialize the actual data in the instance dict.
        init_fakemod_dict(self,adict)

"""Monkeypatch nose to accept any callable as a method.

By default, nose's ismethod() fails for static methods.
Once this is fixed in upstream nose we can disable it.

Notes: 

- As of Nose 1.0.0, the problem persists so this monkeypatch is still
needed.

- Merely importing this module causes the monkeypatch to be applied."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2009-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import unittest
import sys
import nose.loader
from inspect import ismethod, isfunction

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

def getTestCaseNames(self, testCaseClass):
    """Override to select with selector, unless
    config.getTestCaseNamesCompat is True
    """
    if self.config.getTestCaseNamesCompat:
        return unittest.TestLoader.getTestCaseNames(self, testCaseClass)

    def wanted(attr, cls=testCaseClass, sel=self.selector):
        item = getattr(cls, attr, None)
        # MONKEYPATCH: replace this:
        #if not ismethod(item):
        #    return False
        # return sel.wantMethod(item)
        # With:
        if ismethod(item):
            return sel.wantMethod(item)
        # static method or something. If this is a static method, we
        # can't get the class information, and we have to treat it
        # as a function.  Thus, we will miss things like class
        # attributes for test selection
        if isfunction(item):
            return sel.wantFunction(item)
        return False
        # END MONKEYPATCH
    
    cases = filter(wanted, dir(testCaseClass))
    for base in testCaseClass.__bases__:
        for case in self.getTestCaseNames(base):
            if case not in cases:
                cases.append(case)
    # add runTest if nothing else picked
    if not cases and hasattr(testCaseClass, 'runTest'):
        cases = ['runTest']
    if self.sortTestMethodsUsing:
        cases.sort(self.sortTestMethodsUsing)
    return cases


##########################################################################
# Apply monkeypatch here
# Python 3 must be running with newer version of Nose, so don't touch anything.
if sys.version_info[0] < 3:
    nose.loader.TestLoader.getTestCaseNames = getTestCaseNames
##########################################################################

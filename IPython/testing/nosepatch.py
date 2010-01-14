"""Monkeypatch nose to accept any callable as a method.

By default, nose's ismethod() fails for static methods.
Once this is fixed in upstream nose we can disable it.

Note: merely importing this module causes the monkeypatch to be applied."""

import unittest
import nose.loader
from inspect import ismethod, isfunction

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
nose.loader.TestLoader.getTestCaseNames = getTestCaseNames
##########################################################################

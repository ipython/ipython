# encoding: utf-8

"""A parallelized function that does scatter/execute/gather."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from types import FunctionType

class ParallelFunction:
    """A function that operates in parallel on sequences."""
    def __init__(self, func, multiengine, targets, block):
        """Create a `ParallelFunction`.
        """
        assert isinstance(func, (str, FunctionType)), "func must be a fuction or str"
        self.func = func
        self.multiengine = multiengine
        self.targets = targets
        self.block = block
        
    def __call__(self, sequence):
        return self.multiengine.map(self.func, sequence, targets=self.targets, block=self.block)
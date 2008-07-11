# encoding: utf-8

"""A parallelized version of Python's builtin map."""

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
from zope.interface import Interface, implements

class IMapper(Interface):
    
    def __call__(func, *sequences):
        """Do map in parallel."""

class Mapper(object):
    
    implements(IMapper)
    
    def __init__(self, multiengine, dist='b', targets='all', block=True):
        self.multiengine = multiengine
        self.dist = dist
        self.targets = targets
        self.block = block
        
    def __call__(self, func, *sequences):
        return self.map(func, *sequences)
    
    def map(self, func, *sequences):
        assert isinstance(func, (str, FunctionType)), "func must be a fuction or str"
        return self.multiengine._map(func, sequences, dist=self.dist,
            targets=self.targets, block=self.block)
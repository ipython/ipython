# -*- coding: utf-8 -*-
"""Modify the PhysicalQuantities class for more convenient interactive use.

Also redefine some math functions to operate on PhysQties with no need for
special method syntax. This just means moving them out to the global
namespace.

This module should always be loaded *after* math or Numeric, so it can
overwrite math functions with the versions that handle units."""

#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

from Scientific.Physics.PhysicalQuantities import PhysicalQuantity

# This code can be set up to work with Numeric or with math for providing the
# mathematical functions. Uncomment the one you prefer to use below.

# If you use math, sin(x) won't work for x an array, only float or PhysQty
import math

# If you use Numeric, sin(x) works for x a float, PhysQty an array.
#import Numeric as math

class PhysicalQuantityFunction:
    """Generic function wrapper for PhysicalQuantity instances.

    Calls functions from either the math library or the instance's methods as
    required.  Allows using sin(theta) or sqrt(v**2) syntax irrespective of
    whether theta is a pure number or a PhysicalQuantity.

    This is *slow*. It's meant for convenient interactive use, not for
    speed."""

    def __init__(self,name):
        self.name = name
        
    def __call__(self,x):
        if isinstance(x,PhysicalQuantity):
            return PhysicalQuantity.__dict__[self.name](x)
        else:
            return math.__dict__[self.name](x)

class PhysicalQuantityInteractive(PhysicalQuantity):
    """Physical quantity with units - modified for Interactive use.

    Basically, the __str__ and __repr__ methods have been swapped for more
    convenient interactive use. Powers are shown as ^ instead of ** and only 4
    significant figures are shown.

    Also adds the following aliases for commonly used methods:
      b = PhysicalQuantity.inBaseUnits
      u = PhysicalQuantity.inUnitsOf
      
    These are useful when doing a lot of interactive calculations.
    """
    
    # shorthands for the most useful unit conversions
    b = PhysicalQuantity.inBaseUnits  # so you can just type x.b to get base units
    u = PhysicalQuantity.inUnitsOf

    # This can be done, but it can get dangerous when coupled with IPython's
    # auto-calling. Everything ends up shown in baseunits and things like x*2
    # get automatically converted to k(*2), which doesn't work.
    # Probably not a good idea in general...
    #__call__ = b
    
    def __str__(self):
        return PhysicalQuantity.__repr__(self)
 
    def __repr__(self):
        value = '%.4G' % self.value
        units = self.unit.name().replace('**','^')
        return value + ' ' + units

# implement the methods defined in PhysicalQuantity as PhysicalQuantityFunctions
sin = PhysicalQuantityFunction('sin')
cos = PhysicalQuantityFunction('cos')
tan = PhysicalQuantityFunction('tan')
sqrt = PhysicalQuantityFunction('sqrt')

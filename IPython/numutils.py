# -*- coding: utf-8 -*-
"""
A set of convenient utilities for numerical work.

Most of this module requires Numerical Python or is meant to be used with it.
See http://www.pfdubois.com/numpy for details.

$Id: numutils.py 958 2005-12-27 23:17:51Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

__all__ = ['sum_flat','mean_flat','rms_flat','base_repr','binary_repr',
           'amin','amax','amap','zeros_like','empty_like',
           'frange','diagonal_matrix','identity',
           'fromfunction_kw','log2','ispower2',
           'norm','l1norm','l2norm','exp_safe',
           'inf','infty','Infinity',
           'Numeric']

#****************************************************************************
# required modules
import __main__
import math
import operator
import sys

import Numeric
from Numeric import *

#*****************************************************************************
# Globals

# useful for testing infinities in results of array divisions (which don't
# raise an exception)
# Python, LaTeX and Mathematica names.
inf = infty = Infinity = (array([1])/0.0)[0]

#****************************************************************************
# function definitions        
exp_safe_MIN = math.log(2.2250738585072014e-308)
exp_safe_MAX = 1.7976931348623157e+308

def exp_safe(x):
    """Compute exponentials which safely underflow to zero.

    Slow but convenient to use. Note that NumArray will introduce proper
    floating point exception handling with access to the underlying
    hardware."""

    if type(x) is ArrayType:
        return exp(clip(x,exp_safe_MIN,exp_safe_MAX))
    else:
        return math.exp(x)

def amap(fn,*args):
    """amap(function, sequence[, sequence, ...]) -> array.

    Works like map(), but it returns an array.  This is just a convenient
    shorthand for Numeric.array(map(...))"""
    return array(map(fn,*args))

def amin(m,axis=0):
    """amin(m,axis=0) returns the minimum of m along dimension axis.
    """
    return minimum.reduce(asarray(m),axis)

def amax(m,axis=0):
    """amax(m,axis=0) returns the maximum of m along dimension axis.
    """
    return maximum.reduce(asarray(m),axis)

def zeros_like(a):
    """Return an array of zeros of the shape and typecode of a.

    If you don't explicitly need the array to be zeroed, you should instead
    use empty_like(), which is faster as it only allocates memory."""

    return zeros(a.shape,a.typecode())

def empty_like(a):
    """Return an empty (uninitialized) array of the shape and typecode of a.

    Note that this does NOT initialize the returned array.  If you require
    your array to be initialized, you should use zeros_like().

    This requires Numeric.empty(), which appeared in Numeric 23.7."""

    return empty(a.shape,a.typecode())

def sum_flat(a):
    """Return the sum of all the elements of a, flattened out.

    It uses a.flat, and if a is not contiguous, a call to ravel(a) is made."""

    if a.iscontiguous():
        return Numeric.sum(a.flat)
    else:
        return Numeric.sum(ravel(a))

def mean_flat(a):
    """Return the mean of all the elements of a, flattened out."""

    return sum_flat(a)/float(size(a))

def rms_flat(a):
    """Return the root mean square of all the elements of a, flattened out."""

    return math.sqrt(sum_flat(absolute(a)**2)/float(size(a)))

def l1norm(a):
    """Return the l1 norm of a, flattened out.

    Implemented as a separate function (not a call to norm() for speed).

    Ref: http://mathworld.wolfram.com/L1-Norm.html"""

    return sum_flat(absolute(a))

def l2norm(a):
    """Return the l2 norm of a, flattened out.

    Implemented as a separate function (not a call to norm() for speed).

    Ref: http://mathworld.wolfram.com/L2-Norm.html"""

    return math.sqrt(sum_flat(absolute(a)**2))

def norm(a,p=2):
    """norm(a,p=2) -> l-p norm of a.flat

    Return the l-p norm of a, considered as a flat array.  This is NOT a true
    matrix norm, since arrays of arbitrary rank are always flattened.

    p can be a number or one of the strings ('inf','Infinity') to get the
    L-infinity norm.

    Ref: http://mathworld.wolfram.com/VectorNorm.html
         http://mathworld.wolfram.com/L-Infinity-Norm.html"""
    
    if p in ('inf','Infinity'):
        return max(absolute(a).flat)
    else:
        return (sum_flat(absolute(a)**p))**(1.0/p)    
    
def frange(xini,xfin=None,delta=None,**kw):
    """frange([start,] stop[, step, keywords]) -> array of floats

    Return a Numeric array() containing a progression of floats. Similar to
    arange(), but defaults to a closed interval.

    frange(x0, x1) returns [x0, x0+1, x0+2, ..., x1]; start defaults to 0, and
    the endpoint *is included*. This behavior is different from that of
    range() and arange(). This is deliberate, since frange will probably be
    more useful for generating lists of points for function evaluation, and
    endpoints are often desired in this use. The usual behavior of range() can
    be obtained by setting the keyword 'closed=0', in this case frange()
    basically becomes arange().

    When step is given, it specifies the increment (or decrement). All
    arguments can be floating point numbers.

    frange(x0,x1,d) returns [x0,x0+d,x0+2d,...,xfin] where xfin<=x1.

    frange can also be called with the keyword 'npts'. This sets the number of
    points the list should contain (and overrides the value 'step' might have
    been given). arange() doesn't offer this option.

    Examples:
    >>> frange(3)
    array([ 0.,  1.,  2.,  3.])
    >>> frange(3,closed=0)
    array([ 0.,  1.,  2.])
    >>> frange(1,6,2)
    array([1, 3, 5])
    >>> frange(1,6.5,npts=5)
    array([ 1.   ,  2.375,  3.75 ,  5.125,  6.5  ])
    """

    #defaults
    kw.setdefault('closed',1)
    endpoint = kw['closed'] != 0
        
    # funny logic to allow the *first* argument to be optional (like range())
    # This was modified with a simpler version from a similar frange() found
    # at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66472
    if xfin == None:
        xfin = xini + 0.0
        xini = 0.0
        
    if delta == None:
        delta = 1.0

    # compute # of points, spacing and return final list
    try:
        npts=kw['npts']
        delta=(xfin-xini)/float(npts-endpoint)
    except KeyError:
        # round() gets npts right even with the vagaries of floating point.
        npts=int(round((xfin-xini)/delta+endpoint))

    return arange(npts)*delta+xini

def diagonal_matrix(diag):
    """Return square diagonal matrix whose non-zero elements are given by the
    input array."""

    return diag*identity(len(diag))

def identity(n,rank=2,typecode='l'):
    """identity(n,r) returns the identity matrix of shape (n,n,...,n) (rank r).

    For ranks higher than 2, this object is simply a multi-index Kronecker
    delta:
                        /  1  if i0=i1=...=iR,
    id[i0,i1,...,iR] = -|
                        \  0  otherwise.

    Optionally a typecode may be given (it defaults to 'l').

    Since rank defaults to 2, this function behaves in the default case (when
    only n is given) like the Numeric identity function."""
    
    iden = zeros((n,)*rank,typecode=typecode)
    for i in range(n):
        idx = (i,)*rank
        iden[idx] = 1
    return iden

def base_repr (number, base = 2, padding = 0):
    """Return the representation of a number in any given base."""
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if number < base: \
       return (padding - 1) * chars [0] + chars [int (number)]
    max_exponent = int (math.log (number)/math.log (base))
    max_power = long (base) ** max_exponent
    lead_digit = int (number/max_power)
    return chars [lead_digit] + \
           base_repr (number - max_power * lead_digit, base, \
                      max (padding - 1, max_exponent))

def binary_repr(number, max_length = 1025):
    """Return the binary representation of the input number as a string.

    This is more efficient than using base_repr with base 2.

    Increase the value of max_length for very large numbers. Note that on
    32-bit machines, 2**1023 is the largest integer power of 2 which can be
    converted to a Python float."""
    
    assert number < 2L << max_length
    shifts = map (operator.rshift, max_length * [number], \
                  range (max_length - 1, -1, -1))
    digits = map (operator.mod, shifts, max_length * [2])
    if not digits.count (1): return 0
    digits = digits [digits.index (1):]
    return ''.join (map (repr, digits)).replace('L','')

def log2(x,ln2 = math.log(2.0)):
    """Return the log(x) in base 2.
    
    This is a _slow_ function but which is guaranteed to return the correct
    integer value if the input is an ineger exact power of 2."""

    try:
        bin_n = binary_repr(x)[1:]
    except (AssertionError,TypeError):
        return math.log(x)/ln2
    else:
        if '1' in bin_n:
            return math.log(x)/ln2
        else:
            return len(bin_n)

def ispower2(n):
    """Returns the log base 2 of n if n is a power of 2, zero otherwise.

    Note the potential ambiguity if n==1: 2**0==1, interpret accordingly."""

    bin_n = binary_repr(n)[1:]
    if '1' in bin_n:
        return 0
    else:
        return len(bin_n)

def fromfunction_kw(function, dimensions, **kwargs):
    """Drop-in replacement for fromfunction() from Numerical Python.
 
    Allows passing keyword arguments to the desired function.

    Call it as (keywords are optional):
    fromfunction_kw(MyFunction, dimensions, keywords)

    The function MyFunction() is responsible for handling the dictionary of
    keywords it will recieve."""

    return function(tuple(indices(dimensions)),**kwargs)

#**************************** end file <numutils.py> ************************

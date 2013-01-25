# encoding: utf-8
"""Utilities for working with data structures like lists, dicts and tuples.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import types

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def uniq_stable(elems):
    """uniq_stable(elems) -> list

    Return from an iterable, a list of all the unique elements in the input,
    but maintaining the order in which they first appear.

    Note: All elements in the input must be hashable for this routine
    to work, as it internally uses a set for efficiency reasons.
    """
    seen = set()
    return [x for x in elems if x not in seen and not seen.add(x)]


def sort_compare(lst1, lst2, inplace=1):
    """Sort and compare two lists.

    By default it does it in place, thus modifying the lists. Use inplace = 0
    to avoid that (at the cost of temporary copy creation)."""
    if not inplace:
        lst1 = lst1[:]
        lst2 = lst2[:]
    lst1.sort(); lst2.sort()
    return lst1 == lst2


def list2dict(lst):
    """Takes a list of (key,value) pairs and turns it into a dict."""

    dic = {}
    for k,v in lst: dic[k] = v
    return dic


def list2dict2(lst, default=''):
    """Takes a list and turns it into a dict.
    Much slower than list2dict, but more versatile. This version can take
    lists with sublists of arbitrary length (including sclars)."""

    dic = {}
    for elem in lst:
        if type(elem) in (types.ListType,types.TupleType):
            size = len(elem)
            if  size == 0:
                pass
            elif size == 1:
                dic[elem] = default
            else:
                k,v = elem[0], elem[1:]
                if len(v) == 1: v = v[0]
                dic[k] = v
        else:
            dic[elem] = default
    return dic


def flatten(seq):
    """Flatten a list of lists (NOT recursive, only works for 2d lists)."""

    return [x for subseq in seq for x in subseq]


def get_slice(seq, start=0, stop=None, step=1):
    """Get a slice of a sequence with variable step. Specify start,stop,step."""
    if stop == None:
        stop = len(seq)
    item = lambda i: seq[i]
    return map(item,xrange(start,stop,step))


def chop(seq, size):
    """Chop a sequence into chunks of the given size."""
    chunk = lambda i: seq[i:i+size]
    return map(chunk,xrange(0,len(seq),size))



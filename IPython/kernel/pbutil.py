# encoding: utf-8

"""Utilities for PB using modules."""

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

import cPickle as pickle

from twisted.python.failure import Failure
from twisted.python import failure
import threading, sys

from IPython.kernel import pbconfig
from IPython.kernel.error import PBMessageSizeError, UnpickleableException


#-------------------------------------------------------------------------------
# The actual utilities
#-------------------------------------------------------------------------------

def packageFailure(f):
    """Clean and pickle a failure preappending the string FAILURE:"""
    
    f.cleanFailure()
    # This is sometimes helpful in debugging
    #f.raiseException()
    try:
        pString = pickle.dumps(f, 2)
    except pickle.PicklingError:
        # Certain types of exceptions are not pickleable, for instance ones
        # from Boost.Python.  We try to wrap them in something that is
        f.type = UnpickleableException
        f.value = UnpickleableException(str(f.type) + ": " + str(f.value))
        pString = pickle.dumps(f, 2)
    return 'FAILURE:' + pString

def unpackageFailure(r):
    """
    See if a returned value is a pickled Failure object.

    To distinguish between general pickled objects and pickled Failures, the
    other side should prepend the string FAILURE: to any pickled Failure.
    """
    if isinstance(r, str):
        if r.startswith('FAILURE:'):
            try:
                result = pickle.loads(r[8:])
            except pickle.PickleError:
                return failure.Failure( \
                    FailureUnpickleable("Could not unpickle failure."))
            else:
                return result
    return r

def checkMessageSize(m, info):
    """Check string m to see if it violates banana.SIZE_LIMIT.
    
    This should be used on the client side of things for push, scatter
    and push_serialized and on the other end for pull, gather and pull_serialized.
    
    :Parameters:
        `m` : string
            Message whose size will be checked.
        `info` : string
            String describing what object the message refers to.
            
    :Exceptions:
        - `PBMessageSizeError`: Raised in the message is > banana.SIZE_LIMIT

    :returns: The original message or a Failure wrapping a PBMessageSizeError
    """

    if len(m) > pbconfig.banana.SIZE_LIMIT:
        s = """Objects too big to transfer:
Names:            %s
Actual Size (kB): %d
SIZE_LIMIT  (kB): %d
* SIZE_LIMIT can be set in kernel.pbconfig""" \
            % (info, len(m)/1024, pbconfig.banana.SIZE_LIMIT/1024)
        return Failure(PBMessageSizeError(s))
    else:
        return m
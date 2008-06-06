# encoding: utf-8

"""Classes and functions for kernel related errors and exceptions."""

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

from IPython.kernel.core import error
from twisted.python import failure

#-------------------------------------------------------------------------------
# Error classes
#-------------------------------------------------------------------------------

class KernelError(error.IPythonError):
    pass

class NotDefined(KernelError):
    def __init__(self, name):
        self.name = name
        self.args = (name,)

    def __repr__(self):
        return '<NotDefined: %s>' % self.name
    
    __str__ = __repr__

class QueueCleared(KernelError):
    pass

class IdInUse(KernelError):
    pass

class ProtocolError(KernelError):
    pass

class ConnectionError(KernelError):
    pass

class InvalidEngineID(KernelError):
    pass
    
class NoEnginesRegistered(KernelError):
    pass
    
class InvalidClientID(KernelError):
    pass
    
class InvalidDeferredID(KernelError):
    pass
    
class SerializationError(KernelError):
    pass
    
class MessageSizeError(KernelError):
    pass
    
class PBMessageSizeError(MessageSizeError):
    pass
    
class ResultNotCompleted(KernelError):
    pass
    
class ResultAlreadyRetrieved(KernelError):
    pass
    
class ClientError(KernelError):
    pass

class TaskAborted(KernelError):
    pass

class TaskTimeout(KernelError):
    pass

class NotAPendingResult(KernelError):
    pass

class UnpickleableException(KernelError):
    pass

class AbortedPendingDeferredError(KernelError):
    pass

class InvalidProperty(KernelError):
    pass

class MissingBlockArgument(KernelError):
    pass

class StopLocalExecution(KernelError):
    pass

class SecurityError(KernelError):
    pass

class CompositeError(KernelError):
    def __init__(self, message, elist):
        Exception.__init__(self, *(message, elist))
        self.message = message
        self.elist = elist
  
    def _get_engine_str(self, ev):
        try:
            ei = ev._ipython_engine_info
        except AttributeError:
            return '[Engine Exception]'
        else:
            return '[%i:%s]: ' % (ei['engineid'], ei['method'])
    
    def _get_traceback(self, ev):
        try:
            tb = ev._ipython_traceback_text
        except AttributeError:
            return 'No traceback available'
        else:
            return tb
  
    def __str__(self):
        s = str(self.message)
        for et, ev, etb in self.elist:
            engine_str = self._get_engine_str(ev)
            s = s + '\n' + engine_str + str(et.__name__) + ': ' + str(ev)
        return s
    
    def print_tracebacks(self, excid=None):
        if excid is None:
            for (et,ev,etb) in self.elist:
                print self._get_engine_str(ev)
                print self._get_traceback(ev)
                print
        else:
            try:
                et,ev,etb = self.elist[excid]
            except:
                raise IndexError("an exception with index %i does not exist"%excid)
            else:
                print self._get_engine_str(ev)
                print self._get_traceback(ev)
    
    def raise_exception(self, excid=0):
        try:
            et,ev,etb = self.elist[excid]
        except:
            raise IndexError("an exception with index %i does not exist"%excid)
        else:
            raise et, ev, etb

def collect_exceptions(rlist, method):
    elist = []
    for r in rlist:
        if isinstance(r, failure.Failure):
            r.cleanFailure()
            et, ev, etb = r.type, r.value, r.tb
            # Sometimes we could have CompositeError in our list.  Just take
            # the errors out of them and put them in our new list.  This 
            # has the effect of flattening lists of CompositeErrors into one
            # CompositeError
            if et==CompositeError:
                for e in ev.elist:
                    elist.append(e)
            else:
                elist.append((et, ev, etb))
    if len(elist)==0:
        return rlist
    else:
        msg = "one or more exceptions from call to method: %s" % (method)
        # This silliness is needed so the debugger has access to the exception
        # instance (e in this case)
        try:
            raise CompositeError(msg, elist)
        except CompositeError, e:
            raise e
            


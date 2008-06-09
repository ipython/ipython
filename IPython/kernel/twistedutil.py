#!/usr/bin/env python
# encoding: utf-8

"""Things directly related to all of twisted."""

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

import threading, Queue, atexit
import twisted

from twisted.internet import defer, reactor
from twisted.python import log, failure

#-------------------------------------------------------------------------------
# Classes related to twisted and threads
#-------------------------------------------------------------------------------


class ReactorInThread(threading.Thread):
    """Run the twisted reactor in a different thread.
    
    For the process to be able to exit cleanly, do the following:
    
    rit = ReactorInThread()
    rit.setDaemon(True)
    rit.start()
    
    """
    
    def run(self):
        reactor.run(installSignalHandlers=0)
        # self.join()
        
    def stop(self):
        # I don't think this does anything useful.
        blockingCallFromThread(reactor.stop)
        self.join()

if(twisted.version.major >= 8):
    import twisted.internet.threads
    def blockingCallFromThread(f, *a, **kw):
        """
        Run a function in the reactor from a thread, and wait for the result
        synchronously, i.e. until the callback chain returned by the function get a
        result.
        
        Delegates to twisted.internet.threads.blockingCallFromThread(reactor, f, *a, **kw),
        passing twisted.internet.reactor for the first argument.
        
        @param f: the callable to run in the reactor thread
        @type f: any callable.
        @param a: the arguments to pass to C{f}.
        @param kw: the keyword arguments to pass to C{f}.

        @return: the result of the callback chain.
        @raise: any error raised during the callback chain.
        """
        return twisted.internet.threads.blockingCallFromThread(reactor, f, *a, **kw)
    
else:   
    def blockingCallFromThread(f, *a, **kw):
        """
        Run a function in the reactor from a thread, and wait for the result
        synchronously, i.e. until the callback chain returned by the function get a
        result.

        @param f: the callable to run in the reactor thread
        @type f: any callable.
        @param a: the arguments to pass to C{f}.
        @param kw: the keyword arguments to pass to C{f}.

        @return: the result of the callback chain.
        @raise: any error raised during the callback chain.
        """
        from twisted.internet import reactor
        queue = Queue.Queue()
        def _callFromThread():
            result = defer.maybeDeferred(f, *a, **kw)
            result.addBoth(queue.put)
        
        reactor.callFromThread(_callFromThread)
        result = queue.get()
        if isinstance(result, failure.Failure):
            # This makes it easier for the debugger to get access to the instance
            try:
                result.raiseException()
            except Exception, e:
                raise e
        return result
    


#-------------------------------------------------------------------------------
# Things for managing deferreds
#-------------------------------------------------------------------------------


def parseResults(results):
    """Pull out results/Failures from a DeferredList."""
    return [x[1] for x in results]

def gatherBoth(dlist, fireOnOneCallback=0, 
                      fireOnOneErrback=0,
                      consumeErrors=0,
                      logErrors=0):
    """This is like gatherBoth, but sets consumeErrors=1."""
    d = DeferredList(dlist, fireOnOneCallback, fireOnOneErrback,
                     consumeErrors, logErrors)
    if not fireOnOneCallback:
        d.addCallback(parseResults)
    return d

SUCCESS = True
FAILURE = False

class DeferredList(defer.Deferred):
    """I combine a group of deferreds into one callback.

    I track a list of L{Deferred}s for their callbacks, and make a single
    callback when they have all completed, a list of (success, result)
    tuples, 'success' being a boolean.

    Note that you can still use a L{Deferred} after putting it in a
    DeferredList.  For example, you can suppress 'Unhandled error in Deferred'
    messages by adding errbacks to the Deferreds *after* putting them in the
    DeferredList, as a DeferredList won't swallow the errors.  (Although a more
    convenient way to do this is simply to set the consumeErrors flag)
    
    Note: This is a modified version of the twisted.internet.defer.DeferredList
    """

    fireOnOneCallback = 0
    fireOnOneErrback = 0

    def __init__(self, deferredList, fireOnOneCallback=0, fireOnOneErrback=0,
                 consumeErrors=0, logErrors=0):
        """Initialize a DeferredList.

        @type deferredList:  C{list} of L{Deferred}s
        @param deferredList: The list of deferreds to track.
        @param fireOnOneCallback: (keyword param) a flag indicating that
                             only one callback needs to be fired for me to call
                             my callback
        @param fireOnOneErrback: (keyword param) a flag indicating that
                            only one errback needs to be fired for me to call
                            my errback
        @param consumeErrors: (keyword param) a flag indicating that any errors
                            raised in the original deferreds should be
                            consumed by this DeferredList.  This is useful to
                            prevent spurious warnings being logged.
        """
        self.resultList = [None] * len(deferredList)
        defer.Deferred.__init__(self)
        if len(deferredList) == 0 and not fireOnOneCallback:
            self.callback(self.resultList)

        # These flags need to be set *before* attaching callbacks to the
        # deferreds, because the callbacks use these flags, and will run
        # synchronously if any of the deferreds are already fired.
        self.fireOnOneCallback = fireOnOneCallback
        self.fireOnOneErrback = fireOnOneErrback
        self.consumeErrors = consumeErrors
        self.logErrors = logErrors
        self.finishedCount = 0

        index = 0
        for deferred in deferredList:
            deferred.addCallbacks(self._cbDeferred, self._cbDeferred,
                                  callbackArgs=(index,SUCCESS),
                                  errbackArgs=(index,FAILURE))
            index = index + 1

    def _cbDeferred(self, result, index, succeeded):
        """(internal) Callback for when one of my deferreds fires.
        """
        self.resultList[index] = (succeeded, result)

        self.finishedCount += 1
        if not self.called:
            if succeeded == SUCCESS and self.fireOnOneCallback:
                self.callback((result, index))
            elif succeeded == FAILURE and self.fireOnOneErrback:
                # We have modified this to fire the errback chain with the actual
                # Failure instance the originally occured rather than twisted's
                # FirstError which wraps the failure
                self.errback(result)
            elif self.finishedCount == len(self.resultList):
                self.callback(self.resultList)

        if succeeded == FAILURE and self.logErrors:
            log.err(result)
        if succeeded == FAILURE and self.consumeErrors:
            result = None

        return result

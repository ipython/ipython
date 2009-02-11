#!/usr/bin/env python
"""A parallel tasking tool that uses asynchronous programming. This uses 
blocking client to get taskid, but returns a Deferred as the result of 
run(). Users should attach their callbacks on these Deferreds.

Only returning of results is asynchronous. Submitting tasks and getting task
ids are done synchronously.

Yichun Wei 03/2008
"""

import inspect
import itertools
import numpy as N

from twisted.python import log
from ipython1.kernel import client
from ipython1.kernel.client import Task

""" After http://trac.pocoo.org/repos/pocoo/trunk/pocoo/utils/decorators.py
"""
class submit_job(object):
    """ a decorator factory: takes a MultiEngineClient a TaskClient, returns a 
        decorator, that makes a call to the decorated func as a task in ipython1
        and submit it to IPython1 controller:
    """
    def __init__(self, rc, tc):
        self.rc = rc
        self.tc = tc

    def __call__(self, func):
        return self._decorate(func)

    def _getinfo(self, func):
        assert inspect.ismethod(func) or inspect.isfunction(func)
        regargs, varargs, varkwargs, defaults = inspect.getargspec(func)
        argnames = list(regargs)
        if varargs:
            argnames.append(varargs)
        if varkwargs:
            argnames.append(varkwargs)
        counter = itertools.count()
        fullsign = inspect.formatargspec(
            regargs, varargs, varkwargs, defaults,
            formatvalue=lambda value: '=defarg[%i]' % counter.next())[1:-1]
        shortsign = inspect.formatargspec(
            regargs, varargs, varkwargs, defaults,
            formatvalue=lambda value: '')[1:-1]
        dic = dict(('arg%s' % n, name) for n, name in enumerate(argnames))
        dic.update(name=func.__name__, argnames=argnames, shortsign=shortsign,
            fullsign = fullsign, defarg = func.func_defaults or ())
        return dic

    def _decorate(self, func):
        """
        Takes a function and a remote controller and returns a function
        decorated that is going to submit the job with the controller. 
        The decorated function is obtained by evaluating a lambda 
        function with the correct signature.

        the TaskController setupNS doesn't cope with functions, but we
        can use RemoteController to push functions/modules into engines.

        Changes:
        200803. In new ipython1, we use push_function for functions.
        """
        rc, tc = self.rc, self.tc
        infodict = self._getinfo(func)
        if 'rc' in infodict['argnames']:
            raise NameError, "You cannot use rc as argument names!"

        # we assume the engines' namepace has been prepared.
        # ns[func.__name__] is already the decorated closure function.
        # we need to change it back to the original function:
        ns = {}
        ns[func.__name__] = func

        # push func and all its environment/prerequesites to engines
        rc.push_function(ns, block=True) # note it is nonblock by default, not know if it causes problems

        def do_submit_func(*args, **kwds):
            jobns = {} 

            # Initialize job namespace with args that have default args 
            # now we support calls that uses default args
            for n in infodict['fullsign'].split(','):
                try:
                    vname, var = n.split('=')
                    vname, var = vname.strip(), var.strip()
                except: # no defarg, one of vname, var is None
                    pass
                else:
                    jobns.setdefault(vname, eval(var, infodict))

            # push args and kwds, overwritting default args if needed.
            nokwds = dict((n,v) for n,v in zip(infodict['argnames'], args)) # truncated
            jobns.update(nokwds)
            jobns.update(kwds)

            task = Task('a_very_long_and_rare_name = %(name)s(%(shortsign)s)' % infodict, 
                pull=['a_very_long_and_rare_name'], push=jobns,)
            jobid = tc.run(task)
            # res is a deferred, one can attach callbacks on it
            res = tc.task_controller.get_task_result(jobid, block=True)
            res.addCallback(lambda x: x.ns['a_very_long_and_rare_name'])
            res.addErrback(log.err)
            return res 

        do_submit_func.rc = rc
        do_submit_func.tc = tc
        return do_submit_func


def parallelized(rc, tc, initstrlist=[]):
    """ rc - remote controller
        tc - taks controller
        strlist - a list of str that's being executed on engines.
    """
    for cmd in initstrlist:
        rc.execute(cmd, block=True)
    return submit_job(rc, tc)


from twisted.internet import defer
from numpy import array, nan

def pmap(func, parr, **kwds):
    """Run func on every element of parr (array), using the elements 
    as the only one parameter (so you can usually use a dict that 
    wraps many parameters). -> a result array of Deferreds with the 
    same shape. func.tc will be used as the taskclient.

    **kwds are passed on to func, not changed.
    """
    assert func.tc
    tc = func.tc

    def run(p, **kwds):
        if p:
            return func(p, **kwds)
        else:
            return defer.succeed(nan) 

    reslist = [run(p, **kwds).addErrback(log.err) for p in parr.flat]
    resarr = array(reslist)
    resarr.shape = parr.shape
    return resarr


if __name__=='__main__':

    rc = client.MultiEngineClient(client.default_address)
    tc = client.TaskClient(client.default_task_address)

    # if commenting out the decorator you get a local running version 
    # instantly
    @parallelized(rc, tc)
    def f(a, b=1):
        #from time import sleep 
        #sleep(1)
        print "a,b=", a,b
        return a+b

    def showres(x):
        print 'ans:',x

    res = f(11,5)
    res.addCallback(showres)

    # this is not necessary in Twisted 8.0
    from twisted.internet import reactor
    reactor.run()

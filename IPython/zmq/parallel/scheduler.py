"""The Python scheduler for rich scheduling.

The Pure ZMQ scheduler does not allow routing schemes other than LRU,
nor does it check msg_id DAG dependencies. For those, a slightly slower
Python Scheduler exists.
"""

#----------------------------------------------------------------------
# Imports
#----------------------------------------------------------------------

from __future__ import print_function

import logging
import sys

from datetime import datetime, timedelta
from random import randint, random
from types import FunctionType

try:
    import numpy
except ImportError:
    numpy = None

import zmq
from zmq.eventloop import ioloop, zmqstream

# local imports
from IPython.external.decorator import decorator
from IPython.utils.traitlets import Instance, Dict, List, Set

from . import error
from .dependency import Dependency
from .entry_point import connect_logger, local_logger
from .factory import SessionFactory


@decorator
def logged(f,self,*args,**kwargs):
    # print ("#--------------------")
    self.log.debug("scheduler::%s(*%s,**%s)"%(f.func_name, args, kwargs))
    # print ("#--")
    return f(self,*args, **kwargs)

#----------------------------------------------------------------------
# Chooser functions
#----------------------------------------------------------------------

def plainrandom(loads):
    """Plain random pick."""
    n = len(loads)
    return randint(0,n-1)

def lru(loads):
    """Always pick the front of the line.
    
    The content of `loads` is ignored.
    
    Assumes LRU ordering of loads, with oldest first.
    """
    return 0

def twobin(loads):
    """Pick two at random, use the LRU of the two.
    
    The content of loads is ignored.
    
    Assumes LRU ordering of loads, with oldest first.
    """
    n = len(loads)
    a = randint(0,n-1)
    b = randint(0,n-1)
    return min(a,b)

def weighted(loads):
    """Pick two at random using inverse load as weight.
    
    Return the less loaded of the two.
    """
    # weight 0 a million times more than 1:
    weights = 1./(1e-6+numpy.array(loads))
    sums = weights.cumsum()
    t = sums[-1]
    x = random()*t
    y = random()*t
    idx = 0
    idy = 0
    while sums[idx] < x:
        idx += 1
    while sums[idy] < y:
        idy += 1
    if weights[idy] > weights[idx]:
        return idy
    else:
        return idx

def leastload(loads):
    """Always choose the lowest load.
    
    If the lowest load occurs more than once, the first
    occurance will be used.  If loads has LRU ordering, this means
    the LRU of those with the lowest load is chosen.
    """
    return loads.index(min(loads))

#---------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------
# store empty default dependency:
MET = Dependency([])

class TaskScheduler(SessionFactory):
    """Python TaskScheduler object.
    
    This is the simplest object that supports msg_id based
    DAG dependencies. *Only* task msg_ids are checked, not
    msg_ids of jobs submitted via the MUX queue.
    
    """
    
    # input arguments:
    scheme = Instance(FunctionType, default=leastload) # function for determining the destination
    client_stream = Instance(zmqstream.ZMQStream) # client-facing stream
    engine_stream = Instance(zmqstream.ZMQStream) # engine-facing stream
    notifier_stream = Instance(zmqstream.ZMQStream) # hub-facing sub stream
    mon_stream = Instance(zmqstream.ZMQStream) # hub-facing pub stream
    
    # internals:
    graph = Dict() # dict by msg_id of [ msg_ids that depend on key ]
    depending = Dict() # dict by msg_id of (msg_id, raw_msg, after, follow)
    pending = Dict() # dict by engine_uuid of submitted tasks
    completed = Dict() # dict by engine_uuid of completed tasks
    failed = Dict() # dict by engine_uuid of failed tasks
    destinations = Dict() # dict by msg_id of engine_uuids where jobs ran (reverse of completed+failed)
    clients = Dict() # dict by msg_id for who submitted the task
    targets = List() # list of target IDENTs
    loads = List() # list of engine loads
    all_completed = Set() # set of all completed tasks
    all_failed = Set() # set of all failed tasks
    all_done = Set() # set of all finished tasks=union(completed,failed)
    all_ids = Set() # set of all submitted task IDs
    blacklist = Dict() # dict by msg_id of locations where a job has encountered UnmetDependency
    auditor = Instance('zmq.eventloop.ioloop.PeriodicCallback')
    
    
    def start(self):
        self.engine_stream.on_recv(self.dispatch_result, copy=False)
        self._notification_handlers = dict(
            registration_notification = self._register_engine,
            unregistration_notification = self._unregister_engine
        )
        self.notifier_stream.on_recv(self.dispatch_notification)
        self.auditor = ioloop.PeriodicCallback(self.audit_timeouts, 2e3, self.loop) # 1 Hz
        self.auditor.start()
        self.log.info("Scheduler started...%r"%self)
    
    def resume_receiving(self):
        """Resume accepting jobs."""
        self.client_stream.on_recv(self.dispatch_submission, copy=False)
    
    def stop_receiving(self):
        """Stop accepting jobs while there are no engines.
        Leave them in the ZMQ queue."""
        self.client_stream.on_recv(None)
    
    #-----------------------------------------------------------------------
    # [Un]Registration Handling
    #-----------------------------------------------------------------------
    
    def dispatch_notification(self, msg):
        """dispatch register/unregister events."""
        idents,msg = self.session.feed_identities(msg)
        msg = self.session.unpack_message(msg)
        msg_type = msg['msg_type']
        handler = self._notification_handlers.get(msg_type, None)
        if handler is None:
            raise Exception("Unhandled message type: %s"%msg_type)
        else:
            try:
                handler(str(msg['content']['queue']))
            except KeyError:
                self.log.error("task::Invalid notification msg: %s"%msg)
    
    @logged
    def _register_engine(self, uid):
        """New engine with ident `uid` became available."""
        # head of the line:
        self.targets.insert(0,uid)
        self.loads.insert(0,0)
        # initialize sets
        self.completed[uid] = set()
        self.failed[uid] = set()
        self.pending[uid] = {}
        if len(self.targets) == 1:
            self.resume_receiving()

    def _unregister_engine(self, uid):
        """Existing engine with ident `uid` became unavailable."""
        if len(self.targets) == 1:
            # this was our only engine
            self.stop_receiving()
        
        # handle any potentially finished tasks:
        self.engine_stream.flush()
        
        self.completed.pop(uid)
        self.failed.pop(uid)
        # don't pop destinations, because it might be used later
        # map(self.destinations.pop, self.completed.pop(uid))
        # map(self.destinations.pop, self.failed.pop(uid))
        
        idx = self.targets.index(uid)
        self.targets.pop(idx)
        self.loads.pop(idx)
        
        # wait 5 seconds before cleaning up pending jobs, since the results might
        # still be incoming
        if self.pending[uid]:
            dc = ioloop.DelayedCallback(lambda : self.handle_stranded_tasks(uid), 5000, self.loop)
            dc.start()
    
    @logged
    def handle_stranded_tasks(self, engine):
        """Deal with jobs resident in an engine that died."""
        lost = self.pending.pop(engine)
        
        for msg_id, (raw_msg, targets, MET, follow, timeout) in lost.iteritems():
            self.all_failed.add(msg_id)
            self.all_done.add(msg_id)
            idents,msg = self.session.feed_identities(raw_msg, copy=False)
            msg = self.session.unpack_message(msg, copy=False, content=False)
            parent = msg['header']
            idents = [idents[0],engine]+idents[1:]
            print (idents)
            try:
                raise error.EngineError("Engine %r died while running task %r"%(engine, msg_id))
            except:
                content = error.wrap_exception()
            msg = self.session.send(self.client_stream, 'apply_reply', content, 
                                                    parent=parent, ident=idents)
            self.session.send(self.mon_stream, msg, ident=['outtask']+idents)
            self.update_graph(msg_id)
    
    
    #-----------------------------------------------------------------------
    # Job Submission
    #-----------------------------------------------------------------------
    @logged
    def dispatch_submission(self, raw_msg):
        """Dispatch job submission to appropriate handlers."""
        # ensure targets up to date:
        self.notifier_stream.flush()
        try:
            idents, msg = self.session.feed_identities(raw_msg, copy=False)
            msg = self.session.unpack_message(msg, content=False, copy=False)
        except:
            self.log.error("task::Invaid task: %s"%raw_msg, exc_info=True)
            return
        
        # send to monitor
        self.mon_stream.send_multipart(['intask']+raw_msg, copy=False)
        
        header = msg['header']
        msg_id = header['msg_id']
        self.all_ids.add(msg_id)
        
        # targets
        targets = set(header.get('targets', []))
        
        # time dependencies
        after = Dependency(header.get('after', []))
        if after.all:
            after.difference_update(self.all_completed)
            if not after.success_only:
                after.difference_update(self.all_failed)
        if after.check(self.all_completed, self.all_failed):
            # recast as empty set, if `after` already met,
            # to prevent unnecessary set comparisons
            after = MET
        
        # location dependencies
        follow = Dependency(header.get('follow', []))
        
        # turn timeouts into datetime objects:
        timeout = header.get('timeout', None)
        if timeout:
            timeout = datetime.now() + timedelta(0,timeout,0)
        
        args = [raw_msg, targets, after, follow, timeout]
        
        # validate and reduce dependencies:
        for dep in after,follow:
            # check valid:
            if msg_id in dep or dep.difference(self.all_ids):
                self.depending[msg_id] = args
                return self.fail_unreachable(msg_id, error.InvalidDependency)
            # check if unreachable:
            if dep.unreachable(self.all_failed):
                self.depending[msg_id] = args
                return self.fail_unreachable(msg_id)
        
        if after.check(self.all_completed, self.all_failed):
            # time deps already met, try to run
            if not self.maybe_run(msg_id, *args):
                # can't run yet
                self.save_unmet(msg_id, *args)
        else:
            self.save_unmet(msg_id, *args)
    
    # @logged
    def audit_timeouts(self):
        """Audit all waiting tasks for expired timeouts."""
        now = datetime.now()
        for msg_id in self.depending.keys():
            # must recheck, in case one failure cascaded to another:
            if msg_id in self.depending:
                raw,after,targets,follow,timeout = self.depending[msg_id]
                if timeout and timeout < now:
                    self.fail_unreachable(msg_id, timeout=True)
                
    @logged
    def fail_unreachable(self, msg_id, why=error.ImpossibleDependency):
        """a task has become unreachable, send a reply with an ImpossibleDependency
        error."""
        if msg_id not in self.depending:
            self.log.error("msg %r already failed!"%msg_id)
            return
        raw_msg,targets,after,follow,timeout = self.depending.pop(msg_id)
        for mid in follow.union(after):
            if mid in self.graph:
                self.graph[mid].remove(msg_id)
        
        # FIXME: unpacking a message I've already unpacked, but didn't save:
        idents,msg = self.session.feed_identities(raw_msg, copy=False)
        msg = self.session.unpack_message(msg, copy=False, content=False)
        header = msg['header']
        
        try:
            raise why()
        except:
            content = error.wrap_exception()
        
        self.all_done.add(msg_id)
        self.all_failed.add(msg_id)
        
        msg = self.session.send(self.client_stream, 'apply_reply', content, 
                                                parent=header, ident=idents)
        self.session.send(self.mon_stream, msg, ident=['outtask']+idents)
        
        self.update_graph(msg_id, success=False)
    
    @logged
    def maybe_run(self, msg_id, raw_msg, targets, after, follow, timeout):
        """check location dependencies, and run if they are met."""
        blacklist = self.blacklist.setdefault(msg_id, set())
        if follow or targets or blacklist:
            # we need a can_run filter
            def can_run(idx):
                target = self.targets[idx]
                # check targets
                if targets and target not in targets:
                    return False
                # check blacklist
                if target in blacklist:
                    return False
                # check follow
                return follow.check(self.completed[target], self.failed[target])
            
            indices = filter(can_run, range(len(self.targets)))
            if not indices:
                # couldn't run
                if follow.all:
                    # check follow for impossibility
                    dests = set()
                    relevant = self.all_completed if follow.success_only else self.all_done
                    for m in follow.intersection(relevant):
                        dests.add(self.destinations[m])
                    if len(dests) > 1:
                        self.fail_unreachable(msg_id)
                        return False
                if targets:
                    # check blacklist+targets for impossibility
                    targets.difference_update(blacklist)
                    if not targets or not targets.intersection(self.targets):
                        self.fail_unreachable(msg_id)
                        return False
                return False
        else:
            indices = None
            
        self.submit_task(msg_id, raw_msg, targets, follow, timeout, indices)
        return True
            
    @logged
    def save_unmet(self, msg_id, raw_msg, targets, after, follow, timeout):
        """Save a message for later submission when its dependencies are met."""
        self.depending[msg_id] = [raw_msg,targets,after,follow,timeout]
        # track the ids in follow or after, but not those already finished
        for dep_id in after.union(follow).difference(self.all_done):
            if dep_id not in self.graph:
                self.graph[dep_id] = set()
            self.graph[dep_id].add(msg_id)
    
    @logged
    def submit_task(self, msg_id, raw_msg, targets, follow, timeout, indices=None):
        """Submit a task to any of a subset of our targets."""
        if indices:
            loads = [self.loads[i] for i in indices]
        else:
            loads = self.loads
        idx = self.scheme(loads)
        if indices:
            idx = indices[idx]
        target = self.targets[idx]
        # print (target, map(str, msg[:3]))
        self.engine_stream.send(target, flags=zmq.SNDMORE, copy=False)
        self.engine_stream.send_multipart(raw_msg, copy=False)
        self.add_job(idx)
        self.pending[target][msg_id] = (raw_msg, targets, MET, follow, timeout)
        content = dict(msg_id=msg_id, engine_id=target)
        self.session.send(self.mon_stream, 'task_destination', content=content, 
                        ident=['tracktask',self.session.session])
    
    #-----------------------------------------------------------------------
    # Result Handling
    #-----------------------------------------------------------------------
    @logged
    def dispatch_result(self, raw_msg):
        """dispatch method for result replies"""
        try:
            idents,msg = self.session.feed_identities(raw_msg, copy=False)
            msg = self.session.unpack_message(msg, content=False, copy=False)
        except:
            self.log.error("task::Invaid result: %s"%raw_msg, exc_info=True)
            return
        
        header = msg['header']
        if header.get('dependencies_met', True):
            success = (header['status'] == 'ok')
            self.handle_result(idents, msg['parent_header'], raw_msg, success)
            # send to Hub monitor
            self.mon_stream.send_multipart(['outtask']+raw_msg, copy=False)
        else:
            self.handle_unmet_dependency(idents, msg['parent_header'])
        
    @logged
    def handle_result(self, idents, parent, raw_msg, success=True):
        """handle a real task result, either success or failure"""
        # first, relay result to client
        engine = idents[0]
        client = idents[1]
        # swap_ids for XREP-XREP mirror
        raw_msg[:2] = [client,engine]
        # print (map(str, raw_msg[:4]))
        self.client_stream.send_multipart(raw_msg, copy=False)
        # now, update our data structures
        msg_id = parent['msg_id']
        self.blacklist.pop(msg_id, None)
        self.pending[engine].pop(msg_id)
        if success:
            self.completed[engine].add(msg_id)
            self.all_completed.add(msg_id)
        else:
            self.failed[engine].add(msg_id)
            self.all_failed.add(msg_id)
        self.all_done.add(msg_id)
        self.destinations[msg_id] = engine
        
        self.update_graph(msg_id, success)
        
    @logged
    def handle_unmet_dependency(self, idents, parent):
        """handle an unmet dependency"""
        engine = idents[0]
        msg_id = parent['msg_id']
        
        if msg_id not in self.blacklist:
            self.blacklist[msg_id] = set()
        self.blacklist[msg_id].add(engine)
        
        args = self.pending[engine].pop(msg_id)
        raw,targets,after,follow,timeout = args
        
        if self.blacklist[msg_id] == targets:
            self.depending[msg_id] = args
            return self.fail_unreachable(msg_id)
        
        elif not self.maybe_run(msg_id, *args):
            # resubmit failed, put it back in our dependency tree
            self.save_unmet(msg_id, *args)
        
    
    @logged
    def update_graph(self, dep_id, success=True):
        """dep_id just finished. Update our dependency
        graph and submit any jobs that just became runable."""
        # print ("\n\n***********")
        # pprint (dep_id)
        # pprint (self.graph)
        # pprint (self.depending)
        # pprint (self.all_completed)
        # pprint (self.all_failed)
        # print ("\n\n***********\n\n")
        if dep_id not in self.graph:
            return
        jobs = self.graph.pop(dep_id)
        
        for msg_id in jobs:
            raw_msg, targets, after, follow, timeout = self.depending[msg_id]
            # if dep_id in after:
            #     if after.all and (success or not after.success_only):
            #         after.remove(dep_id)
            
            if after.unreachable(self.all_failed) or follow.unreachable(self.all_failed):
                self.fail_unreachable(msg_id)
            
            elif after.check(self.all_completed, self.all_failed): # time deps met, maybe run
                if self.maybe_run(msg_id, raw_msg, targets, MET, follow, timeout):
                    
                    self.depending.pop(msg_id)
                    for mid in follow.union(after):
                        if mid in self.graph:
                            self.graph[mid].remove(msg_id)
    
    #----------------------------------------------------------------------
    # methods to be overridden by subclasses
    #----------------------------------------------------------------------
    
    def add_job(self, idx):
        """Called after self.targets[idx] just got the job with header.
        Override with subclasses.  The default ordering is simple LRU.
        The default loads are the number of outstanding jobs."""
        self.loads[idx] += 1
        for lis in (self.targets, self.loads):
            lis.append(lis.pop(idx))
            
    
    def finish_job(self, idx):
        """Called after self.targets[idx] just finished a job.
        Override with subclasses."""
        self.loads[idx] -= 1
    


def launch_scheduler(in_addr, out_addr, mon_addr, not_addr, config=None,logname='ZMQ', 
                            log_addr=None, loglevel=logging.DEBUG, scheme='lru'):
    from zmq.eventloop import ioloop
    from zmq.eventloop.zmqstream import ZMQStream
    
    ctx = zmq.Context()
    loop = ioloop.IOLoop()
    print (in_addr, out_addr, mon_addr, not_addr)
    ins = ZMQStream(ctx.socket(zmq.XREP),loop)
    ins.bind(in_addr)
    outs = ZMQStream(ctx.socket(zmq.XREP),loop)
    outs.bind(out_addr)
    mons = ZMQStream(ctx.socket(zmq.PUB),loop)
    mons.connect(mon_addr)
    nots = ZMQStream(ctx.socket(zmq.SUB),loop)
    nots.setsockopt(zmq.SUBSCRIBE, '')
    nots.connect(not_addr)
    
    scheme = globals().get(scheme, None)
    # setup logging
    if log_addr:
        connect_logger(logname, ctx, log_addr, root="scheduler", loglevel=loglevel)
    else:
        local_logger(logname, loglevel)
    
    scheduler = TaskScheduler(client_stream=ins, engine_stream=outs,
                            mon_stream=mons, notifier_stream=nots,
                            scheme=scheme, loop=loop, logname=logname,
                            config=config)
    scheduler.start()
    try:
        loop.start()
    except KeyboardInterrupt:
        print ("interrupted, exiting...", file=sys.__stderr__)


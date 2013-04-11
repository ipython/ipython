"""The Python scheduler for rich scheduling.

The Pure ZMQ scheduler does not allow routing schemes other than LRU,
nor does it check msg_id DAG dependencies. For those, a slightly slower
Python Scheduler exists.

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#----------------------------------------------------------------------
# Imports
#----------------------------------------------------------------------

import logging
import sys
import time

from collections import deque
from datetime import datetime
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
from IPython.config.application import Application
from IPython.config.loader import Config
from IPython.utils.traitlets import Instance, Dict, List, Set, Integer, Enum, CBytes
from IPython.utils.py3compat import cast_bytes

from IPython.parallel import error, util
from IPython.parallel.factory import SessionFactory
from IPython.parallel.util import connect_logger, local_logger

from .dependency import Dependency

@decorator
def logged(f,self,*args,**kwargs):
    # print ("#--------------------")
    self.log.debug("scheduler::%s(*%s,**%s)", f.func_name, args, kwargs)
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


class Job(object):
    """Simple container for a job"""
    def __init__(self, msg_id, raw_msg, idents, msg, header, metadata,
                    targets, after, follow, timeout):
        self.msg_id = msg_id
        self.raw_msg = raw_msg
        self.idents = idents
        self.msg = msg
        self.header = header
        self.metadata = metadata
        self.targets = targets
        self.after = after
        self.follow = follow
        self.timeout = timeout
        self.removed = False # used for lazy-delete from sorted queue
        
        self.timestamp = time.time()
        self.blacklist = set()

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __cmp__(self, other):
        return cmp(self.timestamp, other.timestamp)

    @property
    def dependents(self):
        return self.follow.union(self.after)

class TaskScheduler(SessionFactory):
    """Python TaskScheduler object.

    This is the simplest object that supports msg_id based
    DAG dependencies. *Only* task msg_ids are checked, not
    msg_ids of jobs submitted via the MUX queue.

    """

    hwm = Integer(1, config=True,
        help="""specify the High Water Mark (HWM) for the downstream
        socket in the Task scheduler. This is the maximum number
        of allowed outstanding tasks on each engine.
        
        The default (1) means that only one task can be outstanding on each
        engine.  Setting TaskScheduler.hwm=0 means there is no limit, and the
        engines continue to be assigned tasks while they are working,
        effectively hiding network latency behind computation, but can result
        in an imbalance of work when submitting many heterogenous tasks all at
        once.  Any positive value greater than one is a compromise between the
        two.

        """
    )
    scheme_name = Enum(('leastload', 'pure', 'lru', 'plainrandom', 'weighted', 'twobin'),
        'leastload', config=True, allow_none=False,
        help="""select the task scheduler scheme  [default: Python LRU]
        Options are: 'pure', 'lru', 'plainrandom', 'weighted', 'twobin','leastload'"""
    )
    def _scheme_name_changed(self, old, new):
        self.log.debug("Using scheme %r"%new)
        self.scheme = globals()[new]

    # input arguments:
    scheme = Instance(FunctionType) # function for determining the destination
    def _scheme_default(self):
        return leastload
    client_stream = Instance(zmqstream.ZMQStream) # client-facing stream
    engine_stream = Instance(zmqstream.ZMQStream) # engine-facing stream
    notifier_stream = Instance(zmqstream.ZMQStream) # hub-facing sub stream
    mon_stream = Instance(zmqstream.ZMQStream) # hub-facing pub stream
    query_stream = Instance(zmqstream.ZMQStream) # hub-facing DEALER stream

    # internals:
    queue = Instance(deque) # sorted list of Jobs
    def _queue_default(self):
        return deque()
    queue_map = Dict() # dict by msg_id of Jobs (for O(1) access to the Queue)
    graph = Dict() # dict by msg_id of [ msg_ids that depend on key ]
    retries = Dict() # dict by msg_id of retries remaining (non-neg ints)
    # waiting = List() # list of msg_ids ready to run, but haven't due to HWM
    pending = Dict() # dict by engine_uuid of submitted tasks
    completed = Dict() # dict by engine_uuid of completed tasks
    failed = Dict() # dict by engine_uuid of failed tasks
    destinations = Dict() # dict by msg_id of engine_uuids where jobs ran (reverse of completed+failed)
    clients = Dict() # dict by msg_id for who submitted the task
    targets = List() # list of target IDENTs
    loads = List() # list of engine loads
    # full = Set() # set of IDENTs that have HWM outstanding tasks
    all_completed = Set() # set of all completed tasks
    all_failed = Set() # set of all failed tasks
    all_done = Set() # set of all finished tasks=union(completed,failed)
    all_ids = Set() # set of all submitted task IDs

    ident = CBytes() # ZMQ identity. This should just be self.session.session
                     # but ensure Bytes
    def _ident_default(self):
        return self.session.bsession

    def start(self):
        self.query_stream.on_recv(self.dispatch_query_reply)
        self.session.send(self.query_stream, "connection_request", {})
        
        self.engine_stream.on_recv(self.dispatch_result, copy=False)
        self.client_stream.on_recv(self.dispatch_submission, copy=False)

        self._notification_handlers = dict(
            registration_notification = self._register_engine,
            unregistration_notification = self._unregister_engine
        )
        self.notifier_stream.on_recv(self.dispatch_notification)
        self.log.info("Scheduler started [%s]" % self.scheme_name)

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
    
    
    def dispatch_query_reply(self, msg):
        """handle reply to our initial connection request"""
        try:
            idents,msg = self.session.feed_identities(msg)
        except ValueError:
            self.log.warn("task::Invalid Message: %r",msg)
            return
        try:
            msg = self.session.unserialize(msg)
        except ValueError:
            self.log.warn("task::Unauthorized message from: %r"%idents)
            return
        
        content = msg['content']
        for uuid in content.get('engines', {}).values():
            self._register_engine(cast_bytes(uuid))

    
    @util.log_errors
    def dispatch_notification(self, msg):
        """dispatch register/unregister events."""
        try:
            idents,msg = self.session.feed_identities(msg)
        except ValueError:
            self.log.warn("task::Invalid Message: %r",msg)
            return
        try:
            msg = self.session.unserialize(msg)
        except ValueError:
            self.log.warn("task::Unauthorized message from: %r"%idents)
            return

        msg_type = msg['header']['msg_type']

        handler = self._notification_handlers.get(msg_type, None)
        if handler is None:
            self.log.error("Unhandled message type: %r"%msg_type)
        else:
            try:
                handler(cast_bytes(msg['content']['uuid']))
            except Exception:
                self.log.error("task::Invalid notification msg: %r", msg, exc_info=True)

    def _register_engine(self, uid):
        """New engine with ident `uid` became available."""
        # head of the line:
        self.targets.insert(0,uid)
        self.loads.insert(0,0)

        # initialize sets
        self.completed[uid] = set()
        self.failed[uid] = set()
        self.pending[uid] = {}

        # rescan the graph:
        self.update_graph(None)

    def _unregister_engine(self, uid):
        """Existing engine with ident `uid` became unavailable."""
        if len(self.targets) == 1:
            # this was our only engine
            pass

        # handle any potentially finished tasks:
        self.engine_stream.flush()

        # don't pop destinations, because they might be used later
        # map(self.destinations.pop, self.completed.pop(uid))
        # map(self.destinations.pop, self.failed.pop(uid))

        # prevent this engine from receiving work
        idx = self.targets.index(uid)
        self.targets.pop(idx)
        self.loads.pop(idx)

        # wait 5 seconds before cleaning up pending jobs, since the results might
        # still be incoming
        if self.pending[uid]:
            dc = ioloop.DelayedCallback(lambda : self.handle_stranded_tasks(uid), 5000, self.loop)
            dc.start()
        else:
            self.completed.pop(uid)
            self.failed.pop(uid)


    def handle_stranded_tasks(self, engine):
        """Deal with jobs resident in an engine that died."""
        lost = self.pending[engine]
        for msg_id in lost.keys():
            if msg_id not in self.pending[engine]:
                # prevent double-handling of messages
                continue

            raw_msg = lost[msg_id].raw_msg
            idents,msg = self.session.feed_identities(raw_msg, copy=False)
            parent = self.session.unpack(msg[1].bytes)
            idents = [engine, idents[0]]

            # build fake error reply
            try:
                raise error.EngineError("Engine %r died while running task %r"%(engine, msg_id))
            except:
                content = error.wrap_exception()
            # build fake metadata
            md = dict(
                status=u'error',
                engine=engine,
                date=datetime.now(),
            )
            msg = self.session.msg('apply_reply', content, parent=parent, metadata=md)
            raw_reply = map(zmq.Message, self.session.serialize(msg, ident=idents))
            # and dispatch it
            self.dispatch_result(raw_reply)

        # finally scrub completed/failed lists
        self.completed.pop(engine)
        self.failed.pop(engine)


    #-----------------------------------------------------------------------
    # Job Submission
    #-----------------------------------------------------------------------
    

    @util.log_errors
    def dispatch_submission(self, raw_msg):
        """Dispatch job submission to appropriate handlers."""
        # ensure targets up to date:
        self.notifier_stream.flush()
        try:
            idents, msg = self.session.feed_identities(raw_msg, copy=False)
            msg = self.session.unserialize(msg, content=False, copy=False)
        except Exception:
            self.log.error("task::Invaid task msg: %r"%raw_msg, exc_info=True)
            return


        # send to monitor
        self.mon_stream.send_multipart([b'intask']+raw_msg, copy=False)

        header = msg['header']
        md = msg['metadata']
        msg_id = header['msg_id']
        self.all_ids.add(msg_id)

        # get targets as a set of bytes objects
        # from a list of unicode objects
        targets = md.get('targets', [])
        targets = map(cast_bytes, targets)
        targets = set(targets)

        retries = md.get('retries', 0)
        self.retries[msg_id] = retries

        # time dependencies
        after = md.get('after', None)
        if after:
            after = Dependency(after)
            if after.all:
                if after.success:
                    after = Dependency(after.difference(self.all_completed),
                                success=after.success,
                                failure=after.failure,
                                all=after.all,
                    )
                if after.failure:
                    after = Dependency(after.difference(self.all_failed),
                                success=after.success,
                                failure=after.failure,
                                all=after.all,
                    )
            if after.check(self.all_completed, self.all_failed):
                # recast as empty set, if `after` already met,
                # to prevent unnecessary set comparisons
                after = MET
        else:
            after = MET

        # location dependencies
        follow = Dependency(md.get('follow', []))

        # turn timeouts into datetime objects:
        timeout = md.get('timeout', None)
        if timeout:
            timeout = time.time() + float(timeout)

        job = Job(msg_id=msg_id, raw_msg=raw_msg, idents=idents, msg=msg,
                 header=header, targets=targets, after=after, follow=follow,
                 timeout=timeout, metadata=md,
        )
        if timeout:
            # schedule timeout callback
            self.loop.add_timeout(timeout, lambda : self.job_timeout(job))
        
        # validate and reduce dependencies:
        for dep in after,follow:
            if not dep: # empty dependency
                continue
            # check valid:
            if msg_id in dep or dep.difference(self.all_ids):
                self.queue_map[msg_id] = job
                return self.fail_unreachable(msg_id, error.InvalidDependency)
            # check if unreachable:
            if dep.unreachable(self.all_completed, self.all_failed):
                self.queue_map[msg_id] = job
                return self.fail_unreachable(msg_id)

        if after.check(self.all_completed, self.all_failed):
            # time deps already met, try to run
            if not self.maybe_run(job):
                # can't run yet
                if msg_id not in self.all_failed:
                    # could have failed as unreachable
                    self.save_unmet(job)
        else:
            self.save_unmet(job)

    def job_timeout(self, job):
        """callback for a job's timeout.
        
        The job may or may not have been run at this point.
        """
        now = time.time()
        if job.timeout >= (now + 1):
            self.log.warn("task %s timeout fired prematurely: %s > %s",
                job.msg_id, job.timeout, now
            )
        if job.msg_id in self.queue_map:
            # still waiting, but ran out of time
            self.log.info("task %r timed out", job.msg_id)
            self.fail_unreachable(job.msg_id, error.TaskTimeout)

    def fail_unreachable(self, msg_id, why=error.ImpossibleDependency):
        """a task has become unreachable, send a reply with an ImpossibleDependency
        error."""
        if msg_id not in self.queue_map:
            self.log.error("task %r already failed!", msg_id)
            return
        job = self.queue_map.pop(msg_id)
        # lazy-delete from the queue
        job.removed = True
        for mid in job.dependents:
            if mid in self.graph:
                self.graph[mid].remove(msg_id)

        try:
            raise why()
        except:
            content = error.wrap_exception()
        self.log.debug("task %r failing as unreachable with: %s", msg_id, content['ename'])

        self.all_done.add(msg_id)
        self.all_failed.add(msg_id)

        msg = self.session.send(self.client_stream, 'apply_reply', content,
                                                parent=job.header, ident=job.idents)
        self.session.send(self.mon_stream, msg, ident=[b'outtask']+job.idents)

        self.update_graph(msg_id, success=False)

    def available_engines(self):
        """return a list of available engine indices based on HWM"""
        if not self.hwm:
            return range(len(self.targets))
        available = []
        for idx in range(len(self.targets)):
            if self.loads[idx] < self.hwm:
                available.append(idx)
        return available

    def maybe_run(self, job):
        """check location dependencies, and run if they are met."""
        msg_id = job.msg_id
        self.log.debug("Attempting to assign task %s", msg_id)
        available = self.available_engines()
        if not available:
            # no engines, definitely can't run
            return False
        
        if job.follow or job.targets or job.blacklist or self.hwm:
            # we need a can_run filter
            def can_run(idx):
                # check hwm
                if self.hwm and self.loads[idx] == self.hwm:
                    return False
                target = self.targets[idx]
                # check blacklist
                if target in job.blacklist:
                    return False
                # check targets
                if job.targets and target not in job.targets:
                    return False
                # check follow
                return job.follow.check(self.completed[target], self.failed[target])

            indices = filter(can_run, available)

            if not indices:
                # couldn't run
                if job.follow.all:
                    # check follow for impossibility
                    dests = set()
                    relevant = set()
                    if job.follow.success:
                        relevant = self.all_completed
                    if job.follow.failure:
                        relevant = relevant.union(self.all_failed)
                    for m in job.follow.intersection(relevant):
                        dests.add(self.destinations[m])
                    if len(dests) > 1:
                        self.queue_map[msg_id] = job
                        self.fail_unreachable(msg_id)
                        return False
                if job.targets:
                    # check blacklist+targets for impossibility
                    job.targets.difference_update(job.blacklist)
                    if not job.targets or not job.targets.intersection(self.targets):
                        self.queue_map[msg_id] = job
                        self.fail_unreachable(msg_id)
                        return False
                return False
        else:
            indices = None

        self.submit_task(job, indices)
        return True

    def save_unmet(self, job):
        """Save a message for later submission when its dependencies are met."""
        msg_id = job.msg_id
        self.log.debug("Adding task %s to the queue", msg_id)
        self.queue_map[msg_id] = job
        self.queue.append(job)
        # track the ids in follow or after, but not those already finished
        for dep_id in job.after.union(job.follow).difference(self.all_done):
            if dep_id not in self.graph:
                self.graph[dep_id] = set()
            self.graph[dep_id].add(msg_id)

    def submit_task(self, job, indices=None):
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
        # send job to the engine
        self.engine_stream.send(target, flags=zmq.SNDMORE, copy=False)
        self.engine_stream.send_multipart(job.raw_msg, copy=False)
        # update load
        self.add_job(idx)
        self.pending[target][job.msg_id] = job
        # notify Hub
        content = dict(msg_id=job.msg_id, engine_id=target.decode('ascii'))
        self.session.send(self.mon_stream, 'task_destination', content=content,
                        ident=[b'tracktask',self.ident])


    #-----------------------------------------------------------------------
    # Result Handling
    #-----------------------------------------------------------------------
    
    
    @util.log_errors
    def dispatch_result(self, raw_msg):
        """dispatch method for result replies"""
        try:
            idents,msg = self.session.feed_identities(raw_msg, copy=False)
            msg = self.session.unserialize(msg, content=False, copy=False)
            engine = idents[0]
            try:
                idx = self.targets.index(engine)
            except ValueError:
                pass # skip load-update for dead engines
            else:
                self.finish_job(idx)
        except Exception:
            self.log.error("task::Invaid result: %r", raw_msg, exc_info=True)
            return

        md = msg['metadata']
        parent = msg['parent_header']
        if md.get('dependencies_met', True):
            success = (md['status'] == 'ok')
            msg_id = parent['msg_id']
            retries = self.retries[msg_id]
            if not success and retries > 0:
                # failed
                self.retries[msg_id] = retries - 1
                self.handle_unmet_dependency(idents, parent)
            else:
                del self.retries[msg_id]
                # relay to client and update graph
                self.handle_result(idents, parent, raw_msg, success)
                # send to Hub monitor
                self.mon_stream.send_multipart([b'outtask']+raw_msg, copy=False)
        else:
            self.handle_unmet_dependency(idents, parent)

    def handle_result(self, idents, parent, raw_msg, success=True):
        """handle a real task result, either success or failure"""
        # first, relay result to client
        engine = idents[0]
        client = idents[1]
        # swap_ids for ROUTER-ROUTER mirror
        raw_msg[:2] = [client,engine]
        # print (map(str, raw_msg[:4]))
        self.client_stream.send_multipart(raw_msg, copy=False)
        # now, update our data structures
        msg_id = parent['msg_id']
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

    def handle_unmet_dependency(self, idents, parent):
        """handle an unmet dependency"""
        engine = idents[0]
        msg_id = parent['msg_id']

        job = self.pending[engine].pop(msg_id)
        job.blacklist.add(engine)

        if job.blacklist == job.targets:
            self.queue_map[msg_id] = job
            self.fail_unreachable(msg_id)
        elif not self.maybe_run(job):
            # resubmit failed
            if msg_id not in self.all_failed:
                # put it back in our dependency tree
                self.save_unmet(job)

        if self.hwm:
            try:
                idx = self.targets.index(engine)
            except ValueError:
                pass # skip load-update for dead engines
            else:
                if self.loads[idx] == self.hwm-1:
                    self.update_graph(None)

    def update_graph(self, dep_id=None, success=True):
        """dep_id just finished. Update our dependency
        graph and submit any jobs that just became runnable.

        Called with dep_id=None to update entire graph for hwm, but without finishing a task.
        """
        # print ("\n\n***********")
        # pprint (dep_id)
        # pprint (self.graph)
        # pprint (self.queue_map)
        # pprint (self.all_completed)
        # pprint (self.all_failed)
        # print ("\n\n***********\n\n")
        # update any jobs that depended on the dependency
        msg_ids = self.graph.pop(dep_id, [])

        # recheck *all* jobs if
        # a) we have HWM and an engine just become no longer full
        # or b) dep_id was given as None
        
        if dep_id is None or self.hwm and any( [ load==self.hwm-1 for load in self.loads ]):
            jobs = self.queue
            using_queue = True
        else:
            using_queue = False
            jobs = deque(sorted( self.queue_map[msg_id] for msg_id in msg_ids ))
        
        to_restore = []
        while jobs:
            job = jobs.popleft()
            if job.removed:
                continue
            msg_id = job.msg_id
            
            put_it_back = True
            
            if job.after.unreachable(self.all_completed, self.all_failed)\
                    or job.follow.unreachable(self.all_completed, self.all_failed):
                self.fail_unreachable(msg_id)
                put_it_back = False

            elif job.after.check(self.all_completed, self.all_failed): # time deps met, maybe run
                if self.maybe_run(job):
                    put_it_back = False
                    self.queue_map.pop(msg_id)
                    for mid in job.dependents:
                        if mid in self.graph:
                            self.graph[mid].remove(msg_id)
                    
                    # abort the loop if we just filled up all of our engines.
                    # avoids an O(N) operation in situation of full queue,
                    # where graph update is triggered as soon as an engine becomes
                    # non-full, and all tasks after the first are checked,
                    # even though they can't run.
                    if not self.available_engines():
                        break
            
            if using_queue and put_it_back:
                # popped a job from the queue but it neither ran nor failed,
                # so we need to put it back when we are done
                # make sure to_restore preserves the same ordering
                to_restore.append(job)
        
        # put back any tasks we popped but didn't run
        if using_queue:
            self.queue.extendleft(to_restore)
    
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



def launch_scheduler(in_addr, out_addr, mon_addr, not_addr, reg_addr, config=None,
                        logname='root', log_url=None, loglevel=logging.DEBUG,
                        identity=b'task', in_thread=False):

    ZMQStream = zmqstream.ZMQStream

    if config:
        # unwrap dict back into Config
        config = Config(config)

    if in_thread:
        # use instance() to get the same Context/Loop as our parent
        ctx = zmq.Context.instance()
        loop = ioloop.IOLoop.instance()
    else:
        # in a process, don't use instance()
        # for safety with multiprocessing
        ctx = zmq.Context()
        loop = ioloop.IOLoop()
    ins = ZMQStream(ctx.socket(zmq.ROUTER),loop)
    ins.setsockopt(zmq.IDENTITY, identity + b'_in')
    ins.bind(in_addr)

    outs = ZMQStream(ctx.socket(zmq.ROUTER),loop)
    outs.setsockopt(zmq.IDENTITY, identity + b'_out')
    outs.bind(out_addr)
    mons = zmqstream.ZMQStream(ctx.socket(zmq.PUB),loop)
    mons.connect(mon_addr)
    nots = zmqstream.ZMQStream(ctx.socket(zmq.SUB),loop)
    nots.setsockopt(zmq.SUBSCRIBE, b'')
    nots.connect(not_addr)
    
    querys = ZMQStream(ctx.socket(zmq.DEALER),loop)
    querys.connect(reg_addr)
    
    # setup logging.
    if in_thread:
        log = Application.instance().log
    else:
        if log_url:
            log = connect_logger(logname, ctx, log_url, root="scheduler", loglevel=loglevel)
        else:
            log = local_logger(logname, loglevel)

    scheduler = TaskScheduler(client_stream=ins, engine_stream=outs,
                            mon_stream=mons, notifier_stream=nots,
                            query_stream=querys,
                            loop=loop, log=log,
                            config=config)
    scheduler.start()
    if not in_thread:
        try:
            loop.start()
        except KeyboardInterrupt:
            scheduler.log.critical("Interrupted, exiting...")


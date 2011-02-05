"""The Python scheduler for rich scheduling.

The Pure ZMQ scheduler does not allow routing schemes other than LRU,
nor does it check msg_id DAG dependencies. For those, a slightly slower
Python Scheduler exists.
"""

#----------------------------------------------------------------------
# Imports
#----------------------------------------------------------------------

from __future__ import print_function
from random import randint,random
import logging
from types import FunctionType

try:
    import numpy
except ImportError:
    numpy = None

import zmq
from zmq.eventloop import ioloop, zmqstream

# local imports
from IPython.external.decorator import decorator
from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Instance, Dict, List, Set

from client import Client
from dependency import Dependency
import streamsession as ss
from entry_point import connect_logger, local_logger


@decorator
def logged(f,self,*args,**kwargs):
    # print ("#--------------------")
    logging.debug("scheduler::%s(*%s,**%s)"%(f.func_name, args, kwargs))
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
class TaskScheduler(Configurable):
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
    io_loop = Instance(ioloop.IOLoop)
    
    # internals:
    dependencies = Dict() # dict by msg_id of [ msg_ids that depend on key ]
    depending = Dict() # dict by msg_id of (msg_id, raw_msg, after, follow)
    pending = Dict() # dict by engine_uuid of submitted tasks
    completed = Dict() # dict by engine_uuid of completed tasks
    clients = Dict() # dict by msg_id for who submitted the task
    targets = List() # list of target IDENTs
    loads = List() # list of engine loads
    all_done = Set() # set of all completed tasks
    blacklist = Dict() # dict by msg_id of locations where a job has encountered UnmetDependency
    session = Instance(ss.StreamSession)
    
    
    def __init__(self, **kwargs):
        super(TaskScheduler, self).__init__(**kwargs)
        
        self.session = ss.StreamSession(username="TaskScheduler")
        
        self.engine_stream.on_recv(self.dispatch_result, copy=False)
        self._notification_handlers = dict(
            registration_notification = self._register_engine,
            unregistration_notification = self._unregister_engine
        )
        self.notifier_stream.on_recv(self.dispatch_notification)
        logging.info("Scheduler started...%r"%self)
    
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
                logging.error("task::Invalid notification msg: %s"%msg)
    
    @logged
    def _register_engine(self, uid):
        """New engine with ident `uid` became available."""
        # head of the line:
        self.targets.insert(0,uid)
        self.loads.insert(0,0)
        # initialize sets
        self.completed[uid] = set()
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
        lost = self.pending.pop(uid)
        
        idx = self.targets.index(uid)
        self.targets.pop(idx)
        self.loads.pop(idx)
        
        self.handle_stranded_tasks(lost)
    
    def handle_stranded_tasks(self, lost):
        """Deal with jobs resident in an engine that died."""
        # TODO: resubmit the tasks?
        for msg_id in lost:
            pass
    
    
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
        except Exception as e:
            logging.error("task::Invaid msg: %s"%msg)
            return
        
        # send to monitor
        self.mon_stream.send_multipart(['intask']+raw_msg, copy=False)
        
        msg = self.session.unpack_message(msg, content=False, copy=False)
        header = msg['header']
        msg_id = header['msg_id']
        
        # time dependencies
        after = Dependency(header.get('after', []))
        if after.mode == 'all':
            after.difference_update(self.all_done)
        if after.check(self.all_done):
            # recast as empty set, if `after` already met,
            # to prevent unnecessary set comparisons
            after = Dependency([])
        
        # location dependencies
        follow = Dependency(header.get('follow', []))
        if len(after) == 0:
            # time deps already met, try to run
            if not self.maybe_run(msg_id, raw_msg, follow):
                # can't run yet
                self.save_unmet(msg_id, raw_msg, after, follow)
        else:
            self.save_unmet(msg_id, raw_msg, after, follow)
    
    @logged
    def maybe_run(self, msg_id, raw_msg, follow=None):
        """check location dependencies, and run if they are met."""
            
        if follow:
            def can_run(idx):
                target = self.targets[idx]
                return target not in self.blacklist.get(msg_id, []) and\
                        follow.check(self.completed[target])
            
            indices = filter(can_run, range(len(self.targets)))
            if not indices:
                return False
        else:
            indices = None
            
        self.submit_task(msg_id, raw_msg, indices)
        return True
            
    @logged
    def save_unmet(self, msg_id, msg, after, follow):
        """Save a message for later submission when its dependencies are met."""
        self.depending[msg_id] = (msg_id,msg,after,follow)
        # track the ids in both follow/after, but not those already completed
        for dep_id in after.union(follow).difference(self.all_done):
            if dep_id not in self.dependencies:
                self.dependencies[dep_id] = set()
            self.dependencies[dep_id].add(msg_id)
    
    @logged
    def submit_task(self, msg_id, msg, follow=None, indices=None):
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
        self.engine_stream.send_multipart(msg, copy=False)
        self.add_job(idx)
        self.pending[target][msg_id] = (msg, follow)
        content = dict(msg_id=msg_id, engine_id=target)
        self.session.send(self.mon_stream, 'task_destination', content=content, 
                        ident=['tracktask',self.session.session])
    
    #-----------------------------------------------------------------------
    # Result Handling
    #-----------------------------------------------------------------------
    @logged
    def dispatch_result(self, raw_msg):
        try:
            idents,msg = self.session.feed_identities(raw_msg, copy=False)
        except Exception as e:
            logging.error("task::Invaid result: %s"%msg)
            return
        msg = self.session.unpack_message(msg, content=False, copy=False)
        header = msg['header']
        if header.get('dependencies_met', True):
            self.handle_result_success(idents, msg['parent_header'], raw_msg)
            # send to monitor
            self.mon_stream.send_multipart(['outtask']+raw_msg, copy=False)
        else:
            self.handle_unmet_dependency(idents, msg['parent_header'])
        
    @logged
    def handle_result_success(self, idents, parent, raw_msg):
        # first, relay result to client
        engine = idents[0]
        client = idents[1]
        # swap_ids for XREP-XREP mirror
        raw_msg[:2] = [client,engine]
        # print (map(str, raw_msg[:4]))
        self.client_stream.send_multipart(raw_msg, copy=False)
        # now, update our data structures
        msg_id = parent['msg_id']
        self.pending[engine].pop(msg_id)
        self.completed[engine].add(msg_id)
        self.all_done.add(msg_id)
        
        self.update_dependencies(msg_id)
        
    @logged
    def handle_unmet_dependency(self, idents, parent):
        engine = idents[0]
        msg_id = parent['msg_id']
        if msg_id not in self.blacklist:
            self.blacklist[msg_id] = set()
        self.blacklist[msg_id].add(engine)
        raw_msg,follow = self.pending[engine].pop(msg_id)
        if not self.maybe_run(msg_id, raw_msg, follow):
            # resubmit failed, put it back in our dependency tree
            self.save_unmet(msg_id, raw_msg, Dependency(), follow)
        pass
    @logged
    def update_dependencies(self, dep_id):
        """dep_id just finished. Update our dependency
        table and submit any jobs that just became runable."""
        
        if dep_id not in self.dependencies:
            return
        jobs = self.dependencies.pop(dep_id)
        for job in jobs:
            msg_id, raw_msg, after, follow = self.depending[job]
            if dep_id in after:
                after.remove(dep_id)
            if not after: # time deps met, maybe run
                if self.maybe_run(msg_id, raw_msg, follow):
                    self.depending.pop(job)
                    for mid in follow:
                        if mid in self.dependencies:
                            self.dependencies[mid].remove(msg_id)
    
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
    


def launch_scheduler(in_addr, out_addr, mon_addr, not_addr, log_addr=None, loglevel=logging.DEBUG, scheme='weighted'):
    from zmq.eventloop import ioloop
    from zmq.eventloop.zmqstream import ZMQStream
    
    ctx = zmq.Context()
    loop = ioloop.IOLoop()
    
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
        connect_logger(ctx, log_addr, root="scheduler", loglevel=loglevel)
    else:
        local_logger(loglevel)
    
    scheduler = TaskScheduler(client_stream=ins, engine_stream=outs,
                            mon_stream=mons,notifier_stream=nots,
                            scheme=scheme,io_loop=loop)
    
    try:
        loop.start()
    except KeyboardInterrupt:
        print ("interrupted, exiting...", file=sys.__stderr__)


if __name__ == '__main__':
    iface = 'tcp://127.0.0.1:%i'
    launch_scheduler(iface%12345,iface%1236,iface%12347,iface%12348)

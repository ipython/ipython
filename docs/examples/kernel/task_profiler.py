#!/usr/bin/env python
"""Test the performance of the task farming system.

This script submits a set of tasks to the TaskClient.  The tasks
are basically just a time.sleep(t), where t is a random number between
two limits that can be configured at the command line.  To run 
the script there must first be an IPython controller and engines running::

    ipcluster -n 16

A good test to run with 16 engines is::

    python task_profiler.py -n 128 -t 0.01 -T 1.0

This should show a speedup of 13-14x.  The limitation here is that the 
overhead of a single task is about 0.001-0.01 seconds.
"""
import random, sys
from optparse import OptionParser

from IPython.genutils import time
from IPython.kernel import client

def main():
    parser = OptionParser()
    parser.set_defaults(n=100)
    parser.set_defaults(tmin=1)
    parser.set_defaults(tmax=60)
    parser.set_defaults(controller='localhost')
    parser.set_defaults(meport=10105)
    parser.set_defaults(tport=10113)
    
    parser.add_option("-n", type='int', dest='n',
        help='the number of tasks to run')
    parser.add_option("-t", type='float', dest='tmin', 
        help='the minimum task length in seconds')
    parser.add_option("-T", type='float', dest='tmax',
        help='the maximum task length in seconds')
    parser.add_option("-c", type='string', dest='controller',
        help='the address of the controller')
    parser.add_option("-p", type='int', dest='meport',
        help="the port on which the controller listens for the MultiEngine/RemoteController client")
    parser.add_option("-P", type='int', dest='tport',
        help="the port on which the controller listens for the TaskClient client")
    
    (opts, args) = parser.parse_args()
    assert opts.tmax >= opts.tmin, "tmax must not be smaller than tmin"
    
    rc = client.MultiEngineClient()
    tc = client.TaskClient()
    print tc.task_controller
    rc.block=True
    nengines = len(rc.get_ids())
    rc.execute('from IPython.genutils import time')

    # the jobs should take a random time within a range
    times = [random.random()*(opts.tmax-opts.tmin)+opts.tmin for i in range(opts.n)]
    tasks = [client.StringTask("time.sleep(%f)"%t) for t in times]
    stime = sum(times)
    
    print "executing %i tasks, totalling %.1f secs on %i engines"%(opts.n, stime, nengines)
    time.sleep(1)
    start = time.time()
    taskids = [tc.run(t) for t in tasks]
    tc.barrier(taskids)
    stop = time.time()

    ptime = stop-start
    scale = stime/ptime
    
    print "executed %.1f secs in %.1f secs"%(stime, ptime)
    print "%.3fx parallel performance on %i engines"%(scale, nengines)
    print "%.1f%% of theoretical max"%(100*scale/nengines)


if __name__ == '__main__':
    main()

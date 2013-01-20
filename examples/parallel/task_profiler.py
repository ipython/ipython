#!/usr/bin/env python
"""Test the performance of the task farming system.

This script submits a set of tasks via a LoadBalancedView.  The tasks
are basically just a time.sleep(t), where t is a random number between
two limits that can be configured at the command line.  To run
the script there must first be an IPython controller and engines running::

    ipcluster start -n 16

A good test to run with 16 engines is::

    python task_profiler.py -n 128 -t 0.01 -T 1.0

This should show a speedup of 13-14x.  The limitation here is that the
overhead of a single task is about 0.001-0.01 seconds.
"""
import random, sys
from optparse import OptionParser

from IPython.utils.timing import time
from IPython.parallel import Client

def main():
    parser = OptionParser()
    parser.set_defaults(n=100)
    parser.set_defaults(tmin=1e-3)
    parser.set_defaults(tmax=1)
    parser.set_defaults(profile='default')

    parser.add_option("-n", type='int', dest='n',
        help='the number of tasks to run')
    parser.add_option("-t", type='float', dest='tmin',
        help='the minimum task length in seconds')
    parser.add_option("-T", type='float', dest='tmax',
        help='the maximum task length in seconds')
    parser.add_option("-p", '--profile', type='str', dest='profile',
        help="the cluster profile [default: 'default']")

    (opts, args) = parser.parse_args()
    assert opts.tmax >= opts.tmin, "tmax must not be smaller than tmin"

    rc = Client()
    view = rc.load_balanced_view()
    print(view)
    rc.block=True
    nengines = len(rc.ids)
    with rc[:].sync_imports():
        from IPython.utils.timing import time

    # the jobs should take a random time within a range
    times = [random.random()*(opts.tmax-opts.tmin)+opts.tmin for i in range(opts.n)]
    stime = sum(times)

    print("executing %i tasks, totalling %.1f secs on %i engines"%(opts.n, stime, nengines))
    time.sleep(1)
    start = time.time()
    amr = view.map(time.sleep, times)
    amr.get()
    stop = time.time()

    ptime = stop-start
    scale = stime/ptime

    print("executed %.1f secs in %.1f secs"%(stime, ptime))
    print("%.3fx parallel performance on %i engines"%(scale, nengines))
    print("%.1f%% of theoretical max"%(100*scale/nengines))


if __name__ == '__main__':
    main()

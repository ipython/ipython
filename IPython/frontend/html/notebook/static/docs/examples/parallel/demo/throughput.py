from __future__ import print_function

import time
import numpy as np
from IPython import parallel

nlist = map(int, np.logspace(2,9,16,base=2))
nlist2 = map(int, np.logspace(2,8,15,base=2))
tlist = map(int, np.logspace(7,22,16,base=2))
nt = 16
def wait(t=0):
    import time
    time.sleep(t)

def echo(s=''):
    return s

def time_throughput(nmessages, t=0, f=wait):
    client = parallel.Client()
    view = client.load_balanced_view()
    # do one ping before starting timing
    if f is echo:
        t = np.random.random(t/8)
    view.apply_sync(echo, '')
    client.spin()
    tic = time.time()
    for i in xrange(nmessages):
        view.apply(f, t)
    lap = time.time()
    client.wait()
    toc = time.time()
    return lap-tic, toc-tic


def do_runs(nlist,t=0,f=wait, trials=2, runner=time_throughput):
    A = np.zeros((len(nlist),2))
    for i,n in enumerate(nlist):
        t1 = t2 = 0
        for _ in range(trials):
            time.sleep(.25)
            ts = runner(n,t,f)
            t1 += ts[0]
            t2 += ts[1]
        t1 /= trials
        t2 /= trials
        A[i] = (t1,t2)
        A[i] = n/A[i]
        print(n,A[i])
    return A

def do_echo(n,tlist=[0],f=echo, trials=2, runner=time_throughput):
    A = np.zeros((len(tlist),2))
    for i,t in enumerate(tlist):
        t1 = t2 = 0
        for _ in range(trials):
            time.sleep(.25)
            ts = runner(n,t,f)
            t1 += ts[0]
            t2 += ts[1]
        t1 /= trials
        t2 /= trials
        A[i] = (t1,t2)
        A[i] = n/A[i]
        print(t,A[i])
    return A
    

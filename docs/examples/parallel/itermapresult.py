"""Example of iteration through AsyncMapResult, without waiting for all results

Authors
-------
* MinRK
"""
import time

from IPython import parallel

# create client & view
rc = parallel.Client()
dv = rc[:]
v = rc.load_balanced_view()

# scatter 'id', so id=0,1,2 on engines 0,1,2
dv.scatter('id', rc.ids, flatten=True)
print "Engine IDs: ", dv['id']

# create a Reference to `id`. This will be a different value on each engine
ref = parallel.Reference('id')
print "sleeping for `id` seconds on each engine"
tic = time.time()
ar = dv.apply(time.sleep, ref)
for i,r in enumerate(ar):
    print "%i: %.3f"%(i, time.time()-tic)

def sleep_here(t):
    import time
    time.sleep(t)
    return id,t

# one call per task
print "running with one call per task"
amr = v.map(sleep_here, [.01*t for t in range(100)])
tic = time.time()
for i,r in enumerate(amr):
    print "task %i on engine %i: %.3f" % (i, r[0], time.time()-tic)

print "running with four calls per task"
# with chunksize, we can have four calls per task
amr = v.map(sleep_here, [.01*t for t in range(100)], chunksize=4)
tic = time.time()
for i,r in enumerate(amr):
    print "task %i on engine %i: %.3f" % (i, r[0], time.time()-tic)

print "running with two calls per task, with unordered results"
# We can even iterate through faster results first, with ordered=False
amr = v.map(sleep_here, [.01*t for t in range(100,0,-1)], ordered=False, chunksize=2)
tic = time.time()
for i,r in enumerate(amr):
    print "slept %.2fs on engine %i: %.3f" % (r[1], r[0], time.time()-tic)

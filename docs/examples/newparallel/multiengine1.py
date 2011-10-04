#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import time
import numpy

# import IPython.kernel.magic
from IPython.parallel import Client, Reference
from IPython.parallel import error

rc = Client()
mux = rc[:]

#-------------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------------

%load_ext parallelmagic

mux.block = True
mux.clear()
mux.activate()

n = len(rc)
assert n >= 4, "Not Enough Engines: %i, 4 needed for this script"%n

values = [
    10,
    1.0,
    range(100),
    ('asdf', 1000),
    {'a': 10, 'b': 20}
    ]

keys = ['a','b','c','d','e']

sequences = [
    range(100),
    numpy.arange(100)
]

#-------------------------------------------------------------------------------
# Blocking execution
#-------------------------------------------------------------------------------

# Execute

with mux.sync_imports():
    import math
    import numpy

mux.execute('a = 2.0*math.pi')
print mux['a']

for id in mux.targets:
    mux.execute('b=%d' % id, targets=id)


try:
    mux.execute('b = 10',targets=max(mux.targets)+1)
except IndexError:
    print "Caught invalid engine ID OK."

try:
    mux.apply(lambda : 1/0)
except error.CompositeError:
    print "Caught 1/0 correctly."



%px print a, b

try:
    %px 1/0
except error.CompositeError:
    print "Caught 1/0 correctly."


# %autopx

%px a = numpy.random.random((4,4))
%px a = a+a.transpose()
# %autopx

print mux.apply(numpy.linalg.eigvals, Reference('a'))



mux.targets = [0,2]
%px a = 5
mux.targets = [1,3]
%px a = 10
mux.targets = rc.ids
print mux['a']


# Push/Pull

mux.push(dict(a=10, b=30, c={'f':range(10)}))
mux.pull(('a', 'b'))

for id in mux.targets:
    mux.push(dict(a=id), targets=id)


for id in mux.targets:
    mux.pull('a', targets=id)

mux.pull('a')


mux['a'] = 100
mux['a']

# get_result/reset/keys

mux.get_result()
%result
mux.apply(lambda : globals().keys())
mux.clear()
mux.apply(lambda : globals().keys())

try:
    %result
except error.CompositeError:
    print "Caught IndexError ok."


%px a = 5
mux.get_result(-1)
mux.apply(lambda : globals().keys())

# Queue management methods

%px import time
ars = [mux.apply_async(time.sleep, 2.0) for x in range(5)]


mux.queue_status()
time.sleep(3.0)
mux.abort(ars, block=True)
mux.queue_status()
time.sleep(2.0)
mux.queue_status()

mux.wait(ars)

for ar in ars:
    try:
        ar.r
    except error.CompositeError:
        print "Caught QueueCleared OK."


# scatter/gather

mux.scatter('a', range(10))
mux.gather('a')
mux.scatter('b', numpy.arange(10))
mux.gather('b')

#-------------------------------------------------------------------------------
# Non-Blocking execution
#-------------------------------------------------------------------------------

mux.block = False

# execute

ar1 = mux.execute('a=5')
with mux.sync_imports():
    import sets

ar1.wait()

ar1 = mux.execute('1/0')
ar2 = mux.execute('c = sets.Set()')

mux.wait((ar1, ar2))
try:
    ar1.r
except error.CompositeError:
    print "Caught ZeroDivisionError OK."

ar = mux.execute("arint 'hi'")
ar.r

ar = mux.apply(lambda : 1/0)
try:
    ar.r
except error.CompositeError:
    print "Caught ZeroDivisionError OK."

# Make sure we can reraise it!
try:
    ar.r
except error.CompositeError:
    print "Caught ZeroDivisionError OK."

# push/pull

ar1 = mux.push(dict(a=10))
ar1.get()
ar2 = mux.pull('a')
ar2.r


# This is a command to make sure the end of the file is happy.

print "The tests are done!"


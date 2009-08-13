"""Simple script to instantiate a class for testing %run"""

import sys

# An external test will check that calls to f() work after %run
class foo: pass

def f():
    return foo()

# We also want to ensure that while objects remain available for immediate
# access, objects from *previous* runs of the same script get collected, to
# avoid accumulating massive amounts of old references.
class C(object):
    def __init__(self,name):
        self.name = name
        
    def __del__(self):
        print 'tclass.py: deleting object:',self.name

try:
    name = sys.argv[1]
except IndexError:
    pass
else:
    if name.startswith('C'):
        c = C(name)

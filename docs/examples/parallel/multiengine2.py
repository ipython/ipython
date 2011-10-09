#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import time

from IPython.parallel import Client

#-------------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------------

mux = Client()[:]

mux.clear()

mux.block=False

ar1 = mux.apply(time.sleep, 5)
ar2 = mux.push(dict(a=10,b=30,c=range(20000),d='The dog went swimming.'))
ar3 = mux.pull(('a','b','d'), block=False)

print "Try a non-blocking get_result"
ar4 = mux.get_result()

print "Now wait for all the results"
mux.wait([ar1,ar2,ar3,ar4])
print "The last pull got:", ar4.r

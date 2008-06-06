# Setup - all imports are done in tcommon
from IPython.testutils import tcommon
from IPython.testutils.tcommon import *

# Doctest code begins here
from IPython.tools import utils

for i in range(10):
    print i,
    print i+1

print 'simple loop is over'

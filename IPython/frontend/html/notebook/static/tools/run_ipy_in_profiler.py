#!/usr/bin/env python
"""XXX - What exactly is the use of this script?

I (fperez) tried it quickly and it doesn't work in its current form.  Either it
needs to be fixed and documented or removed.
"""

import cProfile as profile
import sys
#import profile

def main():
    import IPython.ipapi
    print "Entering ipython for profiling. Type 'Exit' for profiler report"
    IPython.ipapi.launch_new_instance()

if len(sys.argv) == 1:
    profile.run('main()', 'ipython_profiler_results')

import pstats
p = pstats.Stats(len(sys.argv) >1 and sys.argv[1] or 'ipython_profiler_results')
p.sort_stats('time').print_stats(30)


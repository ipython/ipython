#!/usr/bin/env python
"""Python wrapper around a submitted workflow job.

In reality this would be a more sophisticated script, here we only illustrate
the basic idea by considering that a submitted 'job' is a Python string to be
executed.
"""

import sys

argv = sys.argv

from IPython.zmq.parallel.engine import main

ns = {}

# job
exec sys.argv[1] in ns

# start engine with job namespace
main([], user_ns=ns)

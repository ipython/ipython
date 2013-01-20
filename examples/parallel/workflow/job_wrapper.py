#!/usr/bin/env python
"""Python wrapper around a submitted workflow job.

In reality this would be a more sophisticated script, here we only illustrate
the basic idea by considering that a submitted 'job' is a Python string to be
executed.
"""

import sys

argv = sys.argv

from IPython.parallel.engine import EngineFactory
from IPython.parallel.ipengineapp import launch_new_instance

ns = {}

# job
exec sys.argv[1] in ns

# this should really use Config:
EngineFactory.user_ns = ns

# start engine with job namespace
launch_new_instance()

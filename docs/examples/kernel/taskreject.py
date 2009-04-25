#!/usr/bin/env python
# encoding: utf-8

"""
A new example showing how to use `TaskRejectError` to handle dependencies
in the IPython task system.

To run this example, do::

    $ ipcluster local -n 4

Then, in another terminal start up IPython and do::

    In [0]: %run taskreject.py

    In [1]: mec.execute('run=True', targets=[0,1])

After the first command, the scheduler will keep rescheduling the tasks, as
they will fail with `TaskRejectError`.  But after the second command, there
are two engines that the tasks can run on.  The tasks are quickly funneled
to these engines.

If you want to see how the controller is scheduling and retrying the tasks
do a `tail -f` on the controller's log file in ~/.ipython/log.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from IPython.kernel import client
from IPython.kernel import TaskRejectError

mec = client.MultiEngineClient()
tc = client.TaskClient()

mec.execute('from IPython.kernel import TaskRejectError')
mec.execute('run = False')

def map_task():
    if not run:
        raise TaskRejectError('task dependency not met')
    return 3.0e8

task_ids = []

for i in range(10):
    task = client.MapTask(map_task, retries=20)
    task_ids.append(tc.run(task, block=False))


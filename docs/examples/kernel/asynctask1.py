#!/usr/bin/env python
# encoding: utf-8

# This example shows how the AsynTaskClient can be used
# This example is currently broken

from twisted.internet import reactor, defer
from IPython.kernel import asyncclient

mec = asyncclient.AsyncMultiEngineClient(('localhost', 10105))
tc = asyncclient.AsyncTaskClient(('localhost',10113))

cmd1 = """\
a = 5
b = 10*d
c = a*b*d
"""

t1 = asyncclient.Task(cmd1, clear_before=False, clear_after=True, pull=['a','b','c'])

d = mec.push(dict(d=30))

def raise_and_print(tr):
    tr.raiseException()
    print "a, b: ", tr.ns.a, tr.ns.b
    return tr

d.addCallback(lambda _: tc.run(t1))
d.addCallback(lambda tid: tc.get_task_result(tid,block=True))
d.addCallback(raise_and_print)
d.addCallback(lambda _: reactor.stop())
reactor.run()

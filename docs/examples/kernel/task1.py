from IPython.kernel import client

tc = client.TaskClient()
rc = client.MultiEngineClient()

rc.push(dict(d=30))

cmd1 = """\
a = 5
b = 10*d
c = a*b*d
"""

t1 = client.StringTask(cmd1, clear_before=False, clear_after=True, pull=['a','b','c'])
tid1 = tc.run(t1)
tr1 = tc.get_task_result(tid1,block=True)
tr1.raise_exception()
print "a, b: ", tr1.ns.a, tr1.ns.b
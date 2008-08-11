from IPython.kernel import client

tc = client.TaskClient()

result = tc.map(lambda x: 2*x, range(10))
print "Simple, default map: ", result

m = tc.mapper(block=False, clear_after=True, clear_before=True)
tids = m.map(lambda x: 2*x, range(10))
print "Submitted tasks, got ids: ", tids
tc.barrier(tids)
result = [tc.get_task_result(tid) for tid in tids]
print "Using a mapper: ", result

@tc.parallel()
def f(x): return 2*x

result = f(range(10))
print "Using a parallel function: ", result
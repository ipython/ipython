from IPython.parallel import Client

rc = Client()
v = rc.load_balanced_view()

result = v.map(lambda x: 2*x, range(10))
print "Simple, default map: ", list(result)

ar = v.map_async(lambda x: 2*x, range(10))
print "Submitted tasks, got ids: ", ar.msg_ids
result = ar.get()
print "Using a mapper: ", result

@v.parallel(block=True)
def f(x): return 2*x

result = f.map(range(10))
print "Using a parallel function: ", result
from IPython.parallel import Client

rc = Client()
view = rc[:]
result = view.map_sync(lambda x: 2*x, range(10))
print "Simple, default map: ", result

ar = view.map_async(lambda x: 2*x, range(10))
print "Submitted map, got AsyncResult: ", ar
result = ar.r
print "Using map_async: ", result

@view.parallel(block=True)
def f(x): return 2*x

result = f.map(range(10))
print "Using a parallel function: ", result
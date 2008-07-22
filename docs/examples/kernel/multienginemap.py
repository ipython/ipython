from IPython.kernel import client

mec = client.MultiEngineClient()

result = mec.map(lambda x: 2*x, range(10))
print "Simple, default map: ", result

m = mec.mapper(block=False)
pr = m.map(lambda x: 2*x, range(10))
print "Submitted map, got PendingResult: ", pr
result = pr.r
print "Using a mapper: ", result

@mec.parallel()
def f(x): return 2*x

result = f(range(10))
print "Using a parallel function: ", result
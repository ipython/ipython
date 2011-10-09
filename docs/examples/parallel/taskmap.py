# <nbformat>2</nbformat>

# <markdowncell>

# # Load balanced map and parallel function decorator

# <codecell>

from IPython.parallel import Client

# <codecell>

rc = Client()
v = rc.load_balanced_view()

# <codecell>

result = v.map(lambda x: 2*x, range(10))
print "Simple, default map: ", list(result)

# <codecell>

ar = v.map_async(lambda x: 2*x, range(10))
print "Submitted tasks, got ids: ", ar.msg_ids
result = ar.get()
print "Using a mapper: ", result

# <codecell>

@v.parallel(block=True)
def f(x): return 2*x

result = f.map(range(10))
print "Using a parallel function: ", result


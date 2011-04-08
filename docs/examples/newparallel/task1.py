from IPython.parallel import Client

rc = Client()
v = rc.load_balanced_view()

rc[:]['d'] = 30

def task(a):
    return a, 10*d, a*10*d

ar = v.apply(task, 5)

print "a, b, c: ", ar.get()
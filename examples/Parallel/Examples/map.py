from __future__ import print_function

from IPython.parallel import *

client = Client()
view = client.load_balanced_view()

@view.remote(block=True)
def square(a):
    """return square of a number"""
    return a*a

squares = map(square, range(42))

# but that blocked between each result; not exactly useful

square.block = False

arlist = map(square, range(42))
# submitted very fast

# wait for the results:
squares2 = [ r.get() for r in arlist ]

# now the more convenient @parallel decorator, which has a map method:
view2 = client[:]
@view2.parallel(block=False)
def psquare(a):
    """return square of a number"""
    return a*a

# this chunks the data into n-negines jobs, not 42 jobs:
ar = psquare.map(range(42))

# wait for the results to be done:
squares3 = ar.get()
print(squares == squares2, squares3==squares)
# True

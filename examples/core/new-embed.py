# This shows how to use the new top-level embed function.  It is a simpler
# API that manages the creation of the embedded shell.

from IPython import embed

a = 10
b = 20

embed(header='First time', banner1='')

c = 30
d = 40

try:
    raise Exception('adsfasdf')
except:
    embed(header='The second time')

from IPython.zmq.parallel.client import *

client = Client()

for id in client.ids:
    client.push(dict(ids=id*id), targets=id)

rns = client[0]
rns['a'] = 5

print rns['a']

remotes = client[:]

print remotes['ids']
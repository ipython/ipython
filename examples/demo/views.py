from IPython.zmq.parallel.client import *

client = Client('tcp://127.0.0.1:10101')

for id in client.ids:
    client.push(dict(ids=id*id), targets=id)

rns = client[0]
rns['a'] = 5

print rns['a']

remotes = client[:]

print remotes['ids']
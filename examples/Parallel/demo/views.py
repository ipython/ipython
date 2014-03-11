from IPython.parallel import *

client = Client()

for id in client.ids:
    client[id].push(dict(ids=id*id))

v = client[0]
v['a'] = 5

print(v['a'])

remotes = client[:]

print(remotes['ids'])

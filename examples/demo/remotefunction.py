from IPython.zmq.parallel.client import *

client = Client('tcp://127.0.0.1:10101')

@remote(client, bound=True)
def getkey(name):
    """fetch something from globals"""
    return globals().get(name)

@remote(client, bound=True, targets='all')
def setpids():
    import os
    globals()['pid'] = os.getpid()

# set pid in the globals
setpids()
getkey('pid')
getkey.targets=[1,2]
getkey('pid')
getkey.bound=False
getkey('pid') is None


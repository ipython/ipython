import time
from IPython.zmq.parallel.client import *

def wait(t):
    import time
    time.sleep(t)
    return t

client = Client('tcp://127.0.0.1:10101')
view = client[None]

tic = time.time()
for i in range(128):
    view.apply(wait, 1e-2*i)
    # limit to 1k msgs/s
    time.sleep(1e-2)

client.barrier()
toc = time.time()
print toc-tic

from IPython.zmq.parallel.client import *

client = Client('tcp://127.0.0.1:10101')

@remote(client, block=True)
def square(a):
    """return square of a number"""
    return a*a

squares = map(square, range(42))

# but that blocked between each result, not exactly useful
square.block=False
msg_ids = map(square, range(42))
# submitted very fast
# wait for them to be done:
client.barrier(msg_id)
squares2 = map(client.results.get, msg_ids)
print squares == squares2
# True
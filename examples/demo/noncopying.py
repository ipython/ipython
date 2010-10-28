"""non-copying sends"""
import zmq
import numpy

n = 10
iface = 'inproc://pub'

ctx = zmq.Context()

p = ctx.socket(zmq.PUB)
p.bind(iface)

# connect 2 subs
s1 = ctx.socket(zmq.SUB)
s1.connect(iface)
s1.setsockopt(zmq.SUBSCRIBE, '')

s2 = ctx.socket(zmq.SUB)
s2.connect(iface)
s2.setsockopt(zmq.SUBSCRIBE, '')

A = numpy.random.random((1024,1024))

# send
p.send(A, copy=False)
# recv on 1 non-copy
msg1 = s1.recv(copy=False)
B1 = numpy.frombuffer(msg1.buffer, dtype=A.dtype).reshape(A.shape)
# recv on 2 copy
msg2 = s2.recv(copy=False)
B2 = numpy.frombuffer(buffer(msg2.bytes), dtype=A.dtype).reshape(A.shape)

print (B1==B2).all()
print (B1==A).all()
A[0][0] += 10
print "~"
# after changing A in-place, B1 changes too, proving non-copying sends
print (B1==A).all()
# but B2 is fixed, since it called the msg.bytes attr, which copies
print (B1==B2).all()





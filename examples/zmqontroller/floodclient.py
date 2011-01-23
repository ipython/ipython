#!/usr/bin/env python
import time
import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream
from IPython.zmq import streamsession as session
Message = session.Message
# from IPython.zmq.messages import send_message_pickle as send_message
import uuid

thesession = session.StreamSession()

max_messages=10000
printstep=1000

counter = dict(count=0, engines=1)

def poit(msg):
    print "POIT"
    print msg

def count(msg):
    count = counter["count"] = counter["count"]+1
    if not count % printstep:
        print "#########################"
        print count, time.time()-counter['tic']

def unpack_and_print(msg):
    global msg_counter
    msg_counter += 1
    print msg
    try:
        msg = thesession.unpack_message(msg[-3:])
    except Exception, e:
        print e
        # pass
    print msg


ctx = zmq.Context()

loop = ioloop.IOLoop()
sock = ctx.socket(zmq.XREQ)
queue = ZMQStream(ctx.socket(zmq.XREQ), loop)
client = ZMQStream(sock, loop)
client.on_send(poit)
def check_engines(msg):
    # client.on_recv(unpack_and_print)
    queue.on_recv(count)
    idents = msg[:-3]
    msg = thesession.unpack_message(msg[-3:])
    msg = Message(msg)
    print msg
    queue.connect(str(msg.content.queue))
    engines = dict(msg.content.engines)
    # global tic
    N=max_messages
    if engines:
        tic = time.time()
        counter['tic']= tic
        for i in xrange(N/len(engines)):
          for eid,key in engines.iteritems():
            thesession.send(queue, "execute_request", dict(code='id=%i'%(int(eid)+i)),ident=str(key))
        toc = time.time()
        print "#####################################"
        print N, toc-tic
        print "#####################################"
    
    
    

client.on_recv(check_engines)

sock.connect('tcp://127.0.0.1:10102')
sock.setsockopt(zmq.IDENTITY, thesession.username)
# stream = ZMQStream()
# header = dict(msg_id = uuid.uuid4().bytes, msg_type='relay', id=0)
parent = dict(targets=2)
# content = "GARBAGE"
thesession.send(client, "connection_request")

# send_message(client, (header, content))
# print thesession.recv(client, 0)

loop.start()

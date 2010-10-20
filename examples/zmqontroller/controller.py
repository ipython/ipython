#!/usr/bin/env python
"""A script to launch a controller with all its queues and connect it to a logger"""

import time
import logging

import zmq
from zmq.devices import ProcessMonitoredQueue, ThreadMonitoredQueue
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream
from zmq.log import handlers

from IPython.zmq import log
from IPython.zmq.parallel import controller, heartmonitor, streamsession as session

  
  

def setup():
    """setup a basic controller and open client,registrar, and logging ports. Start the Queue and the heartbeat"""
    ctx = zmq.Context()
    loop = ioloop.IOLoop.instance()
    
    # port config
    # config={}
    execfile('config.py', globals())
    iface = config['interface']
    logport = config['logport']
    rport = config['regport']
    cport = config['clientport']
    cqport = config['cqueueport']
    eqport = config['equeueport']
    ctport = config['ctaskport']
    etport = config['etaskport']
    ccport = config['ccontrolport']
    ecport = config['econtrolport']
    hport = config['heartport']
    nport = config['notifierport']
    
    # setup logging
    lsock = ctx.socket(zmq.PUB)
    lsock.connect('%s:%i'%(iface,logport))
    # connected=False
    # while not connected:
    #     try:
    #     except:
    #         logport = logport + 1
    #     else:
    #         connected=True
    #         
    handler = handlers.PUBHandler(lsock)
    handler.setLevel(logging.DEBUG)
    handler.root_topic = "controller"
    log.logger.addHandler(handler)
    time.sleep(.5)
    
    ### Engine connections ###
    
    # Engine registrar socket
    reg = ZMQStream(ctx.socket(zmq.XREP), loop)
    reg.bind("%s:%i"%(iface, rport))
    
    # heartbeat
    hpub = ctx.socket(zmq.PUB)
    hpub.bind("%s:%i"%(iface, hport))
    hrep = ctx.socket(zmq.XREP)
    hrep.bind("%s:%i"%(iface, hport+1))
    
    hb = heartmonitor.HeartMonitor(loop, ZMQStream(hpub,loop), ZMQStream(hrep,loop),2500)
    hb.start()
    
    ### Client connections ###
    # Clientele socket
    c = ZMQStream(ctx.socket(zmq.XREP), loop)
    c.bind("%s:%i"%(iface, cport))
    
    n = ZMQStream(ctx.socket(zmq.PUB), loop)
    n.bind("%s:%i"%(iface, nport))
    
    thesession = session.StreamSession(username="controller")
    
    
    
    # build and launch the queue
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, "")
    monport = sub.bind_to_random_port(iface)
    sub = ZMQStream(sub, loop)
    
    # Multiplexer Queue (in a Process)
    q = ProcessMonitoredQueue(zmq.XREP, zmq.XREP, zmq.PUB, 'in', 'out')
    q.bind_in("%s:%i"%(iface, cqport))
    q.bind_out("%s:%i"%(iface, eqport))
    q.connect_mon("%s:%i"%(iface, monport))
    q.daemon=True
    q.start()
    
    # Control Queue (in a Process)
    q = ProcessMonitoredQueue(zmq.XREP, zmq.XREP, zmq.PUB, 'incontrol', 'outcontrol')
    q.bind_in("%s:%i"%(iface, ccport))
    q.bind_out("%s:%i"%(iface, ecport))
    q.connect_mon("%s:%i"%(iface, monport))
    q.daemon=True
    q.start()
    
    # Task Queue (in a Process)
    q = ProcessMonitoredQueue(zmq.XREP, zmq.XREQ, zmq.PUB, 'intask', 'outtask')
    q.bind_in("%s:%i"%(iface, ctport))
    q.bind_out("%s:%i"%(iface, etport))
    q.connect_mon("%s:%i"%(iface, monport))
    q.daemon=True
    q.start()
    
    time.sleep(.25)
    
    # build connection dicts
    engine_addrs = {
        'control' : "%s:%i"%(iface, ecport),
        'queue': "%s:%i"%(iface, eqport),
        'heartbeat': ("%s:%i"%(iface, hport), "%s:%i"%(iface, hport+1)),
        'task' : "%s:%i"%(iface, etport),
        'monitor' : "%s:%i"%(iface, monport),
        }
    
    client_addrs = {
        'control' : "%s:%i"%(iface, ccport),
        'query': "%s:%i"%(iface, cport),
        'queue': "%s:%i"%(iface, cqport),
        'task' : "%s:%i"%(iface, ctport),
        'notification': "%s:%i"%(iface, nport)
        }
    con = controller.Controller(loop, thesession, sub, reg, hb, c, n, None, engine_addrs, client_addrs)
    
    return loop
    

if __name__ == '__main__':
    loop = setup()
    loop.start()
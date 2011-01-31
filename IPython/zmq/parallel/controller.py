#!/usr/bin/env python
"""The IPython Controller with 0MQ
This is the master object that handles connections from engines and clients,
and monitors traffic through the various queues.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

import os
import time
from multiprocessing import Process

import zmq
from zmq.eventloop import  ioloop
from zmq.eventloop.zmqstream import ZMQStream
from zmq.devices import ProcessMonitoredQueue

# internal:
from IPython.zmq.entry_point import bind_port

from hub import Hub
from entry_point import (make_base_argument_parser, select_random_ports, split_ports,
                        connect_logger, parse_url, signal_children, generate_exec_key)


import streamsession as session
import heartmonitor
from scheduler import launch_scheduler

from dictdb import DictDB
try:
    import pymongo
except ImportError:
    MongoDB=None
else:
    from mongodb import MongoDB
    
#-------------------------------------------------------------------------
# Entry Point
#-------------------------------------------------------------------------

def make_argument_parser():
    """Make an argument parser"""
    parser = make_base_argument_parser()
    
    parser.add_argument('--client', type=int, metavar='PORT', default=0,
                        help='set the XREP port for clients [default: random]')
    parser.add_argument('--notice', type=int, metavar='PORT', default=0,
                        help='set the PUB socket for registration notification [default: random]')
    parser.add_argument('--hb', type=str, metavar='PORTS',
                        help='set the 2 ports for heartbeats [default: random]')
    parser.add_argument('--ping', type=int, default=3000,
                        help='set the heartbeat period in ms [default: 3000]')
    parser.add_argument('--monitor', type=int, metavar='PORT', default=0,
                        help='set the SUB port for queue monitoring [default: random]')
    parser.add_argument('--mux', type=str, metavar='PORTS',
                        help='set the XREP ports for the MUX queue [default: random]')
    parser.add_argument('--task', type=str, metavar='PORTS',
                        help='set the XREP/XREQ ports for the task queue [default: random]')
    parser.add_argument('--control', type=str, metavar='PORTS',
                        help='set the XREP ports for the control queue [default: random]')
    parser.add_argument('--scheduler', type=str, default='pure',
                        choices = ['pure', 'lru', 'plainrandom', 'weighted', 'twobin','leastload'],
                        help='select the task scheduler  [default: pure ZMQ]')
    parser.add_argument('--mongodb', action='store_true',
                        help='Use MongoDB task storage [default: in-memory]')
    
    return parser
    
def main(argv=None):
    
    parser = make_argument_parser()
    
    args = parser.parse_args(argv)
    parse_url(args)
    
    iface="%s://%s"%(args.transport,args.ip)+':%i'
    
    random_ports = 0
    if args.hb:
        hb = split_ports(args.hb, 2)
    else:
        hb = select_random_ports(2)
    if args.mux:
        mux = split_ports(args.mux, 2)
    else:
        mux = None
        random_ports += 2
    if args.task:
        task = split_ports(args.task, 2)
    else:
        task = None
        random_ports += 2
    if args.control:
        control = split_ports(args.control, 2)
    else:
        control = None
        random_ports += 2
    
    ctx = zmq.Context()
    loop = ioloop.IOLoop.instance()
    
    # setup logging
    connect_logger(ctx, iface%args.logport, root="controller", loglevel=args.loglevel)
    
    # Registrar socket
    reg = ZMQStream(ctx.socket(zmq.XREP), loop)
    regport = bind_port(reg, args.ip, args.regport)
    
    ### Engine connections ###
    
    # heartbeat
    hpub = ctx.socket(zmq.PUB)
    bind_port(hpub, args.ip, hb[0])
    hrep = ctx.socket(zmq.XREP)
    bind_port(hrep, args.ip, hb[1])
    
    hmon = heartmonitor.HeartMonitor(loop, ZMQStream(hpub,loop), ZMQStream(hrep,loop),args.ping)
    hmon.start()
    
    ### Client connections ###
    # Clientele socket
    c = ZMQStream(ctx.socket(zmq.XREP), loop)
    cport = bind_port(c, args.ip, args.client)
    # Notifier socket
    n = ZMQStream(ctx.socket(zmq.PUB), loop)
    nport = bind_port(n, args.ip, args.notice)
    
    ### Key File ###
    if args.execkey and not os.path.isfile(args.execkey):
            generate_exec_key(args.execkey)
    
    thesession = session.StreamSession(username=args.ident or "controller", keyfile=args.execkey)
    
    ### build and launch the queues ###
    
    # monitor socket
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.SUBSCRIBE, "")
    monport = bind_port(sub, args.ip, args.monitor)
    sub = ZMQStream(sub, loop)
    
    ports = select_random_ports(random_ports)
    children = []
    # Multiplexer Queue (in a Process)
    if not mux:
        mux = (ports.pop(),ports.pop())
    q = ProcessMonitoredQueue(zmq.XREP, zmq.XREP, zmq.PUB, 'in', 'out')
    q.bind_in(iface%mux[0])
    q.bind_out(iface%mux[1])
    q.connect_mon(iface%monport)
    q.daemon=True
    q.start()
    children.append(q.launcher)
    
    # Control Queue (in a Process)
    if not control:
        control = (ports.pop(),ports.pop())
    q = ProcessMonitoredQueue(zmq.XREP, zmq.XREP, zmq.PUB, 'incontrol', 'outcontrol')
    q.bind_in(iface%control[0])
    q.bind_out(iface%control[1])
    q.connect_mon(iface%monport)
    q.daemon=True
    q.start()
    children.append(q.launcher)
    # Task Queue (in a Process)
    if not task:
        task = (ports.pop(),ports.pop())
    if args.scheduler == 'pure':
        q = ProcessMonitoredQueue(zmq.XREP, zmq.XREQ, zmq.PUB, 'intask', 'outtask')
        q.bind_in(iface%task[0])
        q.bind_out(iface%task[1])
        q.connect_mon(iface%monport)
        q.daemon=True
        q.start()
        children.append(q.launcher)
    else:
        sargs = (iface%task[0],iface%task[1],iface%monport,iface%nport,args.scheduler)
        print (sargs)
        q = Process(target=launch_scheduler, args=sargs)
        q.daemon=True
        q.start()
        children.append(q)
    
    if args.mongodb:
        from mongodb import MongoDB
        db = MongoDB(thesession.session)
    else:
        db = DictDB()
    time.sleep(.25)
    
    # build connection dicts
    engine_addrs = {
        'control' : iface%control[1],
        'queue': iface%mux[1],
        'heartbeat': (iface%hb[0], iface%hb[1]),
        'task' : iface%task[1],
        'monitor' : iface%monport,
        }
    
    client_addrs = {
        'control' : iface%control[0],
        'query': iface%cport,
        'queue': iface%mux[0],
        'task' : iface%task[0],
        'notification': iface%nport
        }
    signal_children(children)
    hub = Hub(loop, thesession, sub, reg, hmon, c, n, db, engine_addrs, client_addrs)
    dc = ioloop.DelayedCallback(lambda : print("Controller started..."), 100, loop)
    dc.start()
    loop.start()
    
    
    

if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""The IPython Controller Hub with 0MQ
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

import sys
from datetime import datetime
import time
import logging

import zmq
from zmq.eventloop import ioloop, zmqstream

# internal:
from IPython.config.configurable import Configurable
from IPython.utils.traitlets import HasTraits, Instance, Int, Str, Dict
# from IPython.zmq.log import logger # a Logger object

from streamsession import Message, wrap_exception, ISO8601
from heartmonitor import HeartMonitor
from util import validate_url_container

try:
    from pymongo.binary import Binary
except ImportError:
    MongoDB=None
else:
    from mongodb import MongoDB
    
#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

logger = logging.getLogger()

def _passer(*args, **kwargs):
    return

def _printer(*args, **kwargs):
    print (args)
    print (kwargs)

def init_record(msg):
    """Initialize a TaskRecord based on a request."""
    header = msg['header']
    return {
        'msg_id' : header['msg_id'],
        'header' : header,
        'content': msg['content'],
        'buffers': msg['buffers'],
        'submitted': datetime.strptime(header['date'], ISO8601),
        'client_uuid' : None,
        'engine_uuid' : None,
        'started': None,
        'completed': None,
        'resubmitted': None,
        'result_header' : None,
        'result_content' : None,
        'result_buffers' : None,
        'queue' : None,
        'pyin' : None,
        'pyout': None,
        'pyerr': None,
        'stdout': '',
        'stderr': '',
    }


class EngineConnector(HasTraits):
    """A simple object for accessing the various zmq connections of an object.
    Attributes are:
    id (int): engine ID
    uuid (str): uuid (unused?)
    queue (str): identity of queue's XREQ socket
    registration (str): identity of registration XREQ socket
    heartbeat (str): identity of heartbeat XREQ socket
    """
    id=Int(0)
    queue=Str()
    control=Str()
    registration=Str()
    heartbeat=Str()
    pending=Instance(set)
    
    def __init__(self, **kwargs):
        super(EngineConnector, self).__init__(**kwargs)
        logger.info("engine::Engine Connected: %i"%self.id)
        
class Hub(Configurable):
    """The IPython Controller Hub with 0MQ connections
    
    Parameters
    ==========
    loop: zmq IOLoop instance
    session: StreamSession object
    <removed> context: zmq context for creating new connections (?)
    queue: ZMQStream for monitoring the command queue (SUB)
    registrar: ZMQStream for engine registration requests (XREP)
    heartbeat: HeartMonitor object checking the pulse of the engines
    clientele: ZMQStream for client connections (XREP)
                not used for jobs, only query/control commands
    notifier: ZMQStream for broadcasting engine registration changes (PUB)
    db: connection to db for out of memory logging of commands
                NotImplemented
    engine_addrs: dict of zmq connection information for engines to connect
                to the queues.
    client_addrs: dict of zmq connection information for engines to connect
                to the queues.
    """
    # internal data structures:
    ids=None # engine IDs
    keytable=None
    engines=None
    clients=None
    hearts=None
    pending=None
    tasks=None
    completed=None
    # mia=None
    incoming_registrations=None
    registration_timeout=None
    
    # objects from constructor:
    loop=Instance(ioloop.IOLoop)
    registrar=Instance(zmqstream.ZMQStream)
    clientele=Instance(zmqstream.ZMQStream)
    monitor=Instance(zmqstream.ZMQStream)
    heartmonitor=Instance(HeartMonitor)
    notifier=Instance(zmqstream.ZMQStream)
    db=Instance(object)
    client_addrs=Dict()
    engine_addrs=Dict()
    
    
    def __init__(self, **kwargs):
        """
        # universal:
        loop: IOLoop for creating future connections
        session: streamsession for sending serialized data
        # engine:
        queue: ZMQStream for monitoring queue messages
        registrar: ZMQStream for engine registration
        heartbeat: HeartMonitor object for tracking engines
        # client:
        clientele: ZMQStream for client connections
        # extra:
        db: ZMQStream for db connection (NotImplemented)
        engine_addrs: zmq address/protocol dict for engine connections
        client_addrs: zmq address/protocol dict for client connections
        """
        
        super(Hub, self).__init__(**kwargs)
        self.ids = set()
        self.keytable={}
        self.incoming_registrations={}
        self.engines = {}
        self.by_ident = {}
        self.clients = {}
        self.hearts = {}
        # self.mia = set()
        self.registration_timeout = max(5000, 2*self.heartmonitor.period)
        # this is the stuff that will move to DB:
        self.pending = set() # pending messages, keyed by msg_id
        self.queues = {} # pending msg_ids keyed by engine_id
        self.tasks = {} # pending msg_ids submitted as tasks, keyed by client_id
        self.completed = {} # completed msg_ids keyed by engine_id
        self.all_completed = set()
        self._idcounter = 0
        # self.sockets = {}
        # self.loop = loop
        # self.session = session
        # self.registrar = registrar
        # self.clientele = clientele
        # self.queue = queue
        # self.heartmonitor = heartbeat
        # self.notifier = notifier
        # self.db = db
        
        # validate connection dicts:
        # self.client_addrs = client_addrs
        validate_url_container(self.client_addrs)
        
        # assert isinstance(self.client_addrs['queue'], str)
        # assert isinstance(self.client_addrs['control'], str)
        # self.hb_addrs = hb_addrs
        validate_url_container(self.engine_addrs)
        # self.engine_addrs = engine_addrs
        # assert isinstance(self.engine_addrs['queue'], str)
        # assert isinstance(self.engine_addrs['control'], str)
        # assert len(engine_addrs['heartbeat']) == 2
        
        # register our callbacks
        self.registrar.on_recv(self.dispatch_register_request)
        self.clientele.on_recv(self.dispatch_client_msg)
        self.monitor.on_recv(self.dispatch_monitor_traffic)
        
        self.heartmonitor.add_heart_failure_handler(self.handle_heart_failure)
        self.heartmonitor.add_new_heart_handler(self.handle_new_heart)
        
        self.monitor_handlers = { 'in' : self.save_queue_request,
                                'out': self.save_queue_result,
                                'intask': self.save_task_request,
                                'outtask': self.save_task_result,
                                'tracktask': self.save_task_destination,
                                'incontrol': _passer,
                                'outcontrol': _passer,
                                'iopub': self.save_iopub_message,
        }
        
        self.client_handlers = {'queue_request': self.queue_status,
                                'result_request': self.get_results,
                                'purge_request': self.purge_results,
                                'load_request': self.check_load,
                                'resubmit_request': self.resubmit_task,
                                'shutdown_request': self.shutdown_request,
                                }
        
        self.registrar_handlers = {'registration_request' : self.register_engine,
                                'unregistration_request' : self.unregister_engine,
                                'connection_request': self.connection_request,
        }
        
        logger.info("controller::created controller")
    
    @property
    def _next_id(self):
        """gemerate a new ID"""
        newid = self._idcounter
        self._idcounter += 1
        return newid
        # newid = 0
        # incoming = [id[0] for id in self.incoming_registrations.itervalues()]
        # # print newid, self.ids, self.incoming_registrations
        # while newid in self.ids or newid in incoming:
        #     newid += 1
        # return newid
    
    #-----------------------------------------------------------------------------
    # message validation
    #-----------------------------------------------------------------------------
    
    def _validate_targets(self, targets):
        """turn any valid targets argument into a list of integer ids"""
        if targets is None:
            # default to all
            targets = self.ids
            
        if isinstance(targets, (int,str,unicode)):
            # only one target specified
            targets = [targets]
        _targets = []
        for t in targets:
            # map raw identities to ids
            if isinstance(t, (str,unicode)):
                t = self.by_ident.get(t, t)
            _targets.append(t)
        targets = _targets
        bad_targets = [ t for t in targets if t not in self.ids ]
        if bad_targets:
            raise IndexError("No Such Engine: %r"%bad_targets)
        if not targets:
            raise IndexError("No Engines Registered")
        return targets
    
    def _validate_client_msg(self, msg):
        """validates and unpacks headers of a message. Returns False if invalid,
        (ident, header, parent, content)"""
        client_id = msg[0]
        try:
            msg = self.session.unpack_message(msg[1:], content=True)
        except:
            logger.error("client::Invalid Message %s"%msg, exc_info=True)
            return False
        
        msg_type = msg.get('msg_type', None)
        if msg_type is None:
            return False
        header = msg.get('header')
        # session doesn't handle split content for now:
        return client_id, msg
        
    
    #-----------------------------------------------------------------------------
    # dispatch methods (1 per stream)
    #-----------------------------------------------------------------------------
    
    def dispatch_register_request(self, msg):
        """"""
        logger.debug("registration::dispatch_register_request(%s)"%msg)
        idents,msg = self.session.feed_identities(msg)
        if not idents:
            logger.error("Bad Queue Message: %s"%msg, exc_info=True)
            return
        try:
            msg = self.session.unpack_message(msg,content=True)
        except:
            logger.error("registration::got bad registration message: %s"%msg, exc_info=True)
            return
        
        msg_type = msg['msg_type']
        content = msg['content']
        
        handler = self.registrar_handlers.get(msg_type, None)
        if handler is None:
            logger.error("registration::got bad registration message: %s"%msg)
        else:
            handler(idents, msg)
    
    def dispatch_monitor_traffic(self, msg):
        """all ME and Task queue messages come through here, as well as
        IOPub traffic."""
        logger.debug("monitor traffic: %s"%msg[:2])
        switch = msg[0]
        idents, msg = self.session.feed_identities(msg[1:])
        if not idents:
            logger.error("Bad Monitor Message: %s"%msg)
            return
        handler = self.monitor_handlers.get(switch, None)
        if handler is not None:
            handler(idents, msg)
        else:
            logger.error("Invalid monitor topic: %s"%switch)
        
    
    def dispatch_client_msg(self, msg):
        """Route messages from clients"""
        idents, msg = self.session.feed_identities(msg)
        if not idents:
            logger.error("Bad Client Message: %s"%msg)
            return
        client_id = idents[0]
        try:
            msg = self.session.unpack_message(msg, content=True)
        except:
            content = wrap_exception()
            logger.error("Bad Client Message: %s"%msg, exc_info=True)
            self.session.send(self.clientele, "controller_error", ident=client_id, 
                    content=content)
            return
        
        # print client_id, header, parent, content
        #switch on message type:
        msg_type = msg['msg_type']
        logger.info("client:: client %s requested %s"%(client_id, msg_type))
        handler = self.client_handlers.get(msg_type, None)
        try:
            assert handler is not None, "Bad Message Type: %s"%msg_type
        except:
            content = wrap_exception()
            logger.error("Bad Message Type: %s"%msg_type, exc_info=True)
            self.session.send(self.clientele, "controller_error", ident=client_id, 
                    content=content)
            return
        else:
            handler(client_id, msg)
            
    def dispatch_db(self, msg):
        """"""
        raise NotImplementedError
    
    #---------------------------------------------------------------------------
    # handler methods (1 per event)
    #---------------------------------------------------------------------------
    
    #----------------------- Heartbeat --------------------------------------
    
    def handle_new_heart(self, heart):
        """handler to attach to heartbeater.
        Called when a new heart starts to beat.
        Triggers completion of registration."""
        logger.debug("heartbeat::handle_new_heart(%r)"%heart)
        if heart not in self.incoming_registrations:
            logger.info("heartbeat::ignoring new heart: %r"%heart)
        else:
            self.finish_registration(heart)
        
    
    def handle_heart_failure(self, heart):
        """handler to attach to heartbeater.
        called when a previously registered heart fails to respond to beat request.
        triggers unregistration"""
        logger.debug("heartbeat::handle_heart_failure(%r)"%heart)
        eid = self.hearts.get(heart, None)
        queue = self.engines[eid].queue
        if eid is None:
            logger.info("heartbeat::ignoring heart failure %r"%heart)
        else:
            self.unregister_engine(heart, dict(content=dict(id=eid, queue=queue)))
    
    #----------------------- MUX Queue Traffic ------------------------------
    
    def save_queue_request(self, idents, msg):
        if len(idents) < 2:
            logger.error("invalid identity prefix: %s"%idents)
            return
        queue_id, client_id = idents[:2]
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("queue::client %r sent invalid message to %r: %s"%(client_id, queue_id, msg), exc_info=True)
            return
        
        eid = self.by_ident.get(queue_id, None)
        if eid is None:
            logger.error("queue::target %r not registered"%queue_id)
            logger.debug("queue::    valid are: %s"%(self.by_ident.keys()))
            return
            
        header = msg['header']
        msg_id = header['msg_id']
        record = init_record(msg)
        record['engine_uuid'] = queue_id
        record['client_uuid'] = client_id
        record['queue'] = 'mux'
        if MongoDB is not None and isinstance(self.db, MongoDB):
            record['buffers'] = map(Binary, record['buffers'])
        self.pending.add(msg_id)
        self.queues[eid].append(msg_id)
        self.db.add_record(msg_id, record)
    
    def save_queue_result(self, idents, msg):
        if len(idents) < 2:
            logger.error("invalid identity prefix: %s"%idents)
            return
            
        client_id, queue_id = idents[:2]
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("queue::engine %r sent invalid message to %r: %s"%(
                    queue_id,client_id, msg), exc_info=True)
            return
        
        eid = self.by_ident.get(queue_id, None)
        if eid is None:
            logger.error("queue::unknown engine %r is sending a reply: "%queue_id)
            logger.debug("queue::       %s"%msg[2:])
            return
        
        parent = msg['parent_header']
        if not parent:
            return
        msg_id = parent['msg_id']
        if msg_id in self.pending:
            self.pending.remove(msg_id)
            self.all_completed.add(msg_id)
            self.queues[eid].remove(msg_id)
            self.completed[eid].append(msg_id)
            rheader = msg['header']
            completed = datetime.strptime(rheader['date'], ISO8601)
            started = rheader.get('started', None)
            if started is not None:
                started = datetime.strptime(started, ISO8601)
            result = {
                'result_header' : rheader,
                'result_content': msg['content'],
                'started' : started,
                'completed' : completed
            }
            if MongoDB is not None and isinstance(self.db, MongoDB):
                result['result_buffers'] = map(Binary, msg['buffers'])
            else:
                result['result_buffers'] = msg['buffers']
            self.db.update_record(msg_id, result)
        else:
            logger.debug("queue:: unknown msg finished %s"%msg_id)
            
    #--------------------- Task Queue Traffic ------------------------------
    
    def save_task_request(self, idents, msg):
        """Save the submission of a task."""
        client_id = idents[0]
        
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("task::client %r sent invalid task message: %s"%(
                    client_id, msg), exc_info=True)
            return
        record = init_record(msg)
        if MongoDB is not None and isinstance(self.db, MongoDB):
            record['buffers'] = map(Binary, record['buffers'])
        record['client_uuid'] = client_id
        record['queue'] = 'task'
        header = msg['header']
        msg_id = header['msg_id']
        self.pending.add(msg_id)
        self.db.add_record(msg_id, record)
    
    def save_task_result(self, idents, msg):
        """save the result of a completed task."""
        client_id = idents[0]
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("task::invalid task result message send to %r: %s"%(
                    client_id, msg), exc_info=True)
            raise
            return
        
        parent = msg['parent_header']
        if not parent:
            # print msg
            logger.warn("Task %r had no parent!"%msg)
            return
        msg_id = parent['msg_id']
        
        header = msg['header']
        engine_uuid = header.get('engine', None)
        eid = self.by_ident.get(engine_uuid, None)
        
        if msg_id in self.pending:
            self.pending.remove(msg_id)
            self.all_completed.add(msg_id)
            if eid is not None:
                self.completed[eid].append(msg_id)
                if msg_id in self.tasks[eid]:
                    self.tasks[eid].remove(msg_id)
            completed = datetime.strptime(header['date'], ISO8601)
            started = header.get('started', None)
            if started is not None:
                started = datetime.strptime(started, ISO8601)
            result = {
                'result_header' : header,
                'result_content': msg['content'],
                'started' : started,
                'completed' : completed,
                'engine_uuid': engine_uuid
            }
            if MongoDB is not None and isinstance(self.db, MongoDB):
                result['result_buffers'] = map(Binary, msg['buffers'])
            else:
                result['result_buffers'] = msg['buffers']
            self.db.update_record(msg_id, result)
            
        else:
            logger.debug("task::unknown task %s finished"%msg_id)
    
    def save_task_destination(self, idents, msg):
        try:
            msg = self.session.unpack_message(msg, content=True)
        except:
            logger.error("task::invalid task tracking message", exc_info=True)
            return
        content = msg['content']
        print (content)
        msg_id = content['msg_id']
        engine_uuid = content['engine_id']
        eid = self.by_ident[engine_uuid]
        
        logger.info("task::task %s arrived on %s"%(msg_id, eid))
        # if msg_id in self.mia:
        #     self.mia.remove(msg_id)
        # else:
        #     logger.debug("task::task %s not listed as MIA?!"%(msg_id))
        
        self.tasks[eid].append(msg_id)
        # self.pending[msg_id][1].update(received=datetime.now(),engine=(eid,engine_uuid))
        self.db.update_record(msg_id, dict(engine_uuid=engine_uuid))
    
    def mia_task_request(self, idents, msg):
        raise NotImplementedError
        client_id = idents[0]
        # content = dict(mia=self.mia,status='ok')
        # self.session.send('mia_reply', content=content, idents=client_id)
        
        
    #--------------------- IOPub Traffic ------------------------------
    
    def save_iopub_message(self, topics, msg):
        """save an iopub message into the db"""
        print (topics)
        try:
            msg = self.session.unpack_message(msg, content=True)
        except:
            logger.error("iopub::invalid IOPub message", exc_info=True)
            return
        
        parent = msg['parent_header']
        if not parent:
            logger.error("iopub::invalid IOPub message: %s"%msg)
            return
        msg_id = parent['msg_id']
        msg_type = msg['msg_type']
        content = msg['content']
        
        # ensure msg_id is in db
        try:
            rec = self.db.get_record(msg_id)
        except:
            logger.error("iopub::IOPub message has invalid parent", exc_info=True)
            return
        # stream
        d = {}
        if msg_type == 'stream':
            name = content['name']
            s = rec[name] or ''
            d[name] = s + content['data']
            
        elif msg_type == 'pyerr':
            d['pyerr'] = content
        else:
            d[msg_type] = content['data']
        
        self.db.update_record(msg_id, d)
        
    
            
    #-------------------------------------------------------------------------
    # Registration requests
    #-------------------------------------------------------------------------
        
    def connection_request(self, client_id, msg):
        """Reply with connection addresses for clients."""
        logger.info("client::client %s connected"%client_id)
        content = dict(status='ok')
        content.update(self.client_addrs)
        jsonable = {}
        for k,v in self.keytable.iteritems():
            jsonable[str(k)] = v
        content['engines'] = jsonable
        self.session.send(self.registrar, 'connection_reply', content, parent=msg, ident=client_id)
    
    def register_engine(self, reg, msg):
        """Register a new engine."""
        content = msg['content']
        try:
            queue = content['queue']
        except KeyError:
            logger.error("registration::queue not specified", exc_info=True)
            return
        heart = content.get('heartbeat', None)
        """register a new engine, and create the socket(s) necessary"""
        eid = self._next_id
        # print (eid, queue, reg, heart)
        
        logger.debug("registration::register_engine(%i, %r, %r, %r)"%(eid, queue, reg, heart))
        
        content = dict(id=eid,status='ok')
        content.update(self.engine_addrs)
        # check if requesting available IDs:
        if queue in self.by_ident:
            try:
                raise KeyError("queue_id %r in use"%queue)
            except:
                content = wrap_exception()
                logger.error("queue_id %r in use"%queue, exc_info=True)
        elif heart in self.hearts: # need to check unique hearts?
            try:
                raise KeyError("heart_id %r in use"%heart)
            except:
                logger.error("heart_id %r in use"%heart, exc_info=True)
                content = wrap_exception()
        else:
            for h, pack in self.incoming_registrations.iteritems():
                if heart == h:
                    try:
                        raise KeyError("heart_id %r in use"%heart)
                    except:
                        logger.error("heart_id %r in use"%heart, exc_info=True)
                        content = wrap_exception()
                    break
                elif queue == pack[1]:
                    try:
                        raise KeyError("queue_id %r in use"%queue)
                    except:
                        logger.error("queue_id %r in use"%queue, exc_info=True)
                        content = wrap_exception()
                    break
        
        msg = self.session.send(self.registrar, "registration_reply", 
                content=content, 
                ident=reg)
        
        if content['status'] == 'ok':
            if heart in self.heartmonitor.hearts:
                # already beating
                self.incoming_registrations[heart] = (eid,queue,reg[0],None)
                self.finish_registration(heart)
            else:
                purge = lambda : self._purge_stalled_registration(heart)
                dc = ioloop.DelayedCallback(purge, self.registration_timeout, self.loop)
                dc.start()
                self.incoming_registrations[heart] = (eid,queue,reg[0],dc)
        else:
            logger.error("registration::registration %i failed: %s"%(eid, content['evalue']))
        return eid
    
    def unregister_engine(self, ident, msg):
        """Unregister an engine that explicitly requested to leave."""
        try:
            eid = msg['content']['id']
        except:
            logger.error("registration::bad engine id for unregistration: %s"%ident, exc_info=True)
            return
        logger.info("registration::unregister_engine(%s)"%eid)
        content=dict(id=eid, queue=self.engines[eid].queue)
        self.ids.remove(eid)
        self.keytable.pop(eid)
        ec = self.engines.pop(eid)
        self.hearts.pop(ec.heartbeat)
        self.by_ident.pop(ec.queue)
        self.completed.pop(eid)
        for msg_id in self.queues.pop(eid):
            msg = self.pending.remove(msg_id)
            ############## TODO: HANDLE IT ################
        
        if self.notifier:
            self.session.send(self.notifier, "unregistration_notification", content=content)
    
    def finish_registration(self, heart):
        """Second half of engine registration, called after our HeartMonitor
        has received a beat from the Engine's Heart."""
        try: 
            (eid,queue,reg,purge) = self.incoming_registrations.pop(heart)
        except KeyError:
            logger.error("registration::tried to finish nonexistant registration", exc_info=True)
            return
        logger.info("registration::finished registering engine %i:%r"%(eid,queue))
        if purge is not None:
            purge.stop()
        control = queue
        self.ids.add(eid)
        self.keytable[eid] = queue
        self.engines[eid] = EngineConnector(id=eid, queue=queue, registration=reg, 
                                    control=control, heartbeat=heart)
        self.by_ident[queue] = eid
        self.queues[eid] = list()
        self.tasks[eid] = list()
        self.completed[eid] = list()
        self.hearts[heart] = eid
        content = dict(id=eid, queue=self.engines[eid].queue)
        if self.notifier:
            self.session.send(self.notifier, "registration_notification", content=content)
    
    def _purge_stalled_registration(self, heart):
        if heart in self.incoming_registrations:
            eid = self.incoming_registrations.pop(heart)[0]
            logger.info("registration::purging stalled registration: %i"%eid)
        else:
            pass
            
    #-------------------------------------------------------------------------
    # Client Requests
    #-------------------------------------------------------------------------
    
    def shutdown_request(self, client_id, msg):
        """handle shutdown request."""
        # s = self.context.socket(zmq.XREQ)
        # s.connect(self.client_connections['mux'])
        # time.sleep(0.1)
        # for eid,ec in self.engines.iteritems():
        #     self.session.send(s, 'shutdown_request', content=dict(restart=False), ident=ec.queue)
        # time.sleep(1)
        self.session.send(self.clientele, 'shutdown_reply', content={'status': 'ok'}, ident=client_id)
        dc = ioloop.DelayedCallback(lambda : self._shutdown(), 1000, self.loop)
        dc.start()
    
    def _shutdown(self):
        logger.info("controller::controller shutting down.")
        time.sleep(0.1)
        sys.exit(0)
        
    
    def check_load(self, client_id, msg):
        content = msg['content']
        try:
            targets = content['targets']
            targets = self._validate_targets(targets)
        except:
            content = wrap_exception()
            self.session.send(self.clientele, "controller_error", 
                    content=content, ident=client_id)
            return
        
        content = dict(status='ok')
        # loads = {}
        for t in targets:
            content[bytes(t)] = len(self.queues[t])+len(self.tasks[t])
        self.session.send(self.clientele, "load_reply", content=content, ident=client_id)
            
    
    def queue_status(self, client_id, msg):
        """Return the Queue status of one or more targets.
        if verbose: return the msg_ids
        else: return len of each type.
        keys: queue (pending MUX jobs)
            tasks (pending Task jobs)
            completed (finished jobs from both queues)"""
        content = msg['content']
        targets = content['targets']
        try:
            targets = self._validate_targets(targets)
        except:
            content = wrap_exception()
            self.session.send(self.clientele, "controller_error", 
                    content=content, ident=client_id)
            return
        verbose = content.get('verbose', False)
        content = dict(status='ok')
        for t in targets:
            queue = self.queues[t]
            completed = self.completed[t]
            tasks = self.tasks[t]
            if not verbose:
                queue = len(queue)
                completed = len(completed)
                tasks = len(tasks)
            content[bytes(t)] = {'queue': queue, 'completed': completed , 'tasks': tasks}
            # pending
        self.session.send(self.clientele, "queue_reply", content=content, ident=client_id)
    
    def purge_results(self, client_id, msg):
        """Purge results from memory. This method is more valuable before we move
        to a DB based message storage mechanism."""
        content = msg['content']
        msg_ids = content.get('msg_ids', [])
        reply = dict(status='ok')
        if msg_ids == 'all':
            self.db.drop_matching_records(dict(completed={'$ne':None}))
        else:
            for msg_id in msg_ids:
                if msg_id in self.all_completed:
                    self.db.drop_record(msg_id)
                else:
                    if msg_id in self.pending:
                        try:
                            raise IndexError("msg pending: %r"%msg_id)
                        except:
                            reply = wrap_exception()
                    else:
                        try:
                            raise IndexError("No such msg: %r"%msg_id)
                        except:
                            reply = wrap_exception()
                    break
            eids = content.get('engine_ids', [])
            for eid in eids:
                if eid not in self.engines:
                    try:
                        raise IndexError("No such engine: %i"%eid)
                    except:
                        reply = wrap_exception()
                    break
                msg_ids = self.completed.pop(eid)
                uid = self.engines[eid].queue
                self.db.drop_matching_records(dict(engine_uuid=uid, completed={'$ne':None}))
        
        self.session.send(self.clientele, 'purge_reply', content=reply, ident=client_id)
    
    def resubmit_task(self, client_id, msg, buffers):
        """Resubmit a task."""
        raise NotImplementedError
    
    def get_results(self, client_id, msg):
        """Get the result of 1 or more messages."""
        content = msg['content']
        msg_ids = sorted(set(content['msg_ids']))
        statusonly = content.get('status_only', False)
        pending = []
        completed = []
        content = dict(status='ok')
        content['pending'] = pending
        content['completed'] = completed
        buffers = []
        if not statusonly:
            content['results'] = {}
            records = self.db.find_records(dict(msg_id={'$in':msg_ids}))
        for msg_id in msg_ids:
            if msg_id in self.pending:
                pending.append(msg_id)
            elif msg_id in self.all_completed:
                completed.append(msg_id)
                if not statusonly:
                    rec = records[msg_id]
                    io_dict = {}
                    for key in 'pyin pyout pyerr stdout stderr'.split():
                            io_dict[key] = rec[key]
                    content[msg_id] = { 'result_content': rec['result_content'],
                                        'header': rec['header'],
                                        'result_header' : rec['result_header'],
                                        'io' : io_dict,
                                      }
                    buffers.extend(map(str, rec['result_buffers']))
            else:
                try:
                    raise KeyError('No such message: '+msg_id)
                except:
                    content = wrap_exception()
                break
        self.session.send(self.clientele, "result_reply", content=content, 
                                            parent=msg, ident=client_id,
                                            buffers=buffers)


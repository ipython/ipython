#!/usr/bin/env python
# encoding: utf-8

"""The IPython Controller with 0MQ
This is the master object that handles connections from engines, clients, and 
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from datetime import datetime

import zmq
from zmq.eventloop import zmqstream, ioloop
import uuid

# internal:
from streamsession import Message, wrap_exception # default_unpacker as unpack, default_packer as pack
from IPython.zmq.log import logger # a Logger object

# from messages import json # use the same import switches

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class ReverseDict(dict):
    """simple double-keyed subset of dict methods."""
    
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.reverse = dict()
        for key, value in self.iteritems():
            self.reverse[value] = key
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.reverse[key]
    
    def __setitem__(self, key, value):
        if key in self.reverse:
            raise KeyError("Can't have key %r on both sides!"%key)
        dict.__setitem__(self, key, value)
        self.reverse[value] = key
    
    def pop(self, key):
        value = dict.pop(self, key)
        self.d1.pop(value)
        return value
    

class EngineConnector(object):
    """A simple object for accessing the various zmq connections of an object.
    Attributes are:
    id (int): engine ID
    uuid (str): uuid (unused?)
    queue (str): identity of queue's XREQ socket
    registration (str): identity of registration XREQ socket
    heartbeat (str): identity of heartbeat XREQ socket
    """
    id=0
    queue=None
    control=None
    registration=None
    heartbeat=None
    pending=None
    
    def __init__(self, id, queue, registration, control, heartbeat=None):
        logger.info("engine::Engine Connected: %i"%id)
        self.id = id
        self.queue = queue
        self.registration = registration
        self.control = control
        self.heartbeat = heartbeat
        
class Controller(object):
    """The IPython Controller with 0MQ connections
    
    Parameters
    ==========
    loop: zmq IOLoop instance
    session: StreamSession object
    <removed> context: zmq context for creating new connections (?)
    registrar: ZMQStream for engine registration requests (XREP)
    clientele: ZMQStream for client connections (XREP)
                not used for jobs, only query/control commands
    queue: ZMQStream for monitoring the command queue (SUB)
    heartbeat: HeartMonitor object checking the pulse of the engines
    db_stream: connection to db for out of memory logging of commands
                NotImplemented
    queue_addr: zmq connection address of the XREP socket for the queue
    hb_addr: zmq connection address of the PUB socket for heartbeats
    task_addr: zmq connection address of the XREQ socket for task queue
    """
    # internal data structures:
    ids=None # engine IDs
    keytable=None
    engines=None
    clients=None
    hearts=None
    pending=None
    results=None
    tasks=None
    completed=None
    mia=None
    incoming_registrations=None
    registration_timeout=None
    
    #objects from constructor:
    loop=None
    registrar=None
    clientelle=None
    queue=None
    heartbeat=None
    notifier=None
    db=None
    client_addr=None
    engine_addrs=None
    
    
    def __init__(self, loop, session, queue, registrar, heartbeat, clientele, notifier, db, engine_addrs, client_addrs):
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
        self.ids = set()
        self.keytable={}
        self.incoming_registrations={}
        self.engines = {}
        self.by_ident = {}
        self.clients = {}
        self.hearts = {}
        self.mia = set()
        
        # self.sockets = {}
        self.loop = loop
        self.session = session
        self.registrar = registrar
        self.clientele = clientele
        self.queue = queue
        self.heartbeat = heartbeat
        self.notifier = notifier
        self.db = db
        
        self.client_addrs = client_addrs
        assert isinstance(client_addrs['queue'], str)
        # self.hb_addrs = hb_addrs
        self.engine_addrs = engine_addrs
        assert isinstance(engine_addrs['queue'], str)
        assert len(engine_addrs['heartbeat']) == 2
        
        
        # register our callbacks
        self.registrar.on_recv(self.dispatch_register_request)
        self.clientele.on_recv(self.dispatch_client_msg)
        self.queue.on_recv(self.dispatch_queue_traffic)
        
        if heartbeat is not None:
            heartbeat.add_heart_failure_handler(self.handle_heart_failure)
            heartbeat.add_new_heart_handler(self.handle_new_heart)
        
        if self.db is not None:
            self.db.on_recv(self.dispatch_db)
            
        self.client_handlers = {'queue_request': self.queue_status,
                                'result_request': self.get_results,
                                'purge_request': self.purge_results,
                                'resubmit_request': self.resubmit_task,
                                }
        
        self.registrar_handlers = {'registration_request' : self.register_engine,
                                'unregistration_request' : self.unregister_engine,
                                'connection_request': self.connection_request,
        
        }
        # 
        # this is the stuff that will move to DB:
        self.results = {} # completed results
        self.pending = {} # pending messages, keyed by msg_id
        self.queues = {} # pending msg_ids keyed by engine_id
        self.tasks = {} # pending msg_ids submitted as tasks, keyed by client_id
        self.completed = {} # completed msg_ids keyed by engine_id
        self.registration_timeout = max(5000, 2*self.heartbeat.period)
        
        logger.info("controller::created controller")
    
    def _new_id(self):
        """gemerate a new ID"""
        newid = 0
        incoming = [id[0] for id in self.incoming_registrations.itervalues()]
        # print newid, self.ids, self.incoming_registrations
        while newid in self.ids or newid in incoming:
            newid += 1
        return newid
    
    
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
            logger.error("client::Invalid Message %s"%msg)
            return False
        
        msg_type = msg.get('msg_type', None)
        if msg_type is None:
            return False
        header = msg.get('header')
        # session doesn't handle split content for now:
        return client_id, msg
        
    
    #-----------------------------------------------------------------------------
    # dispatch methods (1 per socket)
    #-----------------------------------------------------------------------------
    
    def dispatch_register_request(self, msg):
        """"""
        logger.debug("registration::dispatch_register_request(%s)"%msg)
        idents,msg = self.session.feed_identities(msg)
        print idents,msg, len(msg)
        try:
            msg = self.session.unpack_message(msg,content=True)
        except Exception, e:
            logger.error("registration::got bad registration message: %s"%msg)
            raise e
            return
        
        msg_type = msg['msg_type']
        content = msg['content']
        
        handler = self.registrar_handlers.get(msg_type, None)
        if handler is None:
            logger.error("registration::got bad registration message: %s"%msg)
        else:
            handler(idents, msg)
    
    def dispatch_queue_traffic(self, msg):
        """all ME and Task queue messages come through here"""
        logger.debug("queue traffic: %s"%msg[:2])
        switch = msg[0]
        idents, msg = self.session.feed_identities(msg[1:])
        if switch == 'in':
            self.save_queue_request(idents, msg)
        elif switch == 'out':
            self.save_queue_result(idents, msg)
        elif switch == 'intask':
            self.save_task_request(idents, msg)
        elif switch == 'outtask':
            self.save_task_result(idents, msg)
        elif switch == 'tracktask':
            self.save_task_destination(idents, msg)
        else:
            logger.error("Invalid message topic: %s"%switch)
        
    
    def dispatch_client_msg(self, msg):
        """Route messages from clients"""
        idents, msg = self.session.feed_identities(msg)
        client_id = idents[0]
        try:
            msg = self.session.unpack_message(msg, content=True)
        except:
            content = wrap_exception()
            logger.error("Bad Client Message: %s"%msg)
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
            logger.error("Bad Message Type: %s"%msg_type)
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
        if eid is None:
            logger.info("heartbeat::ignoring heart failure %r"%heart)
        else:
            self.unregister_engine(heart, dict(content=dict(id=eid)))
    
    #----------------------- MUX Queue Traffic ------------------------------
    
    def save_queue_request(self, idents, msg):
        queue_id, client_id = idents[:2]
            
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("queue::client %r sent invalid message to %r: %s"%(client_id, queue_id, msg))
            return
        
        eid = self.by_ident.get(queue_id, None)
        if eid is None:
            logger.error("queue::target %r not registered"%queue_id)
            logger.debug("queue::    valid are: %s"%(self.by_ident.keys()))
            return
            
        header = msg['header']
        msg_id = header['msg_id']
        info = dict(submit=datetime.now(),
                    received=None,
                    engine=(eid, queue_id))
        self.pending[msg_id] = ( msg, info )
        self.queues[eid][0].append(msg_id)
    
    def save_queue_result(self, idents, msg):
        client_id, queue_id = idents[:2]
        
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("queue::engine %r sent invalid message to %r: %s"%(
                    queue_id,client_id, msg))
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
        self.results[msg_id] = msg
        if msg_id in self.pending:
            self.pending.pop(msg_id)
            self.queues[eid][0].remove(msg_id)
            self.completed[eid].append(msg_id)
        else:
            logger.debug("queue:: unknown msg finished %s"%msg_id)
            
    #--------------------- Task Queue Traffic ------------------------------
    
    def save_task_request(self, idents, msg):
        client_id = idents[0]
        
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("task::client %r sent invalid task message: %s"%(
                    client_id, msg))
            return
        
        header = msg['header']
        msg_id = header['msg_id']
        self.mia.add(msg_id)
        self.pending[msg_id] = msg
        if not self.tasks.has_key(client_id):
            self.tasks[client_id] = []
        self.tasks[client_id].append(msg_id)
    
    def save_task_result(self, idents, msg):
        client_id = idents[0]
        try:
            msg = self.session.unpack_message(msg, content=False)
        except:
            logger.error("task::invalid task result message send to %r: %s"%(
                    client_id, msg))
            return
        
        parent = msg['parent_header']
        if not parent:
            # print msg
            # logger.warn("")
            return
        msg_id = parent['msg_id']
        self.results[msg_id] = msg
        if msg_id in self.pending:
            self.pending.pop(msg_id)
            if msg_id in self.mia:
                self.mia.remove(msg_id)
        else:
            logger.debug("task:: unknown task %s finished"%msg_id)
    
    def save_task_destination(self, idents, msg):
        try:
            msg = self.session.unpack_message(msg, content=True)
        except:
            logger.error("task::invalid task tracking message")
            return
        content = msg['content']
        print content
        msg_id = content['msg_id']
        engine_uuid = content['engine_id']
        for eid,queue_id in self.keytable.iteritems():
            if queue_id == engine_uuid:
                break
        
        logger.info("task:: task %s arrived on %s"%(msg_id, eid))
        if msg_id in self.mia:
            self.mia.remove(msg_id)
        else:
            logger.debug("task::task %s not listed as MIA?!"%(msg_id))
        self.tasks[engine_uuid].append(msg_id)
    
    def mia_task_request(self, idents, msg):
        client_id = idents[0]
        content = dict(mia=self.mia,status='ok')
        self.session.send('mia_reply', content=content, idents=client_id)
        
        
            
    #-------------------- Registration -----------------------------
        
    def connection_request(self, client_id, msg):
        """reply with connection addresses for clients"""
        logger.info("client::client %s connected"%client_id)
        content = dict(status='ok')
        content.update(self.client_addrs)
        jsonable = {}
        for k,v in self.keytable.iteritems():
            jsonable[str(k)] = v
        content['engines'] = jsonable
        self.session.send(self.registrar, 'connection_reply', content, parent=msg, ident=client_id)
    
    def register_engine(self, reg, msg):
        """register an engine"""
        content = msg['content']
        try:
            queue = content['queue']
        except KeyError:
            logger.error("registration::queue not specified")
            return
        heart = content.get('heartbeat', None)
        """register a new engine, and create the socket(s) necessary"""
        eid = self._new_id()
        # print (eid, queue, reg, heart)
        
        logger.debug("registration::register_engine(%i, %r, %r, %r)"%(eid, queue, reg, heart))
        
        content = dict(id=eid,status='ok')
        content.update(self.engine_addrs)
        # check if requesting available IDs:
        if queue in self.by_ident:
            content = {'status': 'error', 'reason': "queue_id %r in use"%queue}
        elif heart in self.hearts: # need to check unique hearts?
            content = {'status': 'error', 'reason': "heart_id %r in use"%heart}
        else:
            for h, pack in self.incoming_registrations.iteritems():
                if heart == h:
                    content = {'status': 'error', 'reason': "heart_id %r in use"%heart}
                    break
                elif queue == pack[1]:
                    content = {'status': 'error', 'reason': "queue_id %r in use"%queue}
                    break
        
        msg = self.session.send(self.registrar, "registration_reply", 
                content=content, 
                ident=reg)
        
        if content['status'] == 'ok':
            if heart in self.heartbeat.hearts:
                # already beating
                self.incoming_registrations[heart] = (eid,queue,reg,None)
                self.finish_registration(heart)
            else:
                purge = lambda : self._purge_stalled_registration(heart)
                dc = ioloop.DelayedCallback(purge, self.registration_timeout, self.loop)
                dc.start()
                self.incoming_registrations[heart] = (eid,queue,reg,dc)
        else:
            logger.error("registration::registration %i failed: %s"%(eid, content['reason']))
        return eid
    
    def unregister_engine(self, ident, msg):
        try:
            eid = msg['content']['id']
        except:
            logger.error("registration::bad engine id for unregistration: %s"%ident)
            return
        logger.info("registration::unregister_engine(%s)"%eid)
        content=dict(id=eid, queue=self.engines[eid].queue)
        self.ids.remove(eid)
        self.keytable.pop(eid)
        ec = self.engines.pop(eid)
        self.hearts.pop(ec.heartbeat)
        self.by_ident.pop(ec.queue)
        self.completed.pop(eid)
        for msg_id in self.queues.pop(eid)[0]:
            msg = self.pending.pop(msg_id)
            ############## TODO: HANDLE IT ################
        
        if self.notifier:
            self.session.send(self.notifier, "unregistration_notification", content=content)
    
    def finish_registration(self, heart):
        try: 
            (eid,queue,reg,purge) = self.incoming_registrations.pop(heart)
        except KeyError:
            logger.error("registration::tried to finish nonexistant registration")
            return
        logger.info("registration::finished registering engine %i:%r"%(eid,queue))
        if purge is not None:
            purge.stop()
        control = queue
        self.ids.add(eid)
        self.keytable[eid] = queue
        self.engines[eid] = EngineConnector(eid, queue, reg, control, heart)
        self.by_ident[queue] = eid
        self.queues[eid] = ([],[])
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
            
    #------------------- Client Requests -------------------------------
    
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
            content[str(t)] = len(self.queues[t])
        self.session.send(self.clientele, "load_reply", content=content, ident=client_id)
            
    
    def queue_status(self, client_id, msg):
        """handle queue_status request"""
        content = msg['content']
        targets = content['targets']
        try:
            targets = self._validate_targets(targets)
        except:
            content = wrap_exception()
            self.session.send(self.clientele, "controller_error", 
                    content=content, ident=client_id)
            return
        verbose = msg.get('verbose', False)
        content = dict()
        for t in targets:
            queue = self.queues[t]
            completed = self.completed[t]
            if not verbose:
                queue = len(queue)
                completed = len(completed)
            content[str(t)] = {'queue': queue, 'completed': completed }
            # pending
        self.session.send(self.clientele, "queue_reply", content=content, ident=client_id)
    
    def job_status(self, client_id, msg):
        """handle queue_status request"""
        content = msg['content']
        msg_ids = content['msg_ids']
        try:
            targets = self._validate_targets(targets)
        except:
            content = wrap_exception()
            self.session.send(self.clientele, "controller_error", 
                    content=content, ident=client_id)
            return
        verbose = msg.get('verbose', False)
        content = dict()
        for t in targets:
            queue = self.queues[t]
            completed = self.completed[t]
            if not verbose:
                queue = len(queue)
                completed = len(completed)
            content[str(t)] = {'queue': queue, 'completed': completed }
            # pending
        self.session.send(self.clientele, "queue_reply", content=content, ident=client_id)
    
    def purge_results(self, client_id, msg):
        content = msg['content']
        msg_ids = content.get('msg_ids', [])
        reply = dict(status='ok')
        if msg_ids == 'all':
            self.results = {}
        else:
            for msg_id in msg_ids:
                if msg_id in self.results:
                    self.results.pop(msg_id)
                else:
                    if msg_id in self.pending:
                        reply = dict(status='error', reason="msg pending: %r"%msg_id)
                    else:
                        reply = dict(status='error', reason="No such msg: %r"%msg_id)
                    break
            eids = content.get('engine_ids', [])
            for eid in eids:
                if eid not in self.engines:
                    reply = dict(status='error', reason="No such engine: %i"%eid)
                    break
                msg_ids = self.completed.pop(eid)
                for msg_id in msg_ids:
                    self.results.pop(msg_id)
        
        self.sesison.send(self.clientele, 'purge_reply', content=reply, ident=client_id)
    
    def resubmit_task(self, client_id, msg, buffers):
        content = msg['content']
        header = msg['header']
        
        
        msg_ids = content.get('msg_ids', [])
        reply = dict(status='ok')
        if msg_ids == 'all':
            self.results = {}
        else:
            for msg_id in msg_ids:
                if msg_id in self.results:
                    self.results.pop(msg_id)
                else:
                    if msg_id in self.pending:
                        reply = dict(status='error', reason="msg pending: %r"%msg_id)
                    else:
                        reply = dict(status='error', reason="No such msg: %r"%msg_id)
                    break
            eids = content.get('engine_ids', [])
            for eid in eids:
                if eid not in self.engines:
                    reply = dict(status='error', reason="No such engine: %i"%eid)
                    break
                msg_ids = self.completed.pop(eid)
                for msg_id in msg_ids:
                    self.results.pop(msg_id)
        
        self.sesison.send(self.clientele, 'purge_reply', content=reply, ident=client_id)
    
    def get_results(self, client_id, msg):
        """get the result of 1 or more messages"""
        content = msg['content']
        msg_ids = set(content['msg_ids'])
        statusonly = content.get('status_only', False)
        pending = []
        completed = []
        content = dict(status='ok')
        content['pending'] = pending
        content['completed'] = completed
        for msg_id in msg_ids:
            if msg_id in self.pending:
                pending.append(msg_id)
            elif msg_id in self.results:
                completed.append(msg_id)
                if not statusonly:
                    content[msg_id] = self.results[msg_id]['content']
            else:
                content = dict(status='error')
                content['reason'] = 'no such message: '+msg_id
                break
        self.session.send(self.clientele, "result_reply", content=content, 
                                            parent=msg, ident=client_id)
    


############ OLD METHODS for Python Relay Controller ###################
    def _validate_engine_msg(self, msg):
        """validates and unpacks headers of a message. Returns False if invalid,
        (ident, message)"""
        ident = msg[0]
        try:
            msg = self.session.unpack_message(msg[1:], content=False)
        except:
            logger.error("engine.%s::Invalid Message %s"%(ident, msg))
            return False
        
        try:
            eid = msg.header.username
            assert self.engines.has_key(eid)
        except:
            logger.error("engine::Invalid Engine ID %s"%(ident))
            return False
        
        return eid, msg
    

        
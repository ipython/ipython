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
from datetime import datetime
import logging

import zmq
from zmq.eventloop import zmqstream, ioloop
import uuid

# internal:
from IPython.zmq.log import logger # a Logger object
from IPython.zmq.entry_point import bind_port

from streamsession import Message, wrap_exception, ISO8601
from entry_point import (make_base_argument_parser, select_random_ports, split_ports,
                        connect_logger, parse_url, signal_children, generate_exec_key)
from dictdb import DictDB
try:
    from pymongo.binary import Binary
except ImportError:
    MongoDB=None
else:
    from mongodb import MongoDB
    
#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def _passer(*args, **kwargs):
    return

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
    

def init_record(msg):
    """return an empty TaskRecord dict, with all keys initialized with None."""
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
        'queue' : None
    }


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
        # self.mia = set()
        
        # self.sockets = {}
        self.loop = loop
        self.session = session
        self.registrar = registrar
        self.clientele = clientele
        self.queue = queue
        self.heartbeat = heartbeat
        self.notifier = notifier
        self.db = db
        
        # validate connection dicts:
        self.client_addrs = client_addrs
        assert isinstance(client_addrs['queue'], str)
        assert isinstance(client_addrs['control'], str)
        # self.hb_addrs = hb_addrs
        self.engine_addrs = engine_addrs
        assert isinstance(engine_addrs['queue'], str)
        assert isinstance(client_addrs['control'], str)
        assert len(engine_addrs['heartbeat']) == 2
        
        # register our callbacks
        self.registrar.on_recv(self.dispatch_register_request)
        self.clientele.on_recv(self.dispatch_client_msg)
        self.queue.on_recv(self.dispatch_queue_traffic)
        
        if heartbeat is not None:
            heartbeat.add_heart_failure_handler(self.handle_heart_failure)
            heartbeat.add_new_heart_handler(self.handle_new_heart)
        
        self.queue_handlers = { 'in' : self.save_queue_request,
                                'out': self.save_queue_result,
                                'intask': self.save_task_request,
                                'outtask': self.save_task_result,
                                'tracktask': self.save_task_destination,
                                'incontrol': _passer,
                                'outcontrol': _passer,
        }
        
        self.client_handlers = {'queue_request': self.queue_status,
                                'result_request': self.get_results,
                                'purge_request': self.purge_results,
                                'load_request': self.check_load,
                                'resubmit_request': self.resubmit_task,
                                }
        
        self.registrar_handlers = {'registration_request' : self.register_engine,
                                'unregistration_request' : self.unregister_engine,
                                'connection_request': self.connection_request,
        }
        self.registration_timeout = max(5000, 2*self.heartbeat.period)
        # this is the stuff that will move to DB:
        # self.results = {} # completed results
        self.pending = set() # pending messages, keyed by msg_id
        self.queues = {} # pending msg_ids keyed by engine_id
        self.tasks = {} # pending msg_ids submitted as tasks, keyed by client_id
        self.completed = {} # completed msg_ids keyed by engine_id
        self.all_completed = set()
        
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
    
    def dispatch_queue_traffic(self, msg):
        """all ME and Task queue messages come through here"""
        logger.debug("queue traffic: %s"%msg[:2])
        switch = msg[0]
        idents, msg = self.session.feed_identities(msg[1:])
        if not idents:
            logger.error("Bad Queue Message: %s"%msg)
            return
        handler = self.queue_handlers.get(switch, None)
        if handler is not None:
            handler(idents, msg)
        else:
            logger.error("Invalid message topic: %s"%switch)
        
    
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
            self.db.update_record(msg_id, result)
        else:
            logger.debug("queue:: unknown msg finished %s"%msg_id)
            
    #--------------------- Task Queue Traffic ------------------------------
    
    def save_task_request(self, idents, msg):
        """Save the submission of a task."""
        client_id = idents[0]
        
        try:
            msg = self.session.unpack_message(msg, content=False, copy=False)
        except:
            logger.error("task::client %r sent invalid task message: %s"%(
                    client_id, msg), exc_info=True)
            return
        rec = init_record(msg)
        if MongoDB is not None and isinstance(self.db, MongoDB):
            record['buffers'] = map(Binary, record['buffers'])
        rec['client_uuid'] = client_id
        rec['queue'] = 'task'
        header = msg['header']
        msg_id = header['msg_id']
        self.pending.add(msg_id)
        self.db.add_record(msg_id, rec)
    
    def save_task_result(self, idents, msg):
        """save the result of a completed task."""
        client_id = idents[0]
        try:
            msg = self.session.unpack_message(msg, content=False, copy=False)
        except:
            logger.error("task::invalid task result message send to %r: %s"%(
                    client_id, msg))
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
            self.db.update_record(msg_id, result)
            
        else:
            logger.debug("task::unknown task %s finished"%msg_id)
    
    def save_task_destination(self, idents, msg):
        try:
            msg = self.session.unpack_message(msg, content=True)
        except:
            logger.error("task::invalid task tracking message")
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
            try:
                raise KeyError("queue_id %r in use"%queue)
            except:
                content = wrap_exception()
        elif heart in self.hearts: # need to check unique hearts?
            try:
                raise KeyError("heart_id %r in use"%heart)
            except:
                content = wrap_exception()
        else:
            for h, pack in self.incoming_registrations.iteritems():
                if heart == h:
                    try:
                        raise KeyError("heart_id %r in use"%heart)
                    except:
                        content = wrap_exception()
                    break
                elif queue == pack[1]:
                    try:
                        raise KeyError("queue_id %r in use"%queue)
                    except:
                        content = wrap_exception()
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
            logger.error("registration::registration %i failed: %s"%(eid, content['evalue']))
        return eid
    
    def unregister_engine(self, ident, msg):
        """Unregister an engine that explicitly requested to leave."""
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
        msg_ids = set(content['msg_ids'])
        statusonly = content.get('status_only', False)
        pending = []
        completed = []
        content = dict(status='ok')
        content['pending'] = pending
        content['completed'] = completed
        if not statusonly:
            records = self.db.find_records(dict(msg_id={'$in':msg_ids}))
        for msg_id in msg_ids:
            if msg_id in self.pending:
                pending.append(msg_id)
            elif msg_id in self.all_completed:
                completed.append(msg_id)
                if not statusonly:
                    content[msg_id] = records[msg_id]['result_content']
            else:
                try:
                    raise KeyError('No such message: '+msg_id)
                except:
                    content = wrap_exception()
                break
        self.session.send(self.clientele, "result_reply", content=content, 
                                            parent=msg, ident=client_id)


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
    import time
    from multiprocessing import Process
    
    from zmq.eventloop.zmqstream import ZMQStream
    from zmq.devices import ProcessMonitoredQueue
    from zmq.log import handlers
    
    import streamsession as session
    import heartmonitor
    from scheduler import launch_scheduler
    
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
    con = Controller(loop, thesession, sub, reg, hmon, c, n, db, engine_addrs, client_addrs)
    dc = ioloop.DelayedCallback(lambda : print("Controller started..."), 100, loop)
    loop.start()
    
    
    

if __name__ == '__main__':
    main()

"""The IPython Controller Hub with 0MQ
This is the master object that handles connections from engines and clients,
and monitors traffic through the various queues.

Authors:

* Min RK
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

import sys
import time
from datetime import datetime

import zmq
from zmq.eventloop import ioloop
from zmq.eventloop.zmqstream import ZMQStream

# internal:
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import (
        HasTraits, Instance, Integer, Unicode, Dict, Set, Tuple, CBytes, DottedObjectName
        )

from IPython.parallel import error, util
from IPython.parallel.factory import RegistrationFactory

from IPython.zmq.session import SessionFactory

from .heartmonitor import HeartMonitor

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def _passer(*args, **kwargs):
    return

def _printer(*args, **kwargs):
    print (args)
    print (kwargs)

def empty_record():
    """Return an empty dict with all record keys."""
    return {
        'msg_id' : None,
        'header' : None,
        'content': None,
        'buffers': None,
        'submitted': None,
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

def init_record(msg):
    """Initialize a TaskRecord based on a request."""
    header = msg['header']
    return {
        'msg_id' : header['msg_id'],
        'header' : header,
        'content': msg['content'],
        'buffers': msg['buffers'],
        'submitted': header['date'],
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
    id=Integer(0)
    queue=CBytes()
    control=CBytes()
    registration=CBytes()
    heartbeat=CBytes()
    pending=Set()

class HubFactory(RegistrationFactory):
    """The Configurable for setting up a Hub."""

    # port-pairs for monitoredqueues:
    hb = Tuple(Integer,Integer,config=True,
        help="""XREQ/SUB Port pair for Engine heartbeats""")
    def _hb_default(self):
        return tuple(util.select_random_ports(2))

    mux = Tuple(Integer,Integer,config=True,
        help="""Engine/Client Port pair for MUX queue""")

    def _mux_default(self):
        return tuple(util.select_random_ports(2))

    task = Tuple(Integer,Integer,config=True,
        help="""Engine/Client Port pair for Task queue""")
    def _task_default(self):
        return tuple(util.select_random_ports(2))

    control = Tuple(Integer,Integer,config=True,
        help="""Engine/Client Port pair for Control queue""")

    def _control_default(self):
        return tuple(util.select_random_ports(2))

    iopub = Tuple(Integer,Integer,config=True,
        help="""Engine/Client Port pair for IOPub relay""")

    def _iopub_default(self):
        return tuple(util.select_random_ports(2))

    # single ports:
    mon_port = Integer(config=True,
        help="""Monitor (SUB) port for queue traffic""")

    def _mon_port_default(self):
        return util.select_random_ports(1)[0]

    notifier_port = Integer(config=True,
        help="""PUB port for sending engine status notifications""")

    def _notifier_port_default(self):
        return util.select_random_ports(1)[0]

    engine_ip = Unicode('127.0.0.1', config=True,
        help="IP on which to listen for engine connections. [default: loopback]")
    engine_transport = Unicode('tcp', config=True,
        help="0MQ transport for engine connections. [default: tcp]")

    client_ip = Unicode('127.0.0.1', config=True,
        help="IP on which to listen for client connections. [default: loopback]")
    client_transport = Unicode('tcp', config=True,
        help="0MQ transport for client connections. [default : tcp]")

    monitor_ip = Unicode('127.0.0.1', config=True,
        help="IP on which to listen for monitor messages. [default: loopback]")
    monitor_transport = Unicode('tcp', config=True,
        help="0MQ transport for monitor messages. [default : tcp]")

    monitor_url = Unicode('')

    db_class = DottedObjectName('IPython.parallel.controller.dictdb.DictDB',
        config=True, help="""The class to use for the DB backend""")

    # not configurable
    db = Instance('IPython.parallel.controller.dictdb.BaseDB')
    heartmonitor = Instance('IPython.parallel.controller.heartmonitor.HeartMonitor')

    def _ip_changed(self, name, old, new):
        self.engine_ip = new
        self.client_ip = new
        self.monitor_ip = new
        self._update_monitor_url()

    def _update_monitor_url(self):
        self.monitor_url = "%s://%s:%i" % (self.monitor_transport, self.monitor_ip, self.mon_port)

    def _transport_changed(self, name, old, new):
        self.engine_transport = new
        self.client_transport = new
        self.monitor_transport = new
        self._update_monitor_url()

    def __init__(self, **kwargs):
        super(HubFactory, self).__init__(**kwargs)
        self._update_monitor_url()


    def construct(self):
        self.init_hub()

    def start(self):
        self.heartmonitor.start()
        self.log.info("Heartmonitor started")

    def init_hub(self):
        """construct"""
        client_iface = "%s://%s:" % (self.client_transport, self.client_ip) + "%i"
        engine_iface = "%s://%s:" % (self.engine_transport, self.engine_ip) + "%i"

        ctx = self.context
        loop = self.loop

        # Registrar socket
        q = ZMQStream(ctx.socket(zmq.ROUTER), loop)
        q.bind(client_iface % self.regport)
        self.log.info("Hub listening on %s for registration.", client_iface % self.regport)
        if self.client_ip != self.engine_ip:
            q.bind(engine_iface % self.regport)
            self.log.info("Hub listening on %s for registration.", engine_iface % self.regport)

        ### Engine connections ###

        # heartbeat
        hpub = ctx.socket(zmq.PUB)
        hpub.bind(engine_iface % self.hb[0])
        hrep = ctx.socket(zmq.ROUTER)
        hrep.bind(engine_iface % self.hb[1])
        self.heartmonitor = HeartMonitor(loop=loop, config=self.config, log=self.log,
                                pingstream=ZMQStream(hpub,loop),
                                pongstream=ZMQStream(hrep,loop)
                            )

        ### Client connections ###
        # Notifier socket
        n = ZMQStream(ctx.socket(zmq.PUB), loop)
        n.bind(client_iface%self.notifier_port)

        ### build and launch the queues ###

        # monitor socket
        sub = ctx.socket(zmq.SUB)
        sub.setsockopt(zmq.SUBSCRIBE, b"")
        sub.bind(self.monitor_url)
        sub.bind('inproc://monitor')
        sub = ZMQStream(sub, loop)

        # connect the db
        self.log.info('Hub using DB backend: %r'%(self.db_class.split()[-1]))
        # cdir = self.config.Global.cluster_dir
        self.db = import_item(str(self.db_class))(session=self.session.session,
                                            config=self.config, log=self.log)
        time.sleep(.25)
        try:
            scheme = self.config.TaskScheduler.scheme_name
        except AttributeError:
            from .scheduler import TaskScheduler
            scheme = TaskScheduler.scheme_name.get_default_value()
        # build connection dicts
        self.engine_info = {
            'control' : engine_iface%self.control[1],
            'mux': engine_iface%self.mux[1],
            'heartbeat': (engine_iface%self.hb[0], engine_iface%self.hb[1]),
            'task' : engine_iface%self.task[1],
            'iopub' : engine_iface%self.iopub[1],
            # 'monitor' : engine_iface%self.mon_port,
            }

        self.client_info = {
            'control' : client_iface%self.control[0],
            'mux': client_iface%self.mux[0],
            'task' : (scheme, client_iface%self.task[0]),
            'iopub' : client_iface%self.iopub[0],
            'notification': client_iface%self.notifier_port
            }
        self.log.debug("Hub engine addrs: %s", self.engine_info)
        self.log.debug("Hub client addrs: %s", self.client_info)

        # resubmit stream
        r = ZMQStream(ctx.socket(zmq.DEALER), loop)
        url = util.disambiguate_url(self.client_info['task'][-1])
        r.setsockopt(zmq.IDENTITY, self.session.bsession)
        r.connect(url)

        self.hub = Hub(loop=loop, session=self.session, monitor=sub, heartmonitor=self.heartmonitor,
                query=q, notifier=n, resubmit=r, db=self.db,
                engine_info=self.engine_info, client_info=self.client_info,
                log=self.log)


class Hub(SessionFactory):
    """The IPython Controller Hub with 0MQ connections

    Parameters
    ==========
    loop: zmq IOLoop instance
    session: Session object
    <removed> context: zmq context for creating new connections (?)
    queue: ZMQStream for monitoring the command queue (SUB)
    query: ZMQStream for engine registration and client queries requests (XREP)
    heartbeat: HeartMonitor object checking the pulse of the engines
    notifier: ZMQStream for broadcasting engine registration changes (PUB)
    db: connection to db for out of memory logging of commands
                NotImplemented
    engine_info: dict of zmq connection information for engines to connect
                to the queues.
    client_info: dict of zmq connection information for engines to connect
                to the queues.
    """
    # internal data structures:
    ids=Set() # engine IDs
    keytable=Dict()
    by_ident=Dict()
    engines=Dict()
    clients=Dict()
    hearts=Dict()
    pending=Set()
    queues=Dict()  # pending msg_ids keyed by engine_id
    tasks=Dict() # pending msg_ids submitted as tasks, keyed by client_id
    completed=Dict() # completed msg_ids keyed by engine_id
    all_completed=Set() # completed msg_ids keyed by engine_id
    dead_engines=Set() # completed msg_ids keyed by engine_id
    unassigned=Set() # set of task msg_ds not yet assigned a destination
    incoming_registrations=Dict()
    registration_timeout=Integer()
    _idcounter=Integer(0)

    # objects from constructor:
    query=Instance(ZMQStream)
    monitor=Instance(ZMQStream)
    notifier=Instance(ZMQStream)
    resubmit=Instance(ZMQStream)
    heartmonitor=Instance(HeartMonitor)
    db=Instance(object)
    client_info=Dict()
    engine_info=Dict()


    def __init__(self, **kwargs):
        """
        # universal:
        loop: IOLoop for creating future connections
        session: streamsession for sending serialized data
        # engine:
        queue: ZMQStream for monitoring queue messages
        query: ZMQStream for engine+client registration and client requests
        heartbeat: HeartMonitor object for tracking engines
        # extra:
        db: ZMQStream for db connection (NotImplemented)
        engine_info: zmq address/protocol dict for engine connections
        client_info: zmq address/protocol dict for client connections
        """

        super(Hub, self).__init__(**kwargs)
        self.registration_timeout = max(5000, 2*self.heartmonitor.period)

        # validate connection dicts:
        for k,v in self.client_info.iteritems():
            if k == 'task':
                util.validate_url_container(v[1])
            else:
                util.validate_url_container(v)
        # util.validate_url_container(self.client_info)
        util.validate_url_container(self.engine_info)

        # register our callbacks
        self.query.on_recv(self.dispatch_query)
        self.monitor.on_recv(self.dispatch_monitor_traffic)

        self.heartmonitor.add_heart_failure_handler(self.handle_heart_failure)
        self.heartmonitor.add_new_heart_handler(self.handle_new_heart)

        self.monitor_handlers = {b'in' : self.save_queue_request,
                                b'out': self.save_queue_result,
                                b'intask': self.save_task_request,
                                b'outtask': self.save_task_result,
                                b'tracktask': self.save_task_destination,
                                b'incontrol': _passer,
                                b'outcontrol': _passer,
                                b'iopub': self.save_iopub_message,
        }

        self.query_handlers = {'queue_request': self.queue_status,
                                'result_request': self.get_results,
                                'history_request': self.get_history,
                                'db_request': self.db_query,
                                'purge_request': self.purge_results,
                                'load_request': self.check_load,
                                'resubmit_request': self.resubmit_task,
                                'shutdown_request': self.shutdown_request,
                                'registration_request' : self.register_engine,
                                'unregistration_request' : self.unregister_engine,
                                'connection_request': self.connection_request,
        }

        # ignore resubmit replies
        self.resubmit.on_recv(lambda msg: None, copy=False)

        self.log.info("hub::created hub")

    @property
    def _next_id(self):
        """gemerate a new ID.

        No longer reuse old ids, just count from 0."""
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
            raise IndexError("No Such Engine: %r" % bad_targets)
        if not targets:
            raise IndexError("No Engines Registered")
        return targets

    #-----------------------------------------------------------------------------
    # dispatch methods (1 per stream)
    #-----------------------------------------------------------------------------


    def dispatch_monitor_traffic(self, msg):
        """all ME and Task queue messages come through here, as well as
        IOPub traffic."""
        self.log.debug("monitor traffic: %r", msg[:2])
        switch = msg[0]
        try:
            idents, msg = self.session.feed_identities(msg[1:])
        except ValueError:
            idents=[]
        if not idents:
            self.log.error("Bad Monitor Message: %r", msg)
            return
        handler = self.monitor_handlers.get(switch, None)
        if handler is not None:
            handler(idents, msg)
        else:
            self.log.error("Invalid monitor topic: %r", switch)


    def dispatch_query(self, msg):
        """Route registration requests and queries from clients."""
        try:
            idents, msg = self.session.feed_identities(msg)
        except ValueError:
            idents = []
        if not idents:
            self.log.error("Bad Query Message: %r", msg)
            return
        client_id = idents[0]
        try:
            msg = self.session.unserialize(msg, content=True)
        except Exception:
            content = error.wrap_exception()
            self.log.error("Bad Query Message: %r", msg, exc_info=True)
            self.session.send(self.query, "hub_error", ident=client_id,
                    content=content)
            return
        # print client_id, header, parent, content
        #switch on message type:
        msg_type = msg['header']['msg_type']
        self.log.info("client::client %r requested %r", client_id, msg_type)
        handler = self.query_handlers.get(msg_type, None)
        try:
            assert handler is not None, "Bad Message Type: %r" % msg_type
        except:
            content = error.wrap_exception()
            self.log.error("Bad Message Type: %r", msg_type, exc_info=True)
            self.session.send(self.query, "hub_error", ident=client_id,
                    content=content)
            return

        else:
            handler(idents, msg)

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
        self.log.debug("heartbeat::handle_new_heart(%r)", heart)
        if heart not in self.incoming_registrations:
            self.log.info("heartbeat::ignoring new heart: %r", heart)
        else:
            self.finish_registration(heart)


    def handle_heart_failure(self, heart):
        """handler to attach to heartbeater.
        called when a previously registered heart fails to respond to beat request.
        triggers unregistration"""
        self.log.debug("heartbeat::handle_heart_failure(%r)", heart)
        eid = self.hearts.get(heart, None)
        queue = self.engines[eid].queue
        if eid is None or self.keytable[eid] in self.dead_engines:
            self.log.info("heartbeat::ignoring heart failure %r (not an engine or already dead)", heart)
        else:
            self.unregister_engine(heart, dict(content=dict(id=eid, queue=queue)))

    #----------------------- MUX Queue Traffic ------------------------------

    def save_queue_request(self, idents, msg):
        if len(idents) < 2:
            self.log.error("invalid identity prefix: %r", idents)
            return
        queue_id, client_id = idents[:2]
        try:
            msg = self.session.unserialize(msg)
        except Exception:
            self.log.error("queue::client %r sent invalid message to %r: %r", client_id, queue_id, msg, exc_info=True)
            return

        eid = self.by_ident.get(queue_id, None)
        if eid is None:
            self.log.error("queue::target %r not registered", queue_id)
            self.log.debug("queue::    valid are: %r", self.by_ident.keys())
            return
        record = init_record(msg)
        msg_id = record['msg_id']
        self.log.info("queue::client %r submitted request %r to %s", client_id, msg_id, eid)
        # Unicode in records
        record['engine_uuid'] = queue_id.decode('ascii')
        record['client_uuid'] = client_id.decode('ascii')
        record['queue'] = 'mux'

        try:
            # it's posible iopub arrived first:
            existing = self.db.get_record(msg_id)
            for key,evalue in existing.iteritems():
                rvalue = record.get(key, None)
                if evalue and rvalue and evalue != rvalue:
                    self.log.warn("conflicting initial state for record: %r:%r <%r> %r", msg_id, rvalue, key, evalue)
                elif evalue and not rvalue:
                    record[key] = evalue
            try:
                self.db.update_record(msg_id, record)
            except Exception:
                self.log.error("DB Error updating record %r", msg_id, exc_info=True)
        except KeyError:
            try:
                self.db.add_record(msg_id, record)
            except Exception:
                self.log.error("DB Error adding record %r", msg_id, exc_info=True)


        self.pending.add(msg_id)
        self.queues[eid].append(msg_id)

    def save_queue_result(self, idents, msg):
        if len(idents) < 2:
            self.log.error("invalid identity prefix: %r", idents)
            return

        client_id, queue_id = idents[:2]
        try:
            msg = self.session.unserialize(msg)
        except Exception:
            self.log.error("queue::engine %r sent invalid message to %r: %r",
                    queue_id, client_id, msg, exc_info=True)
            return

        eid = self.by_ident.get(queue_id, None)
        if eid is None:
            self.log.error("queue::unknown engine %r is sending a reply: ", queue_id)
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
            self.log.info("queue::request %r completed on %s", msg_id, eid)
        elif msg_id not in self.all_completed:
            # it could be a result from a dead engine that died before delivering the
            # result
            self.log.warn("queue:: unknown msg finished %r", msg_id)
            return
        # update record anyway, because the unregistration could have been premature
        rheader = msg['header']
        completed = rheader['date']
        started = rheader.get('started', None)
        result = {
            'result_header' : rheader,
            'result_content': msg['content'],
            'started' : started,
            'completed' : completed
        }

        result['result_buffers'] = msg['buffers']
        try:
            self.db.update_record(msg_id, result)
        except Exception:
            self.log.error("DB Error updating record %r", msg_id, exc_info=True)


    #--------------------- Task Queue Traffic ------------------------------

    def save_task_request(self, idents, msg):
        """Save the submission of a task."""
        client_id = idents[0]

        try:
            msg = self.session.unserialize(msg)
        except Exception:
            self.log.error("task::client %r sent invalid task message: %r",
                    client_id, msg, exc_info=True)
            return
        record = init_record(msg)

        record['client_uuid'] = client_id.decode('ascii')
        record['queue'] = 'task'
        header = msg['header']
        msg_id = header['msg_id']
        self.pending.add(msg_id)
        self.unassigned.add(msg_id)
        try:
            # it's posible iopub arrived first:
            existing = self.db.get_record(msg_id)
            if existing['resubmitted']:
                for key in ('submitted', 'client_uuid', 'buffers'):
                    # don't clobber these keys on resubmit
                    # submitted and client_uuid should be different
                    # and buffers might be big, and shouldn't have changed
                    record.pop(key)
                    # still check content,header which should not change
                    # but are not expensive to compare as buffers

            for key,evalue in existing.iteritems():
                if key.endswith('buffers'):
                    # don't compare buffers
                    continue
                rvalue = record.get(key, None)
                if evalue and rvalue and evalue != rvalue:
                    self.log.warn("conflicting initial state for record: %r:%r <%r> %r", msg_id, rvalue, key, evalue)
                elif evalue and not rvalue:
                    record[key] = evalue
            try:
                self.db.update_record(msg_id, record)
            except Exception:
                self.log.error("DB Error updating record %r", msg_id, exc_info=True)
        except KeyError:
            try:
                self.db.add_record(msg_id, record)
            except Exception:
                self.log.error("DB Error adding record %r", msg_id, exc_info=True)
        except Exception:
            self.log.error("DB Error saving task request %r", msg_id, exc_info=True)

    def save_task_result(self, idents, msg):
        """save the result of a completed task."""
        client_id = idents[0]
        try:
            msg = self.session.unserialize(msg)
        except Exception:
            self.log.error("task::invalid task result message send to %r: %r",
                    client_id, msg, exc_info=True)
            return

        parent = msg['parent_header']
        if not parent:
            # print msg
            self.log.warn("Task %r had no parent!", msg)
            return
        msg_id = parent['msg_id']
        if msg_id in self.unassigned:
            self.unassigned.remove(msg_id)

        header = msg['header']
        engine_uuid = header.get('engine', None)
        eid = self.by_ident.get(engine_uuid, None)

        if msg_id in self.pending:
            self.log.info("task::task %r finished on %s", msg_id, eid)
            self.pending.remove(msg_id)
            self.all_completed.add(msg_id)
            if eid is not None:
                self.completed[eid].append(msg_id)
                if msg_id in self.tasks[eid]:
                    self.tasks[eid].remove(msg_id)
            completed = header['date']
            started = header.get('started', None)
            result = {
                'result_header' : header,
                'result_content': msg['content'],
                'started' : started,
                'completed' : completed,
                'engine_uuid': engine_uuid
            }

            result['result_buffers'] = msg['buffers']
            try:
                self.db.update_record(msg_id, result)
            except Exception:
                self.log.error("DB Error saving task request %r", msg_id, exc_info=True)

        else:
            self.log.debug("task::unknown task %r finished", msg_id)

    def save_task_destination(self, idents, msg):
        try:
            msg = self.session.unserialize(msg, content=True)
        except Exception:
            self.log.error("task::invalid task tracking message", exc_info=True)
            return
        content = msg['content']
        # print (content)
        msg_id = content['msg_id']
        engine_uuid = content['engine_id']
        eid = self.by_ident[util.asbytes(engine_uuid)]

        self.log.info("task::task %r arrived on %r", msg_id, eid)
        if msg_id in self.unassigned:
            self.unassigned.remove(msg_id)
        # else:
        #     self.log.debug("task::task %r not listed as MIA?!"%(msg_id))

        self.tasks[eid].append(msg_id)
        # self.pending[msg_id][1].update(received=datetime.now(),engine=(eid,engine_uuid))
        try:
            self.db.update_record(msg_id, dict(engine_uuid=engine_uuid))
        except Exception:
            self.log.error("DB Error saving task destination %r", msg_id, exc_info=True)


    def mia_task_request(self, idents, msg):
        raise NotImplementedError
        client_id = idents[0]
        # content = dict(mia=self.mia,status='ok')
        # self.session.send('mia_reply', content=content, idents=client_id)


    #--------------------- IOPub Traffic ------------------------------

    def save_iopub_message(self, topics, msg):
        """save an iopub message into the db"""
        # print (topics)
        try:
            msg = self.session.unserialize(msg, content=True)
        except Exception:
            self.log.error("iopub::invalid IOPub message", exc_info=True)
            return

        parent = msg['parent_header']
        if not parent:
            self.log.error("iopub::invalid IOPub message: %r", msg)
            return
        msg_id = parent['msg_id']
        msg_type = msg['header']['msg_type']
        content = msg['content']

        # ensure msg_id is in db
        try:
            rec = self.db.get_record(msg_id)
        except KeyError:
            rec = empty_record()
            rec['msg_id'] = msg_id
            self.db.add_record(msg_id, rec)
        # stream
        d = {}
        if msg_type == 'stream':
            name = content['name']
            s = rec[name] or ''
            d[name] = s + content['data']

        elif msg_type == 'pyerr':
            d['pyerr'] = content
        elif msg_type == 'pyin':
            d['pyin'] = content['code']
        else:
            d[msg_type] = content.get('data', '')

        try:
            self.db.update_record(msg_id, d)
        except Exception:
            self.log.error("DB Error saving iopub message %r", msg_id, exc_info=True)



    #-------------------------------------------------------------------------
    # Registration requests
    #-------------------------------------------------------------------------

    def connection_request(self, client_id, msg):
        """Reply with connection addresses for clients."""
        self.log.info("client::client %r connected", client_id)
        content = dict(status='ok')
        content.update(self.client_info)
        jsonable = {}
        for k,v in self.keytable.iteritems():
            if v not in self.dead_engines:
                jsonable[str(k)] = v.decode('ascii')
        content['engines'] = jsonable
        self.session.send(self.query, 'connection_reply', content, parent=msg, ident=client_id)

    def register_engine(self, reg, msg):
        """Register a new engine."""
        content = msg['content']
        try:
            queue = util.asbytes(content['queue'])
        except KeyError:
            self.log.error("registration::queue not specified", exc_info=True)
            return
        heart = content.get('heartbeat', None)
        if heart:
            heart = util.asbytes(heart)
        """register a new engine, and create the socket(s) necessary"""
        eid = self._next_id
        # print (eid, queue, reg, heart)

        self.log.debug("registration::register_engine(%i, %r, %r, %r)", eid, queue, reg, heart)

        content = dict(id=eid,status='ok')
        content.update(self.engine_info)
        # check if requesting available IDs:
        if queue in self.by_ident:
            try:
                raise KeyError("queue_id %r in use" % queue)
            except:
                content = error.wrap_exception()
                self.log.error("queue_id %r in use", queue, exc_info=True)
        elif heart in self.hearts: # need to check unique hearts?
            try:
                raise KeyError("heart_id %r in use" % heart)
            except:
                self.log.error("heart_id %r in use", heart, exc_info=True)
                content = error.wrap_exception()
        else:
            for h, pack in self.incoming_registrations.iteritems():
                if heart == h:
                    try:
                        raise KeyError("heart_id %r in use" % heart)
                    except:
                        self.log.error("heart_id %r in use", heart, exc_info=True)
                        content = error.wrap_exception()
                    break
                elif queue == pack[1]:
                    try:
                        raise KeyError("queue_id %r in use" % queue)
                    except:
                        self.log.error("queue_id %r in use", queue, exc_info=True)
                        content = error.wrap_exception()
                    break

        msg = self.session.send(self.query, "registration_reply",
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
            self.log.error("registration::registration %i failed: %r", eid, content['evalue'])
        return eid

    def unregister_engine(self, ident, msg):
        """Unregister an engine that explicitly requested to leave."""
        try:
            eid = msg['content']['id']
        except:
            self.log.error("registration::bad engine id for unregistration: %r", ident, exc_info=True)
            return
        self.log.info("registration::unregister_engine(%r)", eid)
        # print (eid)
        uuid = self.keytable[eid]
        content=dict(id=eid, queue=uuid.decode('ascii'))
        self.dead_engines.add(uuid)
        # self.ids.remove(eid)
        # uuid = self.keytable.pop(eid)
        #
        # ec = self.engines.pop(eid)
        # self.hearts.pop(ec.heartbeat)
        # self.by_ident.pop(ec.queue)
        # self.completed.pop(eid)
        handleit = lambda : self._handle_stranded_msgs(eid, uuid)
        dc = ioloop.DelayedCallback(handleit, self.registration_timeout, self.loop)
        dc.start()
        ############## TODO: HANDLE IT ################

        if self.notifier:
            self.session.send(self.notifier, "unregistration_notification", content=content)

    def _handle_stranded_msgs(self, eid, uuid):
        """Handle messages known to be on an engine when the engine unregisters.

        It is possible that this will fire prematurely - that is, an engine will
        go down after completing a result, and the client will be notified
        that the result failed and later receive the actual result.
        """

        outstanding = self.queues[eid]

        for msg_id in outstanding:
            self.pending.remove(msg_id)
            self.all_completed.add(msg_id)
            try:
                raise error.EngineError("Engine %r died while running task %r" % (eid, msg_id))
            except:
                content = error.wrap_exception()
            # build a fake header:
            header = {}
            header['engine'] = uuid
            header['date'] = datetime.now()
            rec = dict(result_content=content, result_header=header, result_buffers=[])
            rec['completed'] = header['date']
            rec['engine_uuid'] = uuid
            try:
                self.db.update_record(msg_id, rec)
            except Exception:
                self.log.error("DB Error handling stranded msg %r", msg_id, exc_info=True)


    def finish_registration(self, heart):
        """Second half of engine registration, called after our HeartMonitor
        has received a beat from the Engine's Heart."""
        try:
            (eid,queue,reg,purge) = self.incoming_registrations.pop(heart)
        except KeyError:
            self.log.error("registration::tried to finish nonexistant registration", exc_info=True)
            return
        self.log.info("registration::finished registering engine %i:%r", eid, queue)
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
        content = dict(id=eid, queue=self.engines[eid].queue.decode('ascii'))
        if self.notifier:
            self.session.send(self.notifier, "registration_notification", content=content)
        self.log.info("engine::Engine Connected: %i", eid)

    def _purge_stalled_registration(self, heart):
        if heart in self.incoming_registrations:
            eid = self.incoming_registrations.pop(heart)[0]
            self.log.info("registration::purging stalled registration: %i", eid)
        else:
            pass

    #-------------------------------------------------------------------------
    # Client Requests
    #-------------------------------------------------------------------------

    def shutdown_request(self, client_id, msg):
        """handle shutdown request."""
        self.session.send(self.query, 'shutdown_reply', content={'status': 'ok'}, ident=client_id)
        # also notify other clients of shutdown
        self.session.send(self.notifier, 'shutdown_notice', content={'status': 'ok'})
        dc = ioloop.DelayedCallback(lambda : self._shutdown(), 1000, self.loop)
        dc.start()

    def _shutdown(self):
        self.log.info("hub::hub shutting down.")
        time.sleep(0.1)
        sys.exit(0)


    def check_load(self, client_id, msg):
        content = msg['content']
        try:
            targets = content['targets']
            targets = self._validate_targets(targets)
        except:
            content = error.wrap_exception()
            self.session.send(self.query, "hub_error",
                    content=content, ident=client_id)
            return

        content = dict(status='ok')
        # loads = {}
        for t in targets:
            content[bytes(t)] = len(self.queues[t])+len(self.tasks[t])
        self.session.send(self.query, "load_reply", content=content, ident=client_id)


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
            content = error.wrap_exception()
            self.session.send(self.query, "hub_error",
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
            content[str(t)] = {'queue': queue, 'completed': completed , 'tasks': tasks}
        content['unassigned'] = list(self.unassigned) if verbose else len(self.unassigned)
        # print (content)
        self.session.send(self.query, "queue_reply", content=content, ident=client_id)

    def purge_results(self, client_id, msg):
        """Purge results from memory. This method is more valuable before we move
        to a DB based message storage mechanism."""
        content = msg['content']
        self.log.info("Dropping records with %s", content)
        msg_ids = content.get('msg_ids', [])
        reply = dict(status='ok')
        if msg_ids == 'all':
            try:
                self.db.drop_matching_records(dict(completed={'$ne':None}))
            except Exception:
                reply = error.wrap_exception()
        else:
            pending = filter(lambda m: m in self.pending, msg_ids)
            if pending:
                try:
                    raise IndexError("msg pending: %r" % pending[0])
                except:
                    reply = error.wrap_exception()
            else:
                try:
                    self.db.drop_matching_records(dict(msg_id={'$in':msg_ids}))
                except Exception:
                    reply = error.wrap_exception()

            if reply['status'] == 'ok':
                eids = content.get('engine_ids', [])
                for eid in eids:
                    if eid not in self.engines:
                        try:
                            raise IndexError("No such engine: %i" % eid)
                        except:
                            reply = error.wrap_exception()
                        break
                    uid = self.engines[eid].queue
                    try:
                        self.db.drop_matching_records(dict(engine_uuid=uid, completed={'$ne':None}))
                    except Exception:
                        reply = error.wrap_exception()
                        break

        self.session.send(self.query, 'purge_reply', content=reply, ident=client_id)

    def resubmit_task(self, client_id, msg):
        """Resubmit one or more tasks."""
        def finish(reply):
            self.session.send(self.query, 'resubmit_reply', content=reply, ident=client_id)

        content = msg['content']
        msg_ids = content['msg_ids']
        reply = dict(status='ok')
        try:
            records = self.db.find_records({'msg_id' : {'$in' : msg_ids}}, keys=[
                'header', 'content', 'buffers'])
        except Exception:
            self.log.error('db::db error finding tasks to resubmit', exc_info=True)
            return finish(error.wrap_exception())

        # validate msg_ids
        found_ids = [ rec['msg_id'] for rec in records ]
        invalid_ids = filter(lambda m: m in self.pending, found_ids)
        if len(records) > len(msg_ids):
            try:
                raise RuntimeError("DB appears to be in an inconsistent state."
                    "More matching records were found than should exist")
            except Exception:
                return finish(error.wrap_exception())
        elif len(records) < len(msg_ids):
            missing = [ m for m in msg_ids if m not in found_ids ]
            try:
                raise KeyError("No such msg(s): %r" % missing)
            except KeyError:
                return finish(error.wrap_exception())
        elif invalid_ids:
            msg_id = invalid_ids[0]
            try:
                raise ValueError("Task %r appears to be inflight" % msg_id)
            except Exception:
                return finish(error.wrap_exception())

        # clear the existing records
        now = datetime.now()
        rec = empty_record()
        map(rec.pop, ['msg_id', 'header', 'content', 'buffers', 'submitted'])
        rec['resubmitted'] = now
        rec['queue'] = 'task'
        rec['client_uuid'] = client_id[0]
        try:
            for msg_id in msg_ids:
                self.all_completed.discard(msg_id)
                self.db.update_record(msg_id, rec)
        except Exception:
            self.log.error('db::db error upating record', exc_info=True)
            reply = error.wrap_exception()
        else:
            # send the messages
            for rec in records:
                header = rec['header']
                # include resubmitted in header to prevent digest collision
                header['resubmitted'] = now
                msg = self.session.msg(header['msg_type'])
                msg['content'] = rec['content']
                msg['header'] = header
                msg['header']['msg_id'] = rec['msg_id']
                self.session.send(self.resubmit, msg, buffers=rec['buffers'])

        finish(dict(status='ok'))


    def _extract_record(self, rec):
        """decompose a TaskRecord dict into subsection of reply for get_result"""
        io_dict = {}
        for key in 'pyin pyout pyerr stdout stderr'.split():
                io_dict[key] = rec[key]
        content = { 'result_content': rec['result_content'],
                            'header': rec['header'],
                            'result_header' : rec['result_header'],
                            'io' : io_dict,
                          }
        if rec['result_buffers']:
            buffers = map(bytes, rec['result_buffers'])
        else:
            buffers = []

        return content, buffers

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
            try:
                matches = self.db.find_records(dict(msg_id={'$in':msg_ids}))
                # turn match list into dict, for faster lookup
                records = {}
                for rec in matches:
                    records[rec['msg_id']] = rec
            except Exception:
                content = error.wrap_exception()
                self.session.send(self.query, "result_reply", content=content,
                                                    parent=msg, ident=client_id)
                return
        else:
            records = {}
        for msg_id in msg_ids:
            if msg_id in self.pending:
                pending.append(msg_id)
            elif msg_id in self.all_completed:
                completed.append(msg_id)
                if not statusonly:
                    c,bufs = self._extract_record(records[msg_id])
                    content[msg_id] = c
                    buffers.extend(bufs)
            elif msg_id in records:
                if rec['completed']:
                    completed.append(msg_id)
                    c,bufs = self._extract_record(records[msg_id])
                    content[msg_id] = c
                    buffers.extend(bufs)
                else:
                    pending.append(msg_id)
            else:
                try:
                    raise KeyError('No such message: '+msg_id)
                except:
                    content = error.wrap_exception()
                break
        self.session.send(self.query, "result_reply", content=content,
                                            parent=msg, ident=client_id,
                                            buffers=buffers)

    def get_history(self, client_id, msg):
        """Get a list of all msg_ids in our DB records"""
        try:
            msg_ids = self.db.get_history()
        except Exception as e:
            content = error.wrap_exception()
        else:
            content = dict(status='ok', history=msg_ids)

        self.session.send(self.query, "history_reply", content=content,
                                            parent=msg, ident=client_id)

    def db_query(self, client_id, msg):
        """Perform a raw query on the task record database."""
        content = msg['content']
        query = content.get('query', {})
        keys = content.get('keys', None)
        buffers = []
        empty = list()
        try:
            records = self.db.find_records(query, keys)
        except Exception as e:
            content = error.wrap_exception()
        else:
            # extract buffers from reply content:
            if keys is not None:
                buffer_lens = [] if 'buffers' in keys else None
                result_buffer_lens = [] if 'result_buffers' in keys else None
            else:
                buffer_lens = []
                result_buffer_lens = []

            for rec in records:
                # buffers may be None, so double check
                if buffer_lens is not None:
                    b = rec.pop('buffers', empty) or empty
                    buffer_lens.append(len(b))
                    buffers.extend(b)
                if result_buffer_lens is not None:
                    rb = rec.pop('result_buffers', empty) or empty
                    result_buffer_lens.append(len(rb))
                    buffers.extend(rb)
            content = dict(status='ok', records=records, buffer_lens=buffer_lens,
                                    result_buffer_lens=result_buffer_lens)
        # self.log.debug (content)
        self.session.send(self.query, "db_reply", content=content,
                                            parent=msg, ident=client_id,
                                            buffers=buffers)


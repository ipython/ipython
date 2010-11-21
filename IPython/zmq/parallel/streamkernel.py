#!/usr/bin/env python
"""
Kernel adapted from kernel.py to use ZMQ Streams
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports.
from __future__ import print_function
import __builtin__
from code import CommandCompiler
import os
import sys
import time
import traceback
from datetime import datetime
from signal import SIGTERM, SIGKILL
from pprint import pprint

# System library imports.
import zmq
from zmq.eventloop import ioloop, zmqstream

# Local imports.
from IPython.utils.traitlets import HasTraits, Instance, List
from IPython.zmq.completer import KernelCompleter
from IPython.zmq.log import logger # a Logger object

from streamsession import StreamSession, Message, extract_header, serialize_object,\
                unpack_apply_message, ISO8601
from dependency import UnmetDependency
import heartmonitor
from client import Client

def printer(*args):
    pprint(args)

#-----------------------------------------------------------------------------
# Main kernel class
#-----------------------------------------------------------------------------

class Kernel(HasTraits):

    #---------------------------------------------------------------------------
    # Kernel interface
    #---------------------------------------------------------------------------

    session = Instance(StreamSession)
    shell_streams = Instance(list)
    control_stream = Instance(zmqstream.ZMQStream)
    task_stream = Instance(zmqstream.ZMQStream)
    iopub_stream = Instance(zmqstream.ZMQStream)
    client = Instance(Client)
    
    def __init__(self, **kwargs):
        super(Kernel, self).__init__(**kwargs)
        self.identity = self.shell_streams[0].getsockopt(zmq.IDENTITY)
        self.user_ns = {}
        self.history = []
        self.compiler = CommandCompiler()
        self.completer = KernelCompleter(self.user_ns)
        self.aborted = set()
        
        # Build dict of handlers for message types
        self.shell_handlers = {}
        self.control_handlers = {}
        for msg_type in ['execute_request', 'complete_request', 'apply_request', 
                'clear_request']:
            self.shell_handlers[msg_type] = getattr(self, msg_type)
        
        for msg_type in ['shutdown_request', 'abort_request']+self.shell_handlers.keys():
            self.control_handlers[msg_type] = getattr(self, msg_type)

    #-------------------- control handlers -----------------------------
    def abort_queues(self):
        for stream in self.shell_streams:
            if stream:
                self.abort_queue(stream)
    
    def abort_queue(self, stream):
        while True:
            try:
                msg = self.session.recv(stream, zmq.NOBLOCK,content=True)
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    break
                else:
                    return
            else:
                if msg is None:
                    return
                else:
                    idents,msg = msg
                
                # assert self.reply_socketly_socket.rcvmore(), "Unexpected missing message part."
                # msg = self.reply_socket.recv_json()
            print ("Aborting:", file=sys.__stdout__)
            print (Message(msg), file=sys.__stdout__)
            msg_type = msg['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            # reply_msg = self.session.msg(reply_type, {'status' : 'aborted'}, msg)
            # self.reply_socket.send(ident,zmq.SNDMORE)
            # self.reply_socket.send_json(reply_msg)
            reply_msg = self.session.send(stream, reply_type, 
                        content={'status' : 'aborted'}, parent=msg, ident=idents)[0]
            print(Message(reply_msg), file=sys.__stdout__)
            # We need to wait a bit for requests to come in. This can probably
            # be set shorter for true asynchronous clients.
            time.sleep(0.05)
    
    def abort_request(self, stream, ident, parent):
        """abort a specifig msg by id"""
        msg_ids = parent['content'].get('msg_ids', None)
        if isinstance(msg_ids, basestring):
            msg_ids = [msg_ids]
        if not msg_ids:
            self.abort_queues()
        for mid in msg_ids:
            self.aborted.add(str(mid))
        
        content = dict(status='ok')
        reply_msg = self.session.send(stream, 'abort_reply', content=content, 
                parent=parent, ident=ident)[0]
        print(Message(reply_msg), file=sys.__stdout__)
    
    def shutdown_request(self, stream, ident, parent):
        """kill ourself.  This should really be handled in an external process"""
        self.abort_queues()
        content = dict(parent['content'])
        msg = self.session.send(stream, 'shutdown_reply',
                                content=content, parent=parent, ident=ident)
        # msg = self.session.send(self.pub_socket, 'shutdown_reply',
        #                         content, parent, ident)
        # print >> sys.__stdout__, msg
        time.sleep(0.1)
        sys.exit(0)    
    
    def dispatch_control(self, msg):
        idents,msg = self.session.feed_identities(msg, copy=False)
        try:
            msg = self.session.unpack_message(msg, content=True, copy=False)
        except:
            logger.error("Invalid Message", exc_info=True)
            return
        
        header = msg['header']
        msg_id = header['msg_id']
        
        handler = self.control_handlers.get(msg['msg_type'], None)
        if handler is None:
            print ("UNKNOWN CONTROL MESSAGE TYPE:", msg, file=sys.__stderr__)
        else:
            handler(self.control_stream, idents, msg)
    

    #-------------------- queue helpers ------------------------------
    
    def check_dependencies(self, dependencies):
        if not dependencies:
            return True
        if len(dependencies) == 2 and dependencies[0] in 'any all'.split():
            anyorall = dependencies[0]
            dependencies = dependencies[1]
        else:
            anyorall = 'all'
        results = self.client.get_results(dependencies,status_only=True)
        if results['status'] != 'ok':
            return False
        
        if anyorall == 'any':
            if not results['completed']:
                return False
        else:
            if results['pending']:
                return False
        
        return True
    
    def check_aborted(self, msg_id):
        return msg_id in self.aborted
    
    #-------------------- queue handlers -----------------------------
    
    def clear_request(self, stream, idents, parent):
        """Clear our namespace."""
        self.user_ns = {}
        msg = self.session.send(stream, 'clear_reply', ident=idents, parent=parent, 
                content = dict(status='ok'))
    
    def execute_request(self, stream, ident, parent):
        try:
            code = parent[u'content'][u'code']
        except:
            print("Got bad msg: ", file=sys.__stderr__)
            print(Message(parent), file=sys.__stderr__)
            return
        # pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        # self.iopub_stream.send(pyin_msg)
        self.session.send(self.iopub_stream, u'pyin', {u'code':code},parent=parent)
        started = datetime.now().strftime(ISO8601)
        try:
            comp_code = self.compiler(code, '<zmq-kernel>')
            # allow for not overriding displayhook
            if hasattr(sys.displayhook, 'set_parent'):
                sys.displayhook.set_parent(parent)
            exec comp_code in self.user_ns, self.user_ns
        except:
            # result = u'error'
            etype, evalue, tb = sys.exc_info()
            tb = traceback.format_exception(etype, evalue, tb)
            exc_content = {
                u'status' : u'error',
                u'traceback' : tb,
                u'etype' : unicode(etype),
                u'evalue' : unicode(evalue)
            }
            # exc_msg = self.session.msg(u'pyerr', exc_content, parent)
            self.session.send(self.iopub_stream, u'pyerr', exc_content, parent=parent)
            reply_content = exc_content
        else:
            reply_content = {'status' : 'ok'}
        # reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        # self.reply_socket.send(ident, zmq.SNDMORE)
        # self.reply_socket.send_json(reply_msg)
        reply_msg = self.session.send(stream, u'execute_reply', reply_content, parent=parent, 
                    ident=ident, subheader = dict(started=started))
        print(Message(reply_msg), file=sys.__stdout__)
        if reply_msg['content']['status'] == u'error':
            self.abort_queues()

    def complete_request(self, stream, ident, parent):
        matches = {'matches' : self.complete(parent),
                   'status' : 'ok'}
        completion_msg = self.session.send(stream, 'complete_reply',
                                           matches, parent, ident)
        # print >> sys.__stdout__, completion_msg

    def complete(self, msg):
        return self.completer.complete(msg.content.line, msg.content.text)
    
    def apply_request(self, stream, ident, parent):
        print (parent)
        try:
            content = parent[u'content']
            bufs = parent[u'buffers']
            msg_id = parent['header']['msg_id']
            bound = content.get('bound', False)
        except:
            print("Got bad msg: ", file=sys.__stderr__)
            print(Message(parent), file=sys.__stderr__)
            return
        # pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        # self.iopub_stream.send(pyin_msg)
        # self.session.send(self.iopub_stream, u'pyin', {u'code':code},parent=parent)
        sub = {'dependencies_met' : True, 'engine' : self.identity,
                'started': datetime.now().strftime(ISO8601)}
        try:
            # allow for not overriding displayhook
            if hasattr(sys.displayhook, 'set_parent'):
                sys.displayhook.set_parent(parent)
            # exec "f(*args,**kwargs)" in self.user_ns, self.user_ns
            if bound:
                working = self.user_ns
                suffix = str(msg_id).replace("-","")
                prefix = "_"
                
            else:
                working = dict()
                suffix = prefix = "_" # prevent keyword collisions with lambda
            f,args,kwargs = unpack_apply_message(bufs, working, copy=False)
            # if f.fun
            fname = prefix+f.func_name.strip('<>')+suffix
            argname = prefix+"args"+suffix
            kwargname = prefix+"kwargs"+suffix
            resultname = prefix+"result"+suffix
            
            ns = { fname : f, argname : args, kwargname : kwargs }
            # print ns
            working.update(ns)
            code = "%s=%s(*%s,**%s)"%(resultname, fname, argname, kwargname)
            exec code in working, working
            result = working.get(resultname)
            # clear the namespace
            if bound:
                for key in ns.iterkeys():
                    self.user_ns.pop(key)
            else:
                del working
            
            packed_result,buf = serialize_object(result)
            result_buf = [packed_result]+buf
        except:
            result = u'error'
            etype, evalue, tb = sys.exc_info()
            tb = traceback.format_exception(etype, evalue, tb)
            exc_content = {
                u'status' : u'error',
                u'traceback' : tb,
                u'etype' : unicode(etype),
                u'evalue' : unicode(evalue)
            }
            # exc_msg = self.session.msg(u'pyerr', exc_content, parent)
            self.session.send(self.iopub_stream, u'pyerr', exc_content, parent=parent)
            reply_content = exc_content
            result_buf = []
            
            if etype is UnmetDependency:
                sub['dependencies_met'] = False
        else:
            reply_content = {'status' : 'ok'}
        # reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        # self.reply_socket.send(ident, zmq.SNDMORE)
        # self.reply_socket.send_json(reply_msg)
        reply_msg = self.session.send(stream, u'apply_reply', reply_content, 
                    parent=parent, ident=ident,buffers=result_buf, subheader=sub)
        print(Message(reply_msg), file=sys.__stdout__)
        # if reply_msg['content']['status'] == u'error':
        #     self.abort_queues()
    
    def dispatch_queue(self, stream, msg):
        self.control_stream.flush()
        idents,msg = self.session.feed_identities(msg, copy=False)
        try:
            msg = self.session.unpack_message(msg, content=True, copy=False)
        except:
            logger.error("Invalid Message", exc_info=True)
            return
            
        
        header = msg['header']
        msg_id = header['msg_id']
        if self.check_aborted(msg_id):
            self.aborted.remove(msg_id)
            # is it safe to assume a msg_id will not be resubmitted?
            reply_type = msg['msg_type'].split('_')[0] + '_reply'
            reply_msg = self.session.send(stream, reply_type, 
                        content={'status' : 'aborted'}, parent=msg, ident=idents)
            return
        handler = self.shell_handlers.get(msg['msg_type'], None)
        if handler is None:
            print ("UNKNOWN MESSAGE TYPE:", msg, file=sys.__stderr__)
        else:
            handler(stream, idents, msg)
    
    def start(self):
        #### stream mode:
        if self.control_stream:
            self.control_stream.on_recv(self.dispatch_control, copy=False)
            self.control_stream.on_err(printer)
        
        def make_dispatcher(stream):
            def dispatcher(msg):
                return self.dispatch_queue(stream, msg)
            return dispatcher
        
        for s in self.shell_streams:
            s.on_recv(make_dispatcher(s), copy=False)
            s.on_err(printer)
        
        if self.iopub_stream:
            self.iopub_stream.on_err(printer)
            self.iopub_stream.on_send(printer)
        
        #### while True mode:
        # while True:
        #     idle = True
        #     try:
        #         msg = self.shell_stream.socket.recv_multipart(
        #                     zmq.NOBLOCK, copy=False)
        #     except zmq.ZMQError, e:
        #         if e.errno != zmq.EAGAIN:
        #             raise e
        #     else:
        #         idle=False
        #         self.dispatch_queue(self.shell_stream, msg)
        #             
        #     if not self.task_stream.empty():
        #         idle=False
        #         msg = self.task_stream.recv_multipart()
        #         self.dispatch_queue(self.task_stream, msg)
        #     if idle:
        #         # don't busywait
        #         time.sleep(1e-3)

def make_kernel(identity, control_addr, shell_addrs, iopub_addr, hb_addrs, 
                client_addr=None, loop=None, context=None, key=None):
    # create loop, context, and session:
    if loop is None:
        loop = ioloop.IOLoop.instance()
    if context is None:
        context = zmq.Context()
    c = context
    session = StreamSession(key=key)
    # print (session.key)
    print (control_addr, shell_addrs, iopub_addr, hb_addrs)
    
    # create Control Stream
    control_stream = zmqstream.ZMQStream(c.socket(zmq.PAIR), loop)
    control_stream.setsockopt(zmq.IDENTITY, identity)
    control_stream.connect(control_addr)
    
    # create Shell Streams (MUX, Task, etc.):
    shell_streams = []
    for addr in shell_addrs:
        stream = zmqstream.ZMQStream(c.socket(zmq.PAIR), loop)
        stream.setsockopt(zmq.IDENTITY, identity)
        stream.connect(addr)
        shell_streams.append(stream)
    
    # create iopub stream:
    iopub_stream = zmqstream.ZMQStream(c.socket(zmq.PUB), loop)
    iopub_stream.setsockopt(zmq.IDENTITY, identity)
    iopub_stream.connect(iopub_addr)
    
    # launch heartbeat
    heart = heartmonitor.Heart(*map(str, hb_addrs), heart_id=identity)
    heart.start()
    
    # create (optional) Client
    if client_addr:
        client = Client(client_addr, username=identity)
    else:
        client = None
    
    kernel = Kernel(session=session, control_stream=control_stream, 
            shell_streams=shell_streams, iopub_stream=iopub_stream, 
            client=client)
    kernel.start()
    return loop, c, kernel


#!/usr/bin/env python
"""
Kernel adapted from kernel.py to use ZMQ Streams
"""

import __builtin__
import os
import sys
import time
import traceback
from signal import SIGTERM, SIGKILL
from pprint import pprint

from code import CommandCompiler

import zmq
from zmq.eventloop import ioloop, zmqstream

from streamsession import StreamSession, Message, extract_header, serialize_object,\
                unpack_apply_message
from IPython.zmq.completer import KernelCompleter

def printer(*args):
    pprint(args)

class OutStream(object):
    """A file like object that publishes the stream to a 0MQ PUB socket."""

    def __init__(self, session, pub_socket, name, max_buffer=200):
        self.session = session
        self.pub_socket = pub_socket
        self.name = name
        self._buffer = []
        self._buffer_len = 0
        self.max_buffer = max_buffer
        self.parent_header = {}

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)

    def close(self):
        self.pub_socket = None

    def flush(self):
        if self.pub_socket is None:
            raise ValueError(u'I/O operation on closed file')
        else:
            if self._buffer:
                data = ''.join(self._buffer)
                content = {u'name':self.name, u'data':data}
                # msg = self.session.msg(u'stream', content=content,
                #                        parent=self.parent_header)
                msg = self.session.send(self.pub_socket, u'stream', content=content, parent=self.parent_header)
                # print>>sys.__stdout__, Message(msg)
                # self.pub_socket.send_json(msg)
                self._buffer_len = 0
                self._buffer = []

    def isattr(self):
        return False

    def next(self):
        raise IOError('Read not supported on a write only stream.')

    def read(self, size=None):
        raise IOError('Read not supported on a write only stream.')

    readline=read

    def write(self, s):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            self._buffer.append(s)
            self._buffer_len += len(s)
            self._maybe_send()

    def _maybe_send(self):
        if '\n' in self._buffer[-1]:
            self.flush()
        if self._buffer_len > self.max_buffer:
            self.flush()

    def writelines(self, sequence):
        if self.pub_socket is None:
            raise ValueError('I/O operation on closed file')
        else:
            for s in sequence:
                self.write(s)


class DisplayHook(object):

    def __init__(self, session, pub_socket):
        self.session = session
        self.pub_socket = pub_socket
        self.parent_header = {}

    def __call__(self, obj):
        if obj is None:
            return

        __builtin__._ = obj
        # msg = self.session.msg(u'pyout', {u'data':repr(obj)},
        #                        parent=self.parent_header)
        # self.pub_socket.send_json(msg)
        self.session.send(self.pub_socket, u'pyout', content={u'data':repr(obj)}, parent=self.parent_header)

    def set_parent(self, parent):
        self.parent_header = extract_header(parent)


class RawInput(object):

    def __init__(self, session, socket):
        self.session = session
        self.socket = socket

    def __call__(self, prompt=None):
        msg = self.session.msg(u'raw_input')
        self.socket.send_json(msg)
        while True:
            try:
                reply = self.socket.recv_json(zmq.NOBLOCK)
            except zmq.ZMQError, e:
                if e.errno == zmq.EAGAIN:
                    pass
                else:
                    raise
            else:
                break
        return reply[u'content'][u'data']


class Kernel(object):

    def __init__(self, session, control_stream, reply_stream, pub_stream, 
                                            task_stream=None, client=None):
        self.session = session
        self.control_stream = control_stream
        # self.control_socket = control_stream.socket
        self.reply_stream = reply_stream
        self.task_stream = task_stream
        self.pub_stream = pub_stream
        self.client = client
        self.user_ns = {}
        self.history = []
        self.compiler = CommandCompiler()
        self.completer = KernelCompleter(self.user_ns)
        self.aborted = set()
        
        # Build dict of handlers for message types
        self.queue_handlers = {}
        self.control_handlers = {}
        for msg_type in ['execute_request', 'complete_request', 'apply_request']:
            self.queue_handlers[msg_type] = getattr(self, msg_type)
        
        for msg_type in ['kill_request', 'abort_request']:
            self.control_handlers[msg_type] = getattr(self, msg_type)

    #-------------------- control handlers -----------------------------
    def abort_queues(self):
        for stream in (self.task_stream, self.reply_stream):
            if stream:
                self.abort_queue(stream)
    
    def abort_queue(self, stream):
        while True:
            try:
                msg = self.session.recv(stream, zmq.NOBLOCK,content=True)
            except zmq.ZMQError, e:
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
            print>>sys.__stdout__, "Aborting:"
            print>>sys.__stdout__, Message(msg)
            msg_type = msg['msg_type']
            reply_type = msg_type.split('_')[0] + '_reply'
            # reply_msg = self.session.msg(reply_type, {'status' : 'aborted'}, msg)
            # self.reply_socket.send(ident,zmq.SNDMORE)
            # self.reply_socket.send_json(reply_msg)
            reply_msg = self.session.send(stream, reply_type, 
                        content={'status' : 'aborted'}, parent=msg, ident=idents)
            print>>sys.__stdout__, Message(reply_msg)
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
        reply_msg = self.session.send(stream, 'abort_reply', content=content, parent=parent,
                                                                    ident=ident)
        print>>sys.__stdout__, Message(reply_msg)
    
    def kill_request(self, stream, idents, parent):
        """kill ourselves.  This should really be handled in an external process"""
        self.abort_queues()
        msg = self.session.send(stream, 'kill_reply', ident=idents, parent=parent, 
                content = dict(status='ok'))
        # we can know that a message is done if we *don't* use streams, but 
        # use a socket directly with MessageTracker
        time.sleep(.5)
        os.kill(os.getpid(), SIGTERM)
        time.sleep(1)
        os.kill(os.getpid(), SIGKILL)
    
    def dispatch_control(self, msg):
        idents,msg = self.session.feed_identities(msg, copy=False)
        msg = self.session.unpack_message(msg, content=True, copy=False)
        
        header = msg['header']
        msg_id = header['msg_id']
        
        handler = self.control_handlers.get(msg['msg_type'], None)
        if handler is None:
            print >> sys.__stderr__, "UNKNOWN CONTROL MESSAGE TYPE:", msg
        else:
            handler(self.control_stream, idents, msg)
    
    # def flush_control(self):
    #     while any(zmq.select([self.control_socket],[],[],1e-4)):
    #         try:
    #             msg = self.control_socket.recv_multipart(zmq.NOBLOCK, copy=False)
    #         except zmq.ZMQError, e:
    #             if e.errno != zmq.EAGAIN:
    #                 raise e
    #             return
    #         else:
    #             self.dispatch_control(msg)
    

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
    
    def unmet_dependencies(self, stream, idents, msg):
        reply_type = msg['msg_type'].split('_')[0] + '_reply'
        content = dict(status='resubmitted', reason='unmet dependencies')
        reply_msg = self.session.send(stream, reply_type, 
                    content=content, parent=msg, ident=idents)
        ### TODO: actually resubmit it ###
    
    #-------------------- queue handlers -----------------------------
    
    def execute_request(self, stream, ident, parent):
        try:
            code = parent[u'content'][u'code']
        except:
            print>>sys.__stderr__, "Got bad msg: "
            print>>sys.__stderr__, Message(parent)
            return
        # pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        # self.pub_stream.send(pyin_msg)
        self.session.send(self.pub_stream, u'pyin', {u'code':code},parent=parent)
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
            self.session.send(self.pub_stream, u'pyerr', exc_content, parent=parent)
            reply_content = exc_content
        else:
            reply_content = {'status' : 'ok'}
        # reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        # self.reply_socket.send(ident, zmq.SNDMORE)
        # self.reply_socket.send_json(reply_msg)
        reply_msg = self.session.send(stream, u'execute_reply', reply_content, parent=parent, ident=ident)
        # print>>sys.__stdout__, Message(reply_msg)
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
        try:
            content = parent[u'content']
            bufs = parent[u'buffers']
            msg_id = parent['header']['msg_id']
            bound = content.get('bound', False)
        except:
            print>>sys.__stderr__, "Got bad msg: "
            print>>sys.__stderr__, Message(parent)
            return
        # pyin_msg = self.session.msg(u'pyin',{u'code':code}, parent=parent)
        # self.pub_stream.send(pyin_msg)
        # self.session.send(self.pub_stream, u'pyin', {u'code':code},parent=parent)
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
            self.session.send(self.pub_stream, u'pyerr', exc_content, parent=parent)
            reply_content = exc_content
            result_buf = []
        else:
            reply_content = {'status' : 'ok'}
        # reply_msg = self.session.msg(u'execute_reply', reply_content, parent)
        # self.reply_socket.send(ident, zmq.SNDMORE)
        # self.reply_socket.send_json(reply_msg)
        reply_msg = self.session.send(stream, u'apply_reply', reply_content, parent=parent, ident=ident,buffers=result_buf)
        # print>>sys.__stdout__, Message(reply_msg)
        if reply_msg['content']['status'] == u'error':
            self.abort_queues()
    
    def dispatch_queue(self, stream, msg):
        self.control_stream.flush()
        idents,msg = self.session.feed_identities(msg, copy=False)
        msg = self.session.unpack_message(msg, content=True, copy=False)
        
        header = msg['header']
        msg_id = header['msg_id']
        dependencies = header.get('dependencies', [])
        if self.check_aborted(msg_id):
            self.aborted.remove(msg_id)
            # is it safe to assume a msg_id will not be resubmitted?
            reply_type = msg['msg_type'].split('_')[0] + '_reply'
            reply_msg = self.session.send(stream, reply_type, 
                        content={'status' : 'aborted'}, parent=msg, ident=idents)
            return
        if not self.check_dependencies(dependencies):
            return self.unmet_dependencies(stream, idents, msg)
        handler = self.queue_handlers.get(msg['msg_type'], None)
        if handler is None:
            print >> sys.__stderr__, "UNKNOWN MESSAGE TYPE:", msg
        else:
            handler(stream, idents, msg)
    
    def start(self):
        #### stream mode:
        if self.control_stream:
            self.control_stream.on_recv(self.dispatch_control, copy=False)
            self.control_stream.on_err(printer)
        if self.reply_stream:
            self.reply_stream.on_recv(lambda msg: 
                    self.dispatch_queue(self.reply_stream, msg), copy=False)
            self.reply_stream.on_err(printer)
        if self.task_stream:
            self.task_stream.on_recv(lambda msg: 
                    self.dispatch_queue(self.task_stream, msg), copy=False)
            self.task_stream.on_err(printer)
        
        #### while True mode:
        # while True:
        #     idle = True
        #     try:
        #         msg = self.reply_stream.socket.recv_multipart(
        #                     zmq.NOBLOCK, copy=False)
        #     except zmq.ZMQError, e:
        #         if e.errno != zmq.EAGAIN:
        #             raise e
        #     else:
        #         idle=False
        #         self.dispatch_queue(self.reply_stream, msg)
        #             
        #     if not self.task_stream.empty():
        #         idle=False
        #         msg = self.task_stream.recv_multipart()
        #         self.dispatch_queue(self.task_stream, msg)
        #     if idle:
        #         # don't busywait
        #         time.sleep(1e-3)


def main():
    raise Exception("Don't run me anymore")
    loop = ioloop.IOLoop.instance()
    c = zmq.Context()

    ip = '127.0.0.1'
    port_base = 5575
    connection = ('tcp://%s' % ip) + ':%i'
    rep_conn = connection % port_base
    pub_conn = connection % (port_base+1)

    print >>sys.__stdout__, "Starting the kernel..."
    # print >>sys.__stdout__, "XREQ Channel:", rep_conn
    # print >>sys.__stdout__, "PUB Channel:", pub_conn

    session = StreamSession(username=u'kernel')

    reply_socket = c.socket(zmq.XREQ)
    reply_socket.connect(rep_conn)

    pub_socket = c.socket(zmq.PUB)
    pub_socket.connect(pub_conn)

    stdout = OutStream(session, pub_socket, u'stdout')
    stderr = OutStream(session, pub_socket, u'stderr')
    sys.stdout = stdout
    sys.stderr = stderr

    display_hook = DisplayHook(session, pub_socket)
    sys.displayhook = display_hook
    reply_stream = zmqstream.ZMQStream(reply_socket,loop)
    pub_stream = zmqstream.ZMQStream(pub_socket,loop)
    kernel = Kernel(session, reply_stream, pub_stream)

    # For debugging convenience, put sleep and a string in the namespace, so we
    # have them every time we start.
    kernel.user_ns['sleep'] = time.sleep
    kernel.user_ns['s'] = 'Test string'
    
    print >>sys.__stdout__, "Use Ctrl-\\ (NOT Ctrl-C!) to terminate."
    kernel.start()
    loop.start()


if __name__ == '__main__':
    main()

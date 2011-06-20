#!/usr/bin/env python
"""Session object for building, serializing, sending, and receiving messages in
IPython. The Session object supports serialization, HMAC signatures, and
metadata on messages.

Also defined here are utilities for working with Sessions:
* A SessionFactory to be used as a base class for configurables that work with
Sessions.
* A Message object for convenience that allows attribute-access to the msg dict.

Authors:

* Min RK
* Brian Granger
* Fernando Perez
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

import hmac
import logging
import os
import pprint
import uuid
from datetime import datetime

try:
    import cPickle
    pickle = cPickle
except:
    cPickle = None
    import pickle

import zmq
from zmq.utils import jsonapi
from zmq.eventloop.ioloop import IOLoop
from zmq.eventloop.zmqstream import ZMQStream

from IPython.config.configurable import Configurable, LoggingConfigurable
from IPython.utils.importstring import import_item
from IPython.utils.jsonutil import extract_dates, squash_dates, date_default
from IPython.utils.traitlets import CStr, Unicode, Bool, Any, Instance, Set

#-----------------------------------------------------------------------------
# utility functions
#-----------------------------------------------------------------------------

def squash_unicode(obj):
    """coerce unicode back to bytestrings."""
    if isinstance(obj,dict):
        for key in obj.keys():
            obj[key] = squash_unicode(obj[key])
            if isinstance(key, unicode):
                obj[squash_unicode(key)] = obj.pop(key)
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            obj[i] = squash_unicode(v)
    elif isinstance(obj, unicode):
        obj = obj.encode('utf8')
    return obj

#-----------------------------------------------------------------------------
# globals and defaults
#-----------------------------------------------------------------------------
key = 'on_unknown' if jsonapi.jsonmod.__name__ == 'jsonlib' else 'default'
json_packer = lambda obj: jsonapi.dumps(obj, **{key:date_default})
json_unpacker = lambda s: extract_dates(jsonapi.loads(s))

pickle_packer = lambda o: pickle.dumps(o,-1)
pickle_unpacker = pickle.loads

default_packer = json_packer
default_unpacker = json_unpacker


DELIM="<IDS|MSG>"

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SessionFactory(LoggingConfigurable):
    """The Base class for configurables that have a Session, Context, logger,
    and IOLoop.
    """
    
    logname = Unicode('')
    def _logname_changed(self, name, old, new):
        self.log = logging.getLogger(new)
    
    # not configurable:
    context = Instance('zmq.Context')
    def _context_default(self):
        return zmq.Context.instance()
    
    session = Instance('IPython.zmq.session.Session')
    
    loop = Instance('zmq.eventloop.ioloop.IOLoop', allow_none=False)
    def _loop_default(self):
        return IOLoop.instance()
    
    def __init__(self, **kwargs):
        super(SessionFactory, self).__init__(**kwargs)
        
        if self.session is None:
            # construct the session
            self.session = Session(**kwargs)
    

class Message(object):
    """A simple message object that maps dict keys to attributes.

    A Message can be created from a dict and a dict from a Message instance
    simply by calling dict(msg_obj)."""
    
    def __init__(self, msg_dict):
        dct = self.__dict__
        for k, v in dict(msg_dict).iteritems():
            if isinstance(v, dict):
                v = Message(v)
            dct[k] = v

    # Having this iterator lets dict(msg_obj) work out of the box.
    def __iter__(self):
        return iter(self.__dict__.iteritems())
    
    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return pprint.pformat(self.__dict__)

    def __contains__(self, k):
        return k in self.__dict__

    def __getitem__(self, k):
        return self.__dict__[k]


def msg_header(msg_id, msg_type, username, session):
    date = datetime.now()
    return locals()

def extract_header(msg_or_header):
    """Given a message or header, return the header."""
    if not msg_or_header:
        return {}
    try:
        # See if msg_or_header is the entire message.
        h = msg_or_header['header']
    except KeyError:
        try:
            # See if msg_or_header is just the header
            h = msg_or_header['msg_id']
        except KeyError:
            raise
        else:
            h = msg_or_header
    if not isinstance(h, dict):
        h = dict(h)
    return h

class Session(Configurable):
    """Object for handling serialization and sending of messages.
    
    The Session object handles building messages and sending them
    with ZMQ sockets or ZMQStream objects.  Objects can communicate with each
    other over the network via Session objects, and only need to work with the
    dict-based IPython message spec. The Session will handle 
    serialization/deserialization, security, and metadata.
    
    Sessions support configurable serialiization via packer/unpacker traits,
    and signing with HMAC digests via the key/keyfile traits.
    
    Parameters
    ----------
    
    debug : bool
        whether to trigger extra debugging statements
    packer/unpacker : str : 'json', 'pickle' or import_string
        importstrings for methods to serialize message parts.  If just
        'json' or 'pickle', predefined JSON and pickle packers will be used.
        Otherwise, the entire importstring must be used.
        
        The functions must accept at least valid JSON input, and output *bytes*.
        
        For example, to use msgpack:
        packer = 'msgpack.packb', unpacker='msgpack.unpackb'
    pack/unpack : callables
        You can also set the pack/unpack callables for serialization directly.
    session : bytes
        the ID of this Session object.  The default is to generate a new UUID.
    username : unicode
        username added to message headers.  The default is to ask the OS.
    key : bytes
        The key used to initialize an HMAC signature.  If unset, messages
        will not be signed or checked.
    keyfile : filepath
        The file containing a key.  If this is set, `key` will be initialized
        to the contents of the file.
    
    """
    
    debug=Bool(False, config=True, help="""Debug output in the Session""")
    
    packer = Unicode('json',config=True,
            help="""The name of the packer for serializing messages.
            Should be one of 'json', 'pickle', or an import name
            for a custom callable serializer.""")
    def _packer_changed(self, name, old, new):
        if new.lower() == 'json':
            self.pack = json_packer
            self.unpack = json_unpacker
        elif new.lower() == 'pickle':
            self.pack = pickle_packer
            self.unpack = pickle_unpacker
        else:
            self.pack = import_item(str(new))

    unpacker = Unicode('json', config=True,
        help="""The name of the unpacker for unserializing messages.
        Only used with custom functions for `packer`.""")
    def _unpacker_changed(self, name, old, new):
        if new.lower() == 'json':
            self.pack = json_packer
            self.unpack = json_unpacker
        elif new.lower() == 'pickle':
            self.pack = pickle_packer
            self.unpack = pickle_unpacker
        else:
            self.unpack = import_item(str(new))
        
    session = CStr('', config=True,
        help="""The UUID identifying this session.""")
    def _session_default(self):
        return bytes(uuid.uuid4())
    
    username = Unicode(os.environ.get('USER','username'), config=True,
        help="""Username for the Session. Default is your system username.""")
    
    # message signature related traits:
    key = CStr('', config=True,
        help="""execution key, for extra authentication.""")
    def _key_changed(self, name, old, new):
        if new:
            self.auth = hmac.HMAC(new)
        else:
            self.auth = None
    auth = Instance(hmac.HMAC)
    digest_history = Set()
    
    keyfile = Unicode('', config=True,
        help="""path to file containing execution key.""")
    def _keyfile_changed(self, name, old, new):
        with open(new, 'rb') as f:
            self.key = f.read().strip()

    pack = Any(default_packer) # the actual packer function
    def _pack_changed(self, name, old, new):
        if not callable(new):
            raise TypeError("packer must be callable, not %s"%type(new))
    
    unpack = Any(default_unpacker) # the actual packer function
    def _unpack_changed(self, name, old, new):
        # unpacker is not checked - it is assumed to be 
        if not callable(new):
            raise TypeError("unpacker must be callable, not %s"%type(new))

    def __init__(self, **kwargs):
        """create a Session object
        
        Parameters
        ----------

        debug : bool
            whether to trigger extra debugging statements
        packer/unpacker : str : 'json', 'pickle' or import_string
            importstrings for methods to serialize message parts.  If just
            'json' or 'pickle', predefined JSON and pickle packers will be used.
            Otherwise, the entire importstring must be used.

            The functions must accept at least valid JSON input, and output
            *bytes*.

            For example, to use msgpack:
            packer = 'msgpack.packb', unpacker='msgpack.unpackb'
        pack/unpack : callables
            You can also set the pack/unpack callables for serialization
            directly.
        session : bytes
            the ID of this Session object.  The default is to generate a new 
            UUID.
        username : unicode
            username added to message headers.  The default is to ask the OS.
        key : bytes
            The key used to initialize an HMAC signature.  If unset, messages
            will not be signed or checked.
        keyfile : filepath
            The file containing a key.  If this is set, `key` will be 
            initialized to the contents of the file.
        """
        super(Session, self).__init__(**kwargs)
        self._check_packers()
        self.none = self.pack({})

    @property
    def msg_id(self):
        """always return new uuid"""
        return str(uuid.uuid4())

    def _check_packers(self):
        """check packers for binary data and datetime support."""
        pack = self.pack
        unpack = self.unpack
        
        # check simple serialization
        msg = dict(a=[1,'hi'])
        try:
            packed = pack(msg)
        except Exception:
            raise ValueError("packer could not serialize a simple message")
        
        # ensure packed message is bytes
        if not isinstance(packed, bytes):
            raise ValueError("message packed to %r, but bytes are required"%type(packed))
        
        # check that unpack is pack's inverse
        try:
            unpacked = unpack(packed)
        except Exception:
            raise ValueError("unpacker could not handle the packer's output")
        
        # check datetime support
        msg = dict(t=datetime.now())
        try:
            unpacked = unpack(pack(msg))
        except Exception:
            self.pack = lambda o: pack(squash_dates(o))
            self.unpack = lambda s: extract_dates(unpack(s))
    
    def msg_header(self, msg_type):
        return msg_header(self.msg_id, msg_type, self.username, self.session)

    def msg(self, msg_type, content=None, parent=None, subheader=None):
        msg = {}
        msg['header'] = self.msg_header(msg_type)
        msg['msg_id'] = msg['header']['msg_id']
        msg['parent_header'] = {} if parent is None else extract_header(parent)
        msg['msg_type'] = msg_type
        msg['content'] = {} if content is None else content
        sub = {} if subheader is None else subheader
        msg['header'].update(sub)
        return msg

    def sign(self, msg):
        """Sign a message with HMAC digest. If no auth, return b''."""
        if self.auth is None:
            return b''
        h = self.auth.copy()
        for m in msg:
            h.update(m)
        return h.hexdigest()
    
    def serialize(self, msg, ident=None):
        """Serialize the message components to bytes.
        
        Returns
        -------
        
        list of bytes objects
        
        """
        content = msg.get('content', {})
        if content is None:
            content = self.none
        elif isinstance(content, dict):
            content = self.pack(content)
        elif isinstance(content, bytes):
            # content is already packed, as in a relayed message
            pass
        elif isinstance(content, unicode):
            # should be bytes, but JSON often spits out unicode
            content = content.encode('utf8')
        else:
            raise TypeError("Content incorrect type: %s"%type(content))
        
        real_message = [self.pack(msg['header']), 
                        self.pack(msg['parent_header']), 
                        content
        ]
        
        to_send = []

        if isinstance(ident, list):
            # accept list of idents
            to_send.extend(ident)
        elif ident is not None:
            to_send.append(ident)
        to_send.append(DELIM)
        
        signature = self.sign(real_message)
        to_send.append(signature)
        
        to_send.extend(real_message)

        return to_send
        
    def send(self, stream, msg_or_type, content=None, parent=None, ident=None, 
                                    buffers=None, subheader=None, track=False):
        """Build and send a message via stream or socket.
        
        Parameters
        ----------
        
        stream : zmq.Socket or ZMQStream
            the socket-like object used to send the data
        msg_or_type : str or Message/dict
            Normally, msg_or_type will be a msg_type unless a message is being 
            sent more than once.
        
        content : dict or None
            the content of the message (ignored if msg_or_type is a message)
        parent : Message or dict or None
            the parent or parent header describing the parent of this message
        ident : bytes or list of bytes
            the zmq.IDENTITY routing path
        subheader : dict or None
            extra header keys for this message's header
        buffers : list or None
            the already-serialized buffers to be appended to the message
        track : bool
            whether to track.  Only for use with Sockets, 
            because ZMQStream objects cannot track messages.
        
        Returns
        -------
        msg : message dict
            the constructed message
        (msg,tracker) : (message dict, MessageTracker)
            if track=True, then a 2-tuple will be returned, 
            the first element being the constructed
            message, and the second being the MessageTracker
            
        """

        if not isinstance(stream, (zmq.Socket, ZMQStream)):
            raise TypeError("stream must be Socket or ZMQStream, not %r"%type(stream))
        elif track and isinstance(stream, ZMQStream):
            raise TypeError("ZMQStream cannot track messages")
        
        if isinstance(msg_or_type, (Message, dict)):
            # we got a Message, not a msg_type
            # don't build a new Message
            msg = msg_or_type
        else:
            msg = self.msg(msg_or_type, content, parent, subheader)
        
        buffers = [] if buffers is None else buffers
        to_send = self.serialize(msg, ident)
        flag = 0
        if buffers:
            flag = zmq.SNDMORE
            _track = False
        else:
            _track=track
        if track:
            tracker = stream.send_multipart(to_send, flag, copy=False, track=_track)
        else:
            tracker = stream.send_multipart(to_send, flag, copy=False)
        for b in buffers[:-1]:
            stream.send(b, flag, copy=False)
        if buffers:
            if track:
                tracker = stream.send(buffers[-1], copy=False, track=track)
            else:
                tracker = stream.send(buffers[-1], copy=False)
                
        # omsg = Message(msg)
        if self.debug:
            pprint.pprint(msg)
            pprint.pprint(to_send)
            pprint.pprint(buffers)
        
        msg['tracker'] = tracker
        
        return msg
    
    def send_raw(self, stream, msg, flags=0, copy=True, ident=None):
        """Send a raw message via ident path.
        
        Parameters
        ----------
        msg : list of sendable buffers"""
        to_send = []
        if isinstance(ident, bytes):
            ident = [ident]
        if ident is not None:
            to_send.extend(ident)
            
        to_send.append(DELIM)
        to_send.append(self.sign(msg))
        to_send.extend(msg)
        stream.send_multipart(msg, flags, copy=copy)
    
    def recv(self, socket, mode=zmq.NOBLOCK, content=True, copy=True):
        """receives and unpacks a message
        returns [idents], msg"""
        if isinstance(socket, ZMQStream):
            socket = socket.socket
        try:
            msg = socket.recv_multipart(mode)
        except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
                # We can convert EAGAIN to None as we know in this case
                # recv_multipart won't return None.
                return None,None
            else:
                raise
        # split multipart message into identity list and message dict
        # invalid large messages can cause very expensive string comparisons
        idents, msg = self.feed_identities(msg, copy)
        try:
            return idents, self.unpack_message(msg, content=content, copy=copy)
        except Exception as e:
            print (idents, msg)
            # TODO: handle it
            raise e
    
    def feed_identities(self, msg, copy=True):
        """feed until DELIM is reached, then return the prefix as idents and
        remainder as msg. This is easily broken by setting an IDENT to DELIM,
        but that would be silly.
        
        Parameters
        ----------
        msg : a list of Message or bytes objects
            the message to be split
        copy : bool
            flag determining whether the arguments are bytes or Messages
        
        Returns
        -------
        (idents,msg) : two lists
            idents will always be a list of bytes - the indentity prefix
            msg will be a list of bytes or Messages, unchanged from input
            msg should be unpackable via self.unpack_message at this point.
        """
        if copy:
            idx = msg.index(DELIM)
            return msg[:idx], msg[idx+1:]
        else:
            failed = True
            for idx,m in enumerate(msg):
                if m.bytes == DELIM:
                    failed = False
                    break
            if failed:
                raise ValueError("DELIM not in msg")
            idents, msg = msg[:idx], msg[idx+1:]
            return [m.bytes for m in idents], msg
    
    def unpack_message(self, msg, content=True, copy=True):
        """Return a message object from the format
        sent by self.send.
        
        Parameters:
        -----------
        
        content : bool (True)
            whether to unpack the content dict (True), 
            or leave it serialized (False)
        
        copy : bool (True)
            whether to return the bytes (True), 
            or the non-copying Message object in each place (False)
        
        """
        minlen = 4
        message = {}
        if not copy:
            for i in range(minlen):
                msg[i] = msg[i].bytes
        if self.auth is not None:
            signature = msg[0]
            if signature in self.digest_history:
                raise ValueError("Duplicate Signature: %r"%signature)
            self.digest_history.add(signature)
            check = self.sign(msg[1:4])
            if not signature == check:
                raise ValueError("Invalid Signature: %r"%signature)
        if not len(msg) >= minlen:
            raise TypeError("malformed message, must have at least %i elements"%minlen)
        message['header'] = self.unpack(msg[1])
        message['msg_type'] = message['header']['msg_type']
        message['parent_header'] = self.unpack(msg[2])
        if content:
            message['content'] = self.unpack(msg[3])
        else:
            message['content'] = msg[3]
        
        message['buffers'] = msg[4:]
        return message

def test_msg2obj():
    am = dict(x=1)
    ao = Message(am)
    assert ao.x == am['x']

    am['y'] = dict(z=1)
    ao = Message(am)
    assert ao.y.z == am['y']['z']
    
    k1, k2 = 'y', 'z'
    assert ao[k1][k2] == am[k1][k2]
    
    am2 = dict(ao)
    assert am['x'] == am2['x']
    assert am['y']['z'] == am2['y']['z']


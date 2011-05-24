#!/usr/bin/env python
"""edited session.py to work with streams, and move msg_type to the header
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------


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
from zmq.eventloop.zmqstream import ZMQStream

from IPython.config.configurable import Configurable
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import CStr, Unicode, Bool, Any

from .util import ISO8601


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

def _date_default(obj):
    if isinstance(obj, datetime):
        return obj.strftime(ISO8601)
    else:
        raise TypeError("%r is not JSON serializable"%obj)

_default_key = 'on_unknown' if jsonapi.jsonmod.__name__ == 'jsonlib' else 'default'
json_packer = lambda obj: jsonapi.dumps(obj, **{_default_key:_date_default})
json_unpacker = lambda s: squash_unicode(jsonapi.loads(s))

pickle_packer = lambda o: pickle.dumps(o,-1)
pickle_unpacker = pickle.loads

default_packer = json_packer
default_unpacker = json_unpacker


DELIM="<IDS|MSG>"

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
    date=datetime.now().strftime(ISO8601)
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

class StreamSession(Configurable):
    """tweaked version of IPython.zmq.session.Session, for development in Parallel"""
    debug=Bool(False, config=True, help="""Debug output in the StreamSession""")
    packer = Unicode('json',config=True,
            help="""The name of the packer for serializing messages.
            Should be one of 'json', 'pickle', or an import name
            for a custom serializer.""")
    def _packer_changed(self, name, old, new):
        if new.lower() == 'json':
            self.pack = json_packer
            self.unpack = json_unpacker
        elif new.lower() == 'pickle':
            self.pack = pickle_packer
            self.unpack = pickle_unpacker
        else:
            self.pack = import_item(new)

    unpacker = Unicode('json',config=True,
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
            self.unpack = import_item(new)
        
    session = CStr('',config=True,
        help="""The UUID identifying this session.""")
    def _session_default(self):
        return bytes(uuid.uuid4())
    username = Unicode(os.environ.get('USER','username'),config=True,
        help="""Username for the Session. Default is your system username.""")
    key = CStr('', config=True,
        help="""execution key, for extra authentication.""")

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
        if not callable(new):
            raise TypeError("packer must be callable, not %s"%type(new))

    def __init__(self, **kwargs):
        super(StreamSession, self).__init__(**kwargs)
        self.none = self.pack({})

    @property
    def msg_id(self):
        """always return new uuid"""
        return str(uuid.uuid4())

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

    def check_key(self, msg_or_header):
        """Check that a message's header has the right key"""
        if not self.key:
            return True
        header = extract_header(msg_or_header)
        return header.get('key', '') == self.key
            

    def serialize(self, msg, ident=None):
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

        to_send = []

        if isinstance(ident, list):
            # accept list of idents
            to_send.extend(ident)
        elif ident is not None:
            to_send.append(ident)
        to_send.append(DELIM)
        if self.key:
            to_send.append(self.key)
        to_send.append(self.pack(msg['header']))
        to_send.append(self.pack(msg['parent_header']))
        to_send.append(content)

        return to_send
        
    def send(self, stream, msg_or_type, content=None, buffers=None, parent=None, subheader=None, ident=None, track=False):
        """Build and send a message via stream or socket.
        
        Parameters
        ----------
        
        stream : zmq.Socket or ZMQStream
            the socket-like object used to send the data
        msg_or_type : str or Message/dict
            Normally, msg_or_type will be a msg_type unless a message is being sent more
            than once.
        
        content : dict or None
            the content of the message (ignored if msg_or_type is a message)
        buffers : list or None
            the already-serialized buffers to be appended to the message
        parent : Message or dict or None
            the parent or parent header describing the parent of this message
        subheader : dict or None
            extra header keys for this message's header
        ident : bytes or list of bytes
            the zmq.IDENTITY routing path
        track : bool
            whether to track.  Only for use with Sockets, because ZMQStream objects cannot track messages.
        
        Returns
        -------
        msg : message dict
            the constructed message
        (msg,tracker) : (message dict, MessageTracker)
            if track=True, then a 2-tuple will be returned, the first element being the constructed
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
        if self.key:
            to_send.append(self.key)
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
                return None
            else:
                raise
        # return an actual Message object
        # determine the number of idents by trying to unpack them.
        # this is terrible:
        idents, msg = self.feed_identities(msg, copy)
        try:
            return idents, self.unpack_message(msg, content=content, copy=copy)
        except Exception as e:
            print (idents, msg)
            # TODO: handle it
            raise e
    
    def feed_identities(self, msg, copy=True):
        """feed until DELIM is reached, then return the prefix as idents and remainder as
        msg. This is easily broken by setting an IDENT to DELIM, but that would be silly.
        
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
        ikey = int(self.key != '')
        minlen = 3 + ikey
        msg = list(msg)
        idents = []
        while len(msg) > minlen:
            if copy:
                s = msg[0]
            else:
                s = msg[0].bytes
            if s == DELIM:
                msg.pop(0)
                break
            else:
                idents.append(s)
                msg.pop(0)
                
        return idents, msg
    
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
        ikey = int(self.key != '')
        minlen = 3 + ikey
        message = {}
        if not copy:
            for i in range(minlen):
                msg[i] = msg[i].bytes
        if ikey:
            if not self.key == msg[0]:
                raise KeyError("Invalid Session Key: %s"%msg[0])
        if not len(msg) >= minlen:
            raise TypeError("malformed message, must have at least %i elements"%minlen)
        message['header'] = self.unpack(msg[ikey+0])
        message['msg_type'] = message['header']['msg_type']
        message['parent_header'] = self.unpack(msg[ikey+1])
        if content:
            message['content'] = self.unpack(msg[ikey+2])
        else:
            message['content'] = msg[ikey+2]
        
        message['buffers'] = msg[ikey+3:]# [ m.buffer for m in msg[3:] ]
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

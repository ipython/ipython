import os
import uuid
import pprint

import zmq

from zmq.utils import jsonapi as json

class Message(object):
    """A simple message object that maps dict keys to attributes.

    A Message can be created from a dict and a dict from a Message instance
    simply by calling dict(msg_obj)."""
    
    def __init__(self, msg_dict):
        dct = self.__dict__
        for k, v in msg_dict.iteritems():
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


def msg_header(msg_id, username, session):
    return {
        'msg_id' : msg_id,
        'username' : username,
        'session' : session
    }


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


class Session(object):

    def __init__(self, username=os.environ.get('USER','username'), session=None):
        self.username = username
        if session is None:
            self.session = str(uuid.uuid4())
        else:
            self.session = session
        self.msg_id = 0

    def msg_header(self):
        h = msg_header(self.msg_id, self.username, self.session)
        self.msg_id += 1
        return h

    def msg(self, msg_type, content=None, parent=None):
        """Construct a standard-form message, with a given type, content, and parent.
        
        NOT to be called directly.
        """
        msg = {}
        msg['header'] = self.msg_header()
        msg['parent_header'] = {} if parent is None else extract_header(parent)
        msg['msg_type'] = msg_type
        msg['content'] = {} if content is None else content
        return msg

    def send(self, socket, msg_or_type, content=None, parent=None, ident=None):
        """send a message via a socket, using a uniform message pattern.
        
        Parameters
        ----------
        socket : zmq.Socket
            The socket on which to send.
        msg_or_type : Message/dict or str
            if str : then a new message will be constructed from content,parent
            if Message/dict : then content and parent are ignored, and the message
                is sent.  This is only for use when sending a Message for a second time.
        content : dict, optional
            The contents of the message
        parent : dict, optional
            The parent header, or parent message, of this message
        ident : bytes, optional
            The zmq.IDENTITY prefix of the destination.
            Only for use on certain socket types.
        
        Returns
        -------
        msg : dict
            The message, as constructed by self.msg(msg_type,content,parent)
        """
        if isinstance(msg_type, (Message, dict)):
            msg = dict(msg_type)
        else:
            msg = self.msg(msg_type, content, parent)
        if ident is not None:
            socket.send(ident, zmq.SNDMORE)
        socket.send_json(msg)
        return msg
    
    def recv(self, socket, mode=zmq.NOBLOCK):
        """recv a message on a socket.
        
        Receive an optionally identity-prefixed message, as sent via session.send().
        
        Parameters
        ----------
        
        socket : zmq.Socket
            The socket on which to recv a message.
        mode : int, optional
            the mode flag passed to socket.recv
            default: zmq.NOBLOCK
        
        Returns
        -------
        (ident,msg) : tuple
            always length 2. If no message received, then return is (None,None)
        ident : bytes or None
                the identity prefix is there was one, None otherwise.
        msg : dict or None
                The actual message.  If mode==zmq.NOBLOCK and no message was waiting,
                it will be None.
        """
        try:
            msg = socket.recv_multipart(mode)
        except zmq.ZMQError, e:
            if e.errno == zmq.EAGAIN:
                # We can convert EAGAIN to None as we know in this case
                # recv_json won't return None.
                return None,None
            else:
                raise
        if len(msg) == 1:
            ident=None
            msg = msg[0]
        elif len(msg) == 2:
            ident, msg = msg
        else:
            raise ValueError("Got message with length > 2, which is invalid")
        
        return ident, json.loads(msg)

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

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
* Evan Patterson
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
import logging
import pprint
import uuid

# System library imports
import zmq
from zmq.eventloop.ioloop import IOLoop
from zmq.eventloop.zmqstream import ZMQStream

# Local imports
from IPython.config.configurable import LoggingConfigurable
from IPython.embedded.session import BaseSession
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import Instance, Integer, Unicode
from IPython.zmq.serialize import MAX_ITEMS, MAX_BYTES

# Backwards compatability
from IPython.embedded.session import Message, msg_header, extract_header, \
    default_packer, default_unpacker

#-----------------------------------------------------------------------------
# Constants and globals
#-----------------------------------------------------------------------------

# singleton dummy tracker, which will always report as done
DONE = zmq.MessageTracker()

#-----------------------------------------------------------------------------
# Mixin tools for apps that use Sessions
#-----------------------------------------------------------------------------

session_aliases = dict(
    ident = 'Session.session',
    user = 'Session.username',
    keyfile = 'Session.keyfile',
)

session_flags  = {
    'secure' : ({'Session' : { 'key' : str_to_bytes(str(uuid.uuid4())),
                            'keyfile' : '' }},
        """Use HMAC digests for authentication of messages.
        Setting this flag will generate a new UUID to use as the HMAC key.
        """),
    'no-secure' : ({'Session' : { 'key' : b'', 'keyfile' : '' }},
        """Don't authenticate messages."""),
}

def default_secure(cfg):
    """Set the default behavior for a config environment to be secure.
    
    If Session.key/keyfile have not been set, set Session.key to
    a new random UUID.
    """
    
    if 'Session' in cfg:
        if 'key' in cfg.Session or 'keyfile' in cfg.Session:
            return
    # key/keyfile not specified, generate new UUID:
    cfg.Session.key = str_to_bytes(str(uuid.uuid4()))

#-----------------------------------------------------------------------------
# Classes and functions
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

class Session(BaseSession):
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

    # thresholds:
    copy_threshold = Integer(2**16, config=True,
        help="Threshold (in bytes) beyond which a buffer should be sent without copying.")
    buffer_threshold = Integer(MAX_BYTES, config=True,
        help="Threshold (in bytes) beyond which an object's buffer should be extracted to avoid pickling.")
    item_threshold = Integer(MAX_ITEMS, config=True,
        help="""The maximum number of items for a container to be introspected for custom serialization.
        Containers larger than this are pickled outright.
        """
    )

    def send(self, stream, msg_or_type, content=None, parent=None, ident=None,
             buffers=None, track=False, header=None, metadata=None):
        """Build and send a message via stream or socket.

        The message format used by this function internally is as follows:

        [ident1,ident2,...,DELIM,HMAC,p_header,p_parent,p_content,
         buffer1,buffer2,...]

        The serialize/unserialize methods convert the nested message dict into
        this format.

        Parameters
        ----------

        stream : zmq.Socket or ZMQStream
            The socket-like object used to send the data.
        msg_or_type : str or Message/dict
            Normally, msg_or_type will be a msg_type unless a message is being
            sent more than once. If a header is supplied, this can be set to
            None and the msg_type will be pulled from the header.

        content : dict or None
            The content of the message (ignored if msg_or_type is a message).
        header : dict or None
            The header dict for the message (ignored if msg_to_type is a 
            message).
        parent : Message or dict or None
            The parent or parent header describing the parent of this message
            (ignored if msg_or_type is a message).
        ident : bytes or list of bytes
            The zmq.IDENTITY routing path.
        metadata : dict or None
            The metadata describing the message
        buffers : list or None
            The already-serialized buffers to be appended to the message.
        track : bool
            Whether to track.  Only for use with Sockets, because ZMQStream
            objects cannot track messages.
            

        Returns
        -------
        msg : dict
            The constructed message.
        """

        if not isinstance(stream, (zmq.Socket, ZMQStream)):
            raise TypeError("stream must be Socket or ZMQStream, not %r"%type(stream))
        elif track and isinstance(stream, ZMQStream):
            raise TypeError("ZMQStream cannot track messages")

        if isinstance(msg_or_type, (Message, dict)):
            # We got a Message or message dict, not a msg_type so don't
            # build a new Message.
            msg = msg_or_type
        else:
            msg = self.msg(msg_or_type, content=content, parent=parent,
                           header=header, metadata=metadata)

        buffers = [] if buffers is None else buffers
        to_send = self.serialize(msg, ident)
        to_send.extend(buffers)
        longest = max([ len(s) for s in to_send ])
        copy = (longest < self.copy_threshold)
        
        if buffers and track and not copy:
            # only really track when we are doing zero-copy buffers
            tracker = stream.send_multipart(to_send, copy=False, track=True)
        else:
            # use dummy tracker, which will be done immediately
            tracker = DONE
            stream.send_multipart(to_send, copy=copy)

        if self.debug:
            pprint.pprint(msg)
            pprint.pprint(to_send)
            pprint.pprint(buffers)

        msg['tracker'] = tracker

        return msg

    def send_raw(self, stream, msg_list, flags=0, copy=True, ident=None):
        """Send a raw message via ident path.

        This method is used to send a already serialized message.

        Parameters
        ----------
        stream : ZMQStream or Socket
            The ZMQ stream or socket to use for sending the message.
        msg_list : list
            The serialized list of messages to send. This only includes the
            [p_header,p_parent,p_metadata,p_content,buffer1,buffer2,...] 
            portion of the message.
        ident : ident or list
            A single ident or a list of idents to use in sending.
        """
        to_send = []
        if isinstance(ident, bytes):
            ident = [ident]
        if ident is not None:
            to_send.extend(ident)

        to_send.append(DELIM)
        to_send.append(self.sign(msg_list))
        to_send.extend(msg_list)
        stream.send_multipart(msg_list, flags, copy=copy)

    def recv(self, socket, mode=zmq.NOBLOCK, content=True, copy=True):
        """Receive and unpack a message.

        Parameters
        ----------
        socket : ZMQStream or Socket
            The socket or stream to use in receiving.

        Returns
        -------
        [idents], msg
            [idents] is a list of idents and msg is a nested message dict of
            same format as self.msg returns.
        """
        if isinstance(socket, ZMQStream):
            socket = socket.socket
        try:
            msg_list = socket.recv_multipart(mode, copy=copy)
        except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
                # We can convert EAGAIN to None as we know in this case
                # recv_multipart won't return None.
                return None,None
            else:
                raise
        # split multipart message into identity list and message dict
        # invalid large messages can cause very expensive string comparisons
        idents, msg_list = self.feed_identities(msg_list, copy)
        try:
            return idents, self.unserialize(msg_list, content=content, copy=copy)
        except Exception as e:
            # TODO: handle it
            raise e


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


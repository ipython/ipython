""" Session object for building and serializing messages in IPython. The Session
object supports serialization, HMAC signatures, and metadata on messages.

Also provides a Message object for convenience that allows attribute-access to
the message dict.

Authors:

* Min RK
* Brian Granger
* Fernando Perez
* Evan Patterson
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Standard library imports
import hmac
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

# FIXME: This ZMQ import should not be here!
from zmq.utils import jsonapi

# Local imports
from IPython.config.configurable import Configurable
from IPython.utils.importstring import import_item
from IPython.utils.jsonutil import extract_dates, squash_dates, date_default
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.traitlets import CBytes, Unicode, Bool, Any, Instance, \
    Set, DottedObjectName, CUnicode, Dict

#-----------------------------------------------------------------------------
# Constants and globals
#-----------------------------------------------------------------------------

# ISO8601-ify datetime objects
json_packer = lambda obj: jsonapi.dumps(obj, default=date_default)
json_unpacker = lambda s: extract_dates(jsonapi.loads(s))

pickle_packer = lambda o: pickle.dumps(o,-1)
pickle_unpacker = pickle.loads

default_packer = json_packer
default_unpacker = json_unpacker

DELIM = b"<IDS|MSG>"

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

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


class BaseSession(Configurable):
    """ Session object for building and serializing messages in IPython.

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

    debug = Bool(False, config=True, help="""Debug output in the Session""")

    packer = DottedObjectName('json',config=True,
            help="""The name of the packer for serializing messages.
            Should be one of 'json', 'pickle', or an import name
            for a custom callable serializer.""")
    def _packer_changed(self, name, old, new):
        if new.lower() == 'json':
            self.pack = json_packer
            self.unpack = json_unpacker
            self.unpacker = new
        elif new.lower() == 'pickle':
            self.pack = pickle_packer
            self.unpack = pickle_unpacker
            self.unpacker = new
        else:
            self.pack = import_item(str(new))

    unpacker = DottedObjectName('json', config=True,
        help="""The name of the unpacker for unserializing messages.
        Only used with custom functions for `packer`.""")
    def _unpacker_changed(self, name, old, new):
        if new.lower() == 'json':
            self.pack = json_packer
            self.unpack = json_unpacker
            self.packer = new
        elif new.lower() == 'pickle':
            self.pack = pickle_packer
            self.unpack = pickle_unpacker
            self.packer = new
        else:
            self.unpack = import_item(str(new))

    session = CUnicode(u'', config=True,
        help="""The UUID identifying this session.""")
    def _session_default(self):
        u = unicode(uuid.uuid4())
        self.bsession = u.encode('ascii')
        return u

    def _session_changed(self, name, old, new):
        self.bsession = self.session.encode('ascii')

    # bsession is the session as bytes
    bsession = CBytes(b'')

    username = Unicode(os.environ.get('USER',u'username'), config=True,
        help="""Username for the Session. Default is your system username.""")

    metadata = Dict({}, config=True,
        help="""Metadata dictionary, which serves as the default top-level metadata dict for each message.""")

    # message signature related traits:
    
    key = CBytes(b'', config=True,
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

    # serialization traits:
    
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
        """ Create a BaseSession object. """
        super(BaseSession, self).__init__(**kwargs)
        self._check_packers()
        self.none = self.pack({})
        # ensure self._session_default() if necessary, so bsession is defined:
        self.session    

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

    def msg(self, msg_type, content=None, parent=None, header=None, 
            metadata=None):
        """Return the nested message dict.

        This format is different from what is sent over the wire. The
        serialize/unserialize methods converts this nested message dict to the
        wire format, which is a list of message parts.
        """
        msg = {}
        header = self.msg_header(msg_type) if header is None else header
        msg['header'] = header
        msg['msg_id'] = header['msg_id']
        msg['msg_type'] = header['msg_type']
        msg['parent_header'] = {} if parent is None else extract_header(parent)
        msg['content'] = {} if content is None else content
        msg['metadata'] = self.metadata.copy()
        if metadata is not None:
            msg['metadata'].update(metadata)
        return msg

    def sign(self, msg_list):
        """Sign a message with HMAC digest. If no auth, return b''.

        Parameters
        ----------
        msg_list : list
            The [p_header,p_parent,p_content] part of the message list.
        """
        if self.auth is None:
            return b''
        h = self.auth.copy()
        for m in msg_list:
            h.update(m)
        return str_to_bytes(h.hexdigest())

    def serialize(self, msg, ident=None):
        """Serialize the message components to bytes.

        This is roughly the inverse of unserialize. The serialize/unserialize
        methods work with full message lists, whereas pack/unpack work with
        the individual message parts in the message list.

        Parameters
        ----------
        msg : dict or Message
            The nexted message dict as returned by the self.msg method.

        Returns
        -------
        msg_list : list
            The list of bytes objects to be sent with the format:
            [ident1,ident2,...,DELIM,HMAC,p_header,p_parent,p_metadata,p_content,
             buffer1,buffer2,...]. In this list, the p_* entities are
            the packed or serialized versions, so if JSON is used, these
            are utf8 encoded JSON strings.
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
                        self.pack(msg['metadata']),
                        content,
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

    def feed_identities(self, msg_list, copy=True):
        """Split the identities from the rest of the message.

        Feed until DELIM is reached, then return the prefix as idents and
        remainder as msg_list. This is easily broken by setting an IDENT to
        DELIM, but that would be silly.

        Parameters
        ----------
        msg_list : a list of Message or bytes objects
            The message to be split.
        copy : bool
            flag determining whether the arguments are bytes or Messages

        Returns
        -------
        (idents, msg_list) : two lists
            idents will always be a list of bytes, each of which is a ZMQ
            identity. msg_list will be a list of bytes or zmq.Messages of the
            form [HMAC,p_header,p_parent,p_content,buffer1,buffer2,...] and
            should be unpackable/unserializable via self.unserialize at this
            point.
        """
        if copy:
            idx = msg_list.index(DELIM)
            return msg_list[:idx], msg_list[idx+1:]
        else:
            failed = True
            for idx,m in enumerate(msg_list):
                if m.bytes == DELIM:
                    failed = False
                    break
            if failed:
                raise ValueError("DELIM not in msg_list")
            idents, msg_list = msg_list[:idx], msg_list[idx+1:]
            return [m.bytes for m in idents], msg_list

    def unserialize(self, msg_list, content=True, copy=True):
        """Unserialize a msg_list to a nested message dict.

        This is roughly the inverse of serialize. The serialize/unserialize
        methods work with full message lists, whereas pack/unpack work with
        the individual message parts in the message list.

        Parameters:
        -----------
        msg_list : list of bytes or Message objects
            The list of message parts of the form [HMAC,p_header,p_parent,
            p_metadata,p_content,buffer1,buffer2,...].
        content : bool (True)
            Whether to unpack the content dict (True), or leave it packed
            (False).
        copy : bool (True)
            Whether to return the bytes (True), or the non-copying Message
            object in each place (False).

        Returns
        -------
        msg : dict
            The nested message dict with top-level keys [header, parent_header,
            content, buffers].
        """
        minlen = 5
        message = {}
        if not copy:
            for i in range(minlen):
                msg_list[i] = msg_list[i].bytes
        if self.auth is not None:
            signature = msg_list[0]
            if not signature:
                raise ValueError("Unsigned Message")
            if signature in self.digest_history:
                raise ValueError("Duplicate Signature: %r"%signature)
            self.digest_history.add(signature)
            check = self.sign(msg_list[1:5])
            if not signature == check:
                raise ValueError("Invalid Signature: %r" % signature)
        if not len(msg_list) >= minlen:
            raise TypeError("malformed message, must have at least %i elements"%minlen)
        header = self.unpack(msg_list[1])
        message['header'] = header
        message['msg_id'] = header['msg_id']
        message['msg_type'] = header['msg_type']
        message['parent_header'] = self.unpack(msg_list[2])
        message['metadata'] = self.unpack(msg_list[3])
        if content:
            message['content'] = self.unpack(msg_list[4])
        else:
            message['content'] = msg_list[4]

        message['buffers'] = msg_list[5:]
        return message

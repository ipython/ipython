"""test building messages with streamsession"""

#-------------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os
import uuid
import zmq

from zmq.tests import BaseZMQTestCase
from zmq.eventloop.zmqstream import ZMQStream

from IPython.zmq import session as ss

class SessionTestCase(BaseZMQTestCase):

    def setUp(self):
        BaseZMQTestCase.setUp(self)
        self.session = ss.Session()


class TestSession(SessionTestCase):

    def test_msg(self):
        """message format"""
        msg = self.session.msg('execute')
        thekeys = set('header parent_header metadata content msg_type msg_id'.split())
        s = set(msg.keys())
        self.assertEqual(s, thekeys)
        self.assertTrue(isinstance(msg['content'],dict))
        self.assertTrue(isinstance(msg['metadata'],dict))
        self.assertTrue(isinstance(msg['header'],dict))
        self.assertTrue(isinstance(msg['parent_header'],dict))
        self.assertTrue(isinstance(msg['msg_id'],str))
        self.assertTrue(isinstance(msg['msg_type'],str))
        self.assertEqual(msg['header']['msg_type'], 'execute')
        self.assertEqual(msg['msg_type'], 'execute')

    def test_serialize(self):
        msg = self.session.msg('execute', content=dict(a=10, b=1.1))
        msg_list = self.session.serialize(msg, ident=b'foo')
        ident, msg_list = self.session.feed_identities(msg_list)
        new_msg = self.session.unserialize(msg_list)
        self.assertEqual(ident[0], b'foo')
        self.assertEqual(new_msg['msg_id'],msg['msg_id'])
        self.assertEqual(new_msg['msg_type'],msg['msg_type'])
        self.assertEqual(new_msg['header'],msg['header'])
        self.assertEqual(new_msg['content'],msg['content'])
        self.assertEqual(new_msg['parent_header'],msg['parent_header'])
        self.assertEqual(new_msg['metadata'],msg['metadata'])
        # ensure floats don't come out as Decimal:
        self.assertEqual(type(new_msg['content']['b']),type(new_msg['content']['b']))

    def test_send(self):
        ctx = zmq.Context.instance()
        A = ctx.socket(zmq.PAIR)
        B = ctx.socket(zmq.PAIR)
        A.bind("inproc://test")
        B.connect("inproc://test")

        msg = self.session.msg('execute', content=dict(a=10))
        self.session.send(A, msg, ident=b'foo', buffers=[b'bar'])
        
        ident, msg_list = self.session.feed_identities(B.recv_multipart())
        new_msg = self.session.unserialize(msg_list)
        self.assertEqual(ident[0], b'foo')
        self.assertEqual(new_msg['msg_id'],msg['msg_id'])
        self.assertEqual(new_msg['msg_type'],msg['msg_type'])
        self.assertEqual(new_msg['header'],msg['header'])
        self.assertEqual(new_msg['content'],msg['content'])
        self.assertEqual(new_msg['parent_header'],msg['parent_header'])
        self.assertEqual(new_msg['metadata'],msg['metadata'])
        self.assertEqual(new_msg['buffers'],[b'bar'])

        content = msg['content']
        header = msg['header']
        parent = msg['parent_header']
        metadata = msg['metadata']
        msg_type = header['msg_type']
        self.session.send(A, None, content=content, parent=parent,
            header=header, metadata=metadata, ident=b'foo', buffers=[b'bar'])
        ident, msg_list = self.session.feed_identities(B.recv_multipart())
        new_msg = self.session.unserialize(msg_list)
        self.assertEqual(ident[0], b'foo')
        self.assertEqual(new_msg['msg_id'],msg['msg_id'])
        self.assertEqual(new_msg['msg_type'],msg['msg_type'])
        self.assertEqual(new_msg['header'],msg['header'])
        self.assertEqual(new_msg['content'],msg['content'])
        self.assertEqual(new_msg['metadata'],msg['metadata'])
        self.assertEqual(new_msg['parent_header'],msg['parent_header'])
        self.assertEqual(new_msg['buffers'],[b'bar'])

        self.session.send(A, msg, ident=b'foo', buffers=[b'bar'])
        ident, new_msg = self.session.recv(B)
        self.assertEqual(ident[0], b'foo')
        self.assertEqual(new_msg['msg_id'],msg['msg_id'])
        self.assertEqual(new_msg['msg_type'],msg['msg_type'])
        self.assertEqual(new_msg['header'],msg['header'])
        self.assertEqual(new_msg['content'],msg['content'])
        self.assertEqual(new_msg['metadata'],msg['metadata'])
        self.assertEqual(new_msg['parent_header'],msg['parent_header'])
        self.assertEqual(new_msg['buffers'],[b'bar'])

        A.close()
        B.close()
        ctx.term()

    def test_args(self):
        """initialization arguments for Session"""
        s = self.session
        self.assertTrue(s.pack is ss.default_packer)
        self.assertTrue(s.unpack is ss.default_unpacker)
        self.assertEqual(s.username, os.environ.get('USER', u'username'))

        s = ss.Session()
        self.assertEqual(s.username, os.environ.get('USER', u'username'))

        self.assertRaises(TypeError, ss.Session, pack='hi')
        self.assertRaises(TypeError, ss.Session, unpack='hi')
        u = str(uuid.uuid4())
        s = ss.Session(username=u'carrot', session=u)
        self.assertEqual(s.session, u)
        self.assertEqual(s.username, u'carrot')

    def test_tracking(self):
        """test tracking messages"""
        a,b = self.create_bound_pair(zmq.PAIR, zmq.PAIR)
        s = self.session
        s.copy_threshold = 1
        stream = ZMQStream(a)
        msg = s.send(a, 'hello', track=False)
        self.assertTrue(msg['tracker'] is ss.DONE)
        msg = s.send(a, 'hello', track=True)
        self.assertTrue(isinstance(msg['tracker'], zmq.MessageTracker))
        M = zmq.Message(b'hi there', track=True)
        msg = s.send(a, 'hello', buffers=[M], track=True)
        t = msg['tracker']
        self.assertTrue(isinstance(t, zmq.MessageTracker))
        self.assertRaises(zmq.NotDone, t.wait, .1)
        del M
        t.wait(1) # this will raise


    # def test_rekey(self):
    #     """rekeying dict around json str keys"""
    #     d = {'0': uuid.uuid4(), 0:uuid.uuid4()}
    #     self.assertRaises(KeyError, ss.rekey, d)
    #
    #     d = {'0': uuid.uuid4(), 1:uuid.uuid4(), 'asdf':uuid.uuid4()}
    #     d2 = {0:d['0'],1:d[1],'asdf':d['asdf']}
    #     rd = ss.rekey(d)
    #     self.assertEqual(d2,rd)
    #
    #     d = {'1.5':uuid.uuid4(),'1':uuid.uuid4()}
    #     d2 = {1.5:d['1.5'],1:d['1']}
    #     rd = ss.rekey(d)
    #     self.assertEqual(d2,rd)
    #
    #     d = {'1.0':uuid.uuid4(),'1':uuid.uuid4()}
    #     self.assertRaises(KeyError, ss.rekey, d)
    #
    def test_unique_msg_ids(self):
        """test that messages receive unique ids"""
        ids = set()
        for i in range(2**12):
            h = self.session.msg_header('test')
            msg_id = h['msg_id']
            self.assertTrue(msg_id not in ids)
            ids.add(msg_id)

    def test_feed_identities(self):
        """scrub the front for zmq IDENTITIES"""
        theids = "engine client other".split()
        content = dict(code='whoda',stuff=object())
        themsg = self.session.msg('execute',content=content)
        pmsg = theids

    def test_session_id(self):
        session = ss.Session()
        # get bs before us
        bs = session.bsession
        us = session.session
        self.assertEqual(us.encode('ascii'), bs)
        session = ss.Session()
        # get us before bs
        us = session.session
        bs = session.bsession
        self.assertEqual(us.encode('ascii'), bs)
        # change propagates:
        session.session = 'something else'
        bs = session.bsession
        us = session.session
        self.assertEqual(us.encode('ascii'), bs)
        session = ss.Session(session='stuff')
        # get us before bs
        self.assertEqual(session.bsession, session.session.encode('ascii'))
        self.assertEqual(b'stuff', session.bsession)



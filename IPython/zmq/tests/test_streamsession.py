
import os
import uuid
import zmq

from zmq.tests import BaseZMQTestCase

from IPython.zmq.tests import SessionTestCase
from IPython.zmq import streamsession as ss

class SessionTestCase(BaseZMQTestCase):
    
    def setUp(self):
        BaseZMQTestCase.setUp(self)
        self.session = ss.StreamSession()

class TestSession(SessionTestCase):
    
    def test_msg(self):
        """message format"""
        msg = self.session.msg('execute')
        thekeys = set('header msg_id parent_header msg_type content'.split())
        s = set(msg.keys())
        self.assertEquals(s, thekeys)
        self.assertTrue(isinstance(msg['content'],dict))
        self.assertTrue(isinstance(msg['header'],dict))
        self.assertTrue(isinstance(msg['parent_header'],dict))
        self.assertEquals(msg['msg_type'], 'execute')
        
            
    
    def test_args(self):
        """initialization arguments for StreamSession"""
        s = ss.StreamSession()
        self.assertTrue(s.pack is ss.default_packer)
        self.assertTrue(s.unpack is ss.default_unpacker)
        self.assertEquals(s.username, os.environ.get('USER', 'username'))
        
        s = ss.StreamSession(username=None)
        self.assertEquals(s.username, os.environ.get('USER', 'username'))
        
        self.assertRaises(TypeError, ss.StreamSession, packer='hi')
        self.assertRaises(TypeError, ss.StreamSession, unpacker='hi')
        u = str(uuid.uuid4())
        s = ss.StreamSession(username='carrot', session=u)
        self.assertEquals(s.session, u)
        self.assertEquals(s.username, 'carrot')
        
    
    def test_rekey(self):
        """rekeying dict around json str keys"""
        d = {'0': uuid.uuid4(), 0:uuid.uuid4()}
        self.assertRaises(KeyError, ss.rekey, d)
        
        d = {'0': uuid.uuid4(), 1:uuid.uuid4(), 'asdf':uuid.uuid4()}
        d2 = {0:d['0'],1:d[1],'asdf':d['asdf']}
        rd = ss.rekey(d)
        self.assertEquals(d2,rd)
        
        d = {'1.5':uuid.uuid4(),'1':uuid.uuid4()}
        d2 = {1.5:d['1.5'],1:d['1']}
        rd = ss.rekey(d)
        self.assertEquals(d2,rd)
        
        d = {'1.0':uuid.uuid4(),'1':uuid.uuid4()}
        self.assertRaises(KeyError, ss.rekey, d)
    
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

"""Tests for the session manager."""

from unittest import TestCase

from tornado import web

from ..sessionmanager import SessionManager

class TestSessionManager(TestCase):
    
    def test_get_session(self):
        sm = SessionManager()
        session_id = sm.new_session_id()
        sm.save_session(session_id=session_id, name='test.ipynb', path='/path/to/', kernel_id='5678')
        model = sm.get_session(session_id=session_id)
        expected = {'id':session_id, 'notebook':{'name':u'test.ipynb', 'path': u'/path/to/'}, 'kernel':{'id':u'5678'}}
        self.assertEqual(model, expected)

    def test_bad_get_session(self):
        # Should raise error if a bad key is passed to the database.
        sm = SessionManager()
        session_id = sm.new_session_id()
        sm.save_session(session_id=session_id, name='test.ipynb', path='/path/to/', kernel_id='5678')
        self.assertRaises(TypeError, sm.get_session, bad_id=session_id) # Bad keyword

    def test_list_sessions(self):
        sm = SessionManager()
        session_id1 = sm.new_session_id()
        session_id2 = sm.new_session_id()
        session_id3 = sm.new_session_id()
        sm.save_session(session_id=session_id1, name='test1.ipynb', path='/path/to/1/', kernel_id='5678')
        sm.save_session(session_id=session_id2, name='test2.ipynb', path='/path/to/2/', kernel_id='5678')
        sm.save_session(session_id=session_id3, name='test3.ipynb', path='/path/to/3/', kernel_id='5678')
        sessions = sm.list_sessions()
        expected = [{'id':session_id1, 'notebook':{'name':u'test1.ipynb', 
                    'path': u'/path/to/1/'}, 'kernel':{'id':u'5678'}},
                    {'id':session_id2, 'notebook': {'name':u'test2.ipynb', 
                    'path': u'/path/to/2/'}, 'kernel':{'id':u'5678'}},
                    {'id':session_id3, 'notebook':{'name':u'test3.ipynb', 
                    'path': u'/path/to/3/'}, 'kernel':{'id':u'5678'}}]
        self.assertEqual(sessions, expected)

    def test_update_session(self):
        sm = SessionManager()
        session_id = sm.new_session_id()
        sm.save_session(session_id=session_id, name='test.ipynb', path='/path/to/', kernel_id=None)
        sm.update_session(session_id, kernel_id='5678')
        sm.update_session(session_id, name='new_name.ipynb')
        model = sm.get_session(session_id=session_id)
        expected = {'id':session_id, 'notebook':{'name':u'new_name.ipynb', 'path': u'/path/to/'}, 'kernel':{'id':u'5678'}}
        self.assertEqual(model, expected)
    
    def test_bad_update_session(self):
        # try to update a session with a bad keyword ~ raise error
        sm = SessionManager()
        session_id = sm.new_session_id()
        sm.save_session(session_id=session_id, name='test.ipynb', path='/path/to/', kernel_id='5678')
        self.assertRaises(TypeError, sm.update_session, session_id=session_id, bad_kw='test.ipynb') # Bad keyword

    def test_delete_session(self):
        sm = SessionManager()
        session_id1 = sm.new_session_id()
        session_id2 = sm.new_session_id()
        session_id3 = sm.new_session_id()
        sm.save_session(session_id=session_id1, name='test1.ipynb', path='/path/to/1/', kernel_id='5678')
        sm.save_session(session_id=session_id2, name='test2.ipynb', path='/path/to/2/', kernel_id='5678')
        sm.save_session(session_id=session_id3, name='test3.ipynb', path='/path/to/3/', kernel_id='5678')
        sm.delete_session(session_id2)
        sessions = sm.list_sessions()
        expected = [{'id':session_id1, 'notebook':{'name':u'test1.ipynb', 
                    'path': u'/path/to/1/'}, 'kernel':{'id':u'5678'}},
                    {'id':session_id3, 'notebook':{'name':u'test3.ipynb', 
                    'path': u'/path/to/3/'}, 'kernel':{'id':u'5678'}}]
        self.assertEqual(sessions, expected)

    def test_bad_delete_session(self):
        # try to delete a session that doesn't exist ~ raise error
        sm = SessionManager()
        session_id = sm.new_session_id()
        sm.save_session(session_id=session_id, name='test.ipynb', path='/path/to/', kernel_id='5678')
        self.assertRaises(TypeError, sm.delete_session, bad_kwarg='23424') # Bad keyword
        self.assertRaises(web.HTTPError, sm.delete_session, session_id='23424') # nonexistant


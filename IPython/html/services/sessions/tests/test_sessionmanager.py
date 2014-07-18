"""Tests for the session manager."""

from unittest import TestCase

from tornado import web

from ..sessionmanager import SessionManager
from IPython.html.services.kernels.kernelmanager import MappingKernelManager

class DummyKernel(object):
    def __init__(self, kernel_name='python'):
        self.kernel_name = kernel_name

class DummyMKM(MappingKernelManager):
    """MappingKernelManager interface that doesn't start kernels, for testing"""
    def __init__(self, *args, **kwargs):
        super(DummyMKM, self).__init__(*args, **kwargs)
        self.id_letters = iter(u'ABCDEFGHIJK')

    def _new_id(self):
        return next(self.id_letters)
    
    def start_kernel(self, kernel_id=None, path=None, kernel_name='python', **kwargs):
        kernel_id = kernel_id or self._new_id()
        self._kernels[kernel_id] = DummyKernel(kernel_name=kernel_name)
        return kernel_id

    def shutdown_kernel(self, kernel_id, now=False):
        del self._kernels[kernel_id]

class TestSessionManager(TestCase):
    
    def test_get_session(self):
        sm = SessionManager(kernel_manager=DummyMKM())
        session_id = sm.create_session(name='test.ipynb', path='/path/to/',
                                       kernel_name='bar')['id']
        model = sm.get_session(session_id=session_id)
        expected = {'id':session_id,
                    'notebook':{'name':u'test.ipynb', 'path': u'/path/to/'},
                    'kernel': {'id':u'A', 'name': 'bar'}}
        self.assertEqual(model, expected)

    def test_bad_get_session(self):
        # Should raise error if a bad key is passed to the database.
        sm = SessionManager(kernel_manager=DummyMKM())
        session_id = sm.create_session(name='test.ipynb', path='/path/to/',
                                       kernel_name='foo')['id']
        self.assertRaises(TypeError, sm.get_session, bad_id=session_id) # Bad keyword

    def test_list_sessions(self):
        sm = SessionManager(kernel_manager=DummyMKM())
        sessions = [
            sm.create_session(name='test1.ipynb', path='/path/to/1/', kernel_name='python'),
            sm.create_session(name='test2.ipynb', path='/path/to/2/', kernel_name='python'),
            sm.create_session(name='test3.ipynb', path='/path/to/3/', kernel_name='python'),
        ]
        sessions = sm.list_sessions()
        expected = [{'id':sessions[0]['id'], 'notebook':{'name':u'test1.ipynb', 
                    'path': u'/path/to/1/'}, 'kernel':{'id':u'A', 'name':'python'}},
                    {'id':sessions[1]['id'], 'notebook': {'name':u'test2.ipynb', 
                    'path': u'/path/to/2/'}, 'kernel':{'id':u'B', 'name':'python'}},
                    {'id':sessions[2]['id'], 'notebook':{'name':u'test3.ipynb', 
                    'path': u'/path/to/3/'}, 'kernel':{'id':u'C', 'name':'python'}}]
        self.assertEqual(sessions, expected)

    def test_update_session(self):
        sm = SessionManager(kernel_manager=DummyMKM())
        session_id = sm.create_session(name='test.ipynb', path='/path/to/',
                                       kernel_name='julia')['id']
        sm.update_session(session_id, name='new_name.ipynb')
        model = sm.get_session(session_id=session_id)
        expected = {'id':session_id,
                    'notebook':{'name':u'new_name.ipynb', 'path': u'/path/to/'},
                    'kernel':{'id':u'A', 'name':'julia'}}
        self.assertEqual(model, expected)
    
    def test_bad_update_session(self):
        # try to update a session with a bad keyword ~ raise error
        sm = SessionManager(kernel_manager=DummyMKM())
        session_id = sm.create_session(name='test.ipynb', path='/path/to/',
                                       kernel_name='ir')['id']
        self.assertRaises(TypeError, sm.update_session, session_id=session_id, bad_kw='test.ipynb') # Bad keyword

    def test_delete_session(self):
        sm = SessionManager(kernel_manager=DummyMKM())
        sessions = [
            sm.create_session(name='test1.ipynb', path='/path/to/1/', kernel_name='python'),
            sm.create_session(name='test2.ipynb', path='/path/to/2/', kernel_name='python'),
            sm.create_session(name='test3.ipynb', path='/path/to/3/', kernel_name='python'),
        ]
        sm.delete_session(sessions[1]['id'])
        new_sessions = sm.list_sessions()
        expected = [{'id':sessions[0]['id'], 'notebook':{'name':u'test1.ipynb', 
                    'path': u'/path/to/1/'}, 'kernel':{'id':u'A', 'name':'python'}},
                    {'id':sessions[2]['id'], 'notebook':{'name':u'test3.ipynb', 
                    'path': u'/path/to/3/'}, 'kernel':{'id':u'C', 'name':'python'}}]
        self.assertEqual(new_sessions, expected)

    def test_bad_delete_session(self):
        # try to delete a session that doesn't exist ~ raise error
        sm = SessionManager(kernel_manager=DummyMKM())
        sm.create_session(name='test.ipynb', path='/path/to/', kernel_name='python')
        self.assertRaises(TypeError, sm.delete_session, bad_kwarg='23424') # Bad keyword
        self.assertRaises(web.HTTPError, sm.delete_session, session_id='23424') # nonexistant


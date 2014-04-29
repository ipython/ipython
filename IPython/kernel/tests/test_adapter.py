"""Tests for adapting IPython msg spec versions"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import copy

from unittest import TestCase
import nose.tools as nt

from IPython.kernel.adapter import adapt, V4toV5, V5toV4
from IPython.kernel.zmq.session import Session


def test_default_version():
    s = Session()
    msg = s.msg("msg_type")
    msg['header'].pop('version')
    original = copy.deepcopy(msg)
    adapted = adapt(original)
    nt.assert_equal(adapted['header'].version, V4toV5.version)


class AdapterTest(TestCase):
    
    def setUp(self):
        print("hi")
        self.session = Session()
    
    def adapt(self, msg, version=None):
        original = copy.deepcopy(msg)
        adapted = adapt(msg, version or self.to_version)
        return original, adapted
    
    def check_header(self, msg):
        pass


class V4toV5TestCase(AdapterTest):
    from_version = 4
    to_version = 5
    
    def msg(self, msg_type, content):
        """Create a v4 msg (same as v5, minus version header)"""
        msg = self.session.msg(msg_type, content)
        msg['header'].pop('version')
        return msg
    
    def test_same_version(self):
        msg = self.msg("execute_result",
            content={'status' : 'ok'}
        )
        original, adapted = self.adapt(msg, self.from_version)
    
        self.assertEqual(original, adapted)
    
    def test_no_adapt(self):
        msg = self.msg("input_reply", {'value' : 'some text'})
        v4, v5 = self.adapt(msg)
        self.assertEqual(v5['header']['version'], V4toV5.version)
        v5['header'].pop('version')
        self.assertEqual(v4, v5)
    
    def test_rename_type(self):
        for v5_type, v4_type in [
                ('execute_result', 'pyout'),
                ('execute_input', 'pyin'),
                ('error', 'pyerr'),
            ]:
            msg = self.msg(v4_type, {'key' : 'value'})
            v4, v5 = self.adapt(msg)
            self.assertEqual(v5['header']['version'], V4toV5.version)
            self.assertEqual(v5['header']['msg_type'], v5_type)
            self.assertEqual(v4['content'], v5['content'])
    
    def test_execute_request(self):
        msg = self.msg("execute_request", {
            'code' : 'a=5',
            'silent' : False,
            'user_expressions' : {'a' : 'apple'},
            'user_variables' : ['b'],
        })
        v4, v5 = self.adapt(msg)
        self.assertEqual(v4['header']['msg_type'], v5['header']['msg_type'])
        v4c = v4['content']
        v5c = v5['content']
        self.assertEqual(v5c['user_expressions'], {'a' : 'apple', 'b': 'b'})
        nt.assert_not_in('user_variables', v5c)
        self.assertEqual(v5c['code'], v4c['code'])
    
    def test_complete_request(self):
        pass
    
    def test_complete_reply(self):
        pass
    
    def test_object_info_request(self):
        pass
    
    def test_object_info_reply(self):
        pass
    
    # iopub channel
    
    def test_display_data(self):
        pass
    
    # stdin channel
    
    def test_input_request(self):
        msg = self.msg('input_request', {'prompt': "$>"})
        v4, v5 = self.adapt(msg)
        self.assertEqual(v5['content']['prompt'], v4['content']['prompt'])
        self.assertFalse(v5['content']['password'])


class V5toV4TestCase(AdapterTest):
    from_version = 5
    to_version = 4
    
    def msg(self, msg_type, content):
        return self.session.msg(msg_type, content)
    
    def test_same_version(self):
        msg = self.msg("execute_result",
            content={'status' : 'ok'}
        )
        original, adapted = self.adapt(msg, self.from_version)
    
        self.assertEqual(original, adapted)
    
    def test_no_adapt(self):
        msg = self.msg("input_reply", {'value' : 'some text'})
        v5, v4 = self.adapt(msg)
        self.assertNotIn('version', v4['header'])
        v5['header'].pop('version')
        self.assertEqual(v4, v5)
    
    def test_rename_type(self):
        for v5_type, v4_type in [
                ('execute_result', 'pyout'),
                ('execute_input', 'pyin'),
                ('error', 'pyerr'),
            ]:
            msg = self.msg(v5_type, {'key' : 'value'})
            v5, v4 = self.adapt(msg)
            self.assertEqual(v4['header']['msg_type'], v4_type)
            nt.assert_not_in('version', v4['header'])
            self.assertEqual(v4['content'], v5['content'])
    
    def test_execute_request(self):
        msg = self.msg("execute_request", {
            'code' : 'a=5',
            'silent' : False,
            'user_expressions' : {'a' : 'apple'},
        })
        v5, v4 = self.adapt(msg)
        self.assertEqual(v4['header']['msg_type'], v5['header']['msg_type'])
        v4c = v4['content']
        v5c = v5['content']
        self.assertEqual(v4c['user_variables'], [])
        self.assertEqual(v5c['code'], v4c['code'])
    
    def test_complete_request(self):
        pass
    
    def test_complete_reply(self):
        pass
    
    def test_inspect_request(self):
        pass
    
    def test_inspect_reply(self):
        pass
    
    # iopub channel
    
    def test_display_data(self):
        pass
    
    # stdin channel
    
    def test_input_request(self):
        msg = self.msg('input_request', {'prompt': "$>", 'password' : True})
        v5, v4 = self.adapt(msg)
        self.assertEqual(v5['content']['prompt'], v4['content']['prompt'])
        self.assertNotIn('password', v4['content'])
    


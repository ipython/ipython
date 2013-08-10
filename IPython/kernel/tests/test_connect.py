"""Tests for kernel connection utilities

Authors
-------
* MinRK
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import json
import os

import nose.tools as nt

from IPython.config import Config
from IPython.consoleapp import IPythonConsoleApp
from IPython.core.application import BaseIPythonApplication
from IPython.utils.tempdir import TemporaryDirectory, TemporaryWorkingDirectory
from IPython.utils.py3compat import str_to_bytes
from IPython.kernel import connect

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class DummyConsoleApp(BaseIPythonApplication, IPythonConsoleApp):
    def initialize(self, argv=[]):
        BaseIPythonApplication.initialize(self, argv=argv)
        self.init_connection_file()

sample_info = dict(ip='1.2.3.4', transport='ipc',
        shell_port=1, hb_port=2, iopub_port=3, stdin_port=4, control_port=5,
        key=b'abc123', signature_scheme='hmac-md5',
    )

def test_write_connection_file():
    with TemporaryDirectory() as d:
        cf = os.path.join(d, 'kernel.json')
        connect.write_connection_file(cf, **sample_info)
        nt.assert_true(os.path.exists(cf))
        with open(cf, 'r') as f:
            info = json.load(f)
    info['key'] = str_to_bytes(info['key'])
    nt.assert_equal(info, sample_info)

def test_app_load_connection_file():
    """test `ipython console --existing` loads a connection file"""
    with TemporaryDirectory() as d:
        cf = os.path.join(d, 'kernel.json')
        connect.write_connection_file(cf, **sample_info)
        app = DummyConsoleApp(connection_file=cf)
        app.initialize(argv=[])
    
    for attr, expected in sample_info.items():
        if attr in ('key', 'signature_scheme'):
            continue
        value = getattr(app, attr)
        nt.assert_equal(value, expected, "app.%s = %s != %s" % (attr, value, expected))

def test_get_connection_file():
    cfg = Config()
    with TemporaryWorkingDirectory() as d:
        cfg.ProfileDir.location = d
        cf = 'kernel.json'
        app = DummyConsoleApp(config=cfg, connection_file=cf)
        app.initialize(argv=[])
        
        profile_cf = os.path.join(app.profile_dir.location, 'security', cf)
        nt.assert_equal(profile_cf, app.connection_file)
        with open(profile_cf, 'w') as f:
            f.write("{}")
        nt.assert_true(os.path.exists(profile_cf))
        nt.assert_equal(connect.get_connection_file(app), profile_cf)
        
        app.connection_file = cf
        nt.assert_equal(connect.get_connection_file(app), profile_cf)

def test_find_connection_file():
    cfg = Config()
    with TemporaryDirectory() as d:
        cfg.ProfileDir.location = d
        cf = 'kernel.json'
        app = DummyConsoleApp(config=cfg, connection_file=cf)
        app.initialize(argv=[])
        BaseIPythonApplication._instance = app
        
        profile_cf = os.path.join(app.profile_dir.location, 'security', cf)
        with open(profile_cf, 'w') as f:
            f.write("{}")
        
        for query in (
            'kernel.json',
            'kern*',
            '*ernel*',
            'k*',
            ):
            nt.assert_equal(connect.find_connection_file(query), profile_cf)
        
        BaseIPythonApplication._instance = None

def test_get_connection_info():
    with TemporaryDirectory() as d:
        cf = os.path.join(d, 'kernel.json')
        connect.write_connection_file(cf, **sample_info)
        json_info = connect.get_connection_info(cf)
        info = connect.get_connection_info(cf, unpack=True)
    
    nt.assert_equal(type(json_info), type(""))
    nt.assert_equal(info, sample_info)
    
    info2 = json.loads(json_info)
    info2['key'] = str_to_bytes(info2['key'])
    nt.assert_equal(info2, sample_info)
    


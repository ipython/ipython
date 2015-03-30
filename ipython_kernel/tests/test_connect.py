"""Tests for kernel connection utilities"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os

import nose.tools as nt

from IPython.config import Config
from IPython.utils.tempdir import TemporaryDirectory, TemporaryWorkingDirectory
from IPython.utils.py3compat import str_to_bytes
from ipython_kernel import connect
from ipython_kernel.kernelapp import IPKernelApp


sample_info = dict(ip='1.2.3.4', transport='ipc',
        shell_port=1, hb_port=2, iopub_port=3, stdin_port=4, control_port=5,
        key=b'abc123', signature_scheme='hmac-md5',
    )


class DummyKernelApp(IPKernelApp):
    def initialize(self, argv=[]):
        self.init_profile_dir()
        self.init_connection_file()


def test_get_connection_file():
    cfg = Config()
    with TemporaryWorkingDirectory() as d:
        cfg.ProfileDir.location = d
        cf = 'kernel.json'
        app = DummyKernelApp(config=cfg, connection_file=cf)
        app.initialize()

        profile_cf = os.path.join(app.profile_dir.location, 'security', cf)
        nt.assert_equal(profile_cf, app.abs_connection_file)
        with open(profile_cf, 'w') as f:
            f.write("{}")
        nt.assert_true(os.path.exists(profile_cf))
        nt.assert_equal(connect.get_connection_file(app), profile_cf)

        app.connection_file = cf
        nt.assert_equal(connect.get_connection_file(app), profile_cf)


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

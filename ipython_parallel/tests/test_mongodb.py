"""Tests for mongodb backend

Authors:

* Min RK
"""

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

from unittest import TestCase

from nose import SkipTest

from pymongo import Connection
from IPython.parallel.controller.mongodb import MongoDB

from . import test_db

conn_kwargs = {}
if 'DB_IP' in os.environ:
    conn_kwargs['host'] = os.environ['DB_IP']
if 'DBA_MONGODB_ADMIN_URI' in os.environ:
    # On ShiningPanda, we need a username and password to connect. They are
    # passed in a mongodb:// URI.
    conn_kwargs['host'] = os.environ['DBA_MONGODB_ADMIN_URI']
if 'DB_PORT' in os.environ:
    conn_kwargs['port'] = int(os.environ['DB_PORT'])

try:
    c = Connection(**conn_kwargs)
except Exception:
    c=None

class TestMongoBackend(test_db.TaskDBTest, TestCase):
    """MongoDB backend tests"""

    def create_db(self):
        try:
            return MongoDB(database='iptestdb', _connection=c)
        except Exception:
            raise SkipTest("Couldn't connect to mongodb")

def teardown(self):
    if c is not None:
        c.drop_database('iptestdb')

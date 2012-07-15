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

from nose import SkipTest

from pymongo import Connection
from IPython.parallel.controller.mongodb import MongoDB

from . import test_db

try:
    c = Connection()
except Exception:
    c=None

class TestMongoBackend(test_db.TestDictBackend):
    """MongoDB backend tests"""

    def create_db(self):
        try:
            return MongoDB(database='iptestdb', _connection=c)
        except Exception:
            raise SkipTest("Couldn't connect to mongodb")

def teardown(self):
    if c is not None:
        c.drop_database('iptestdb')

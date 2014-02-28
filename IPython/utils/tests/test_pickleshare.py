from __future__ import print_function

import os
from unittest import TestCase

from IPython.testing.decorators import skip
from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.pickleshare import PickleShareDB


class PickleShareDBTestCase(TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
    
    def tearDown(self):
        self.tempdir.cleanup()

    def test_picklesharedb(self):
        db = PickleShareDB(self.tempdir.name)
        db.clear()
        print("Should be empty:",db.items())
        db['hello'] = 15
        db['aku ankka'] = [1,2,313]
        db['paths/nest/ok/keyname'] = [1,(5,46)]
        db.hset('hash', 'aku', 12)
        db.hset('hash', 'ankka', 313)
        self.assertEqual(db.hget('hash','aku'), 12)
        self.assertEqual(db.hget('hash','ankka'), 313)
        print("all hashed",db.hdict('hash'))
        print(db.keys())
        print(db.keys('paths/nest/ok/k*'))
        print(dict(db)) # snapsot of whole db
        db.uncache() # frees memory, causes re-reads later
    
        # shorthand for accessing deeply nested files
        lnk = db.getlink('myobjects/test')
        lnk.foo = 2
        lnk.bar = lnk.foo + 5
        self.assertEqual(lnk.bar, 7)

    @skip("Too slow for regular running.")
    def test_stress(self):
        db = PickleShareDB('~/fsdbtest')
        import time,sys
        for i in range(1000):
            for j in range(1000):
                if i % 15 == 0 and i < 200:
                    if str(j) in db:
                        del db[str(j)]
                    continue
    
                if j%33 == 0:
                    time.sleep(0.02)
    
                db[str(j)] = db.get(str(j), []) + [(i,j,"proc %d" % os.getpid())]
                db.hset('hash',j, db.hget('hash',j,15) + 1 )
    
            print(i, end=' ')
            sys.stdout.flush()
            if i % 10 == 0:
                db.uncache()
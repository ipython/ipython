#!/usr/bin/env python

""" PickleShare - a small 'shelve' like datastore with concurrency support

Like shelve, a PickleShareDB object acts like a normal dictionary. Unlike
shelve, many processes can access the database simultaneously. Changing a
value in database is immediately visible to other processes accessing the
same database.

Concurrency is possible because the values are stored in separate files. Hence
the "database" is a directory where *all* files are governed by PickleShare.

Example usage::

    from pickleshare import *
    db = PickleShareDB('~/testpickleshare')
    db.clear()
    print "Should be empty:",db.items()
    db['hello'] = 15
    db['aku ankka'] = [1,2,313]
    db['paths/are/ok/key'] = [1,(5,46)]
    print db.keys()
    del db['aku ankka']

This module is certainly not ZODB, but can be used for low-load
(non-mission-critical) situations where tiny code size trumps the
advanced features of a "real" object database.

Installation guide: easy_install pickleshare

Author: Ville Vainio <vivainio@gmail.com>
License: MIT open source license.

"""

from IPython.external.path import path as Path
import os,stat,time
import collections
import cPickle as pickle
import glob

def gethashfile(key):
    return ("%02x" % abs(hash(key) % 256))[-2:]

_sentinel = object()

class PickleShareDB(collections.MutableMapping):
    """ The main 'connection' object for PickleShare database """
    def __init__(self,root):
        """ Return a db object that will manage the specied directory"""
        self.root = Path(root).expanduser().abspath()
        if not self.root.isdir():
            self.root.makedirs()
        # cache has { 'key' : (obj, orig_mod_time) }
        self.cache = {}


    def __getitem__(self,key):
        """ db['key'] reading """
        fil = self.root / key
        try:
            mtime = (fil.stat()[stat.ST_MTIME])
        except OSError:
            raise KeyError(key)

        if fil in self.cache and mtime == self.cache[fil][1]:
            return self.cache[fil][0]
        try:
            # The cached item has expired, need to read
            with fil.open("rb") as f:
                obj = pickle.loads(f.read())
        except:
            raise KeyError(key)

        self.cache[fil] = (obj,mtime)
        return obj

    def __setitem__(self,key,value):
        """ db['key'] = 5 """
        fil = self.root / key
        parent = fil.parent
        if parent and not parent.isdir():
            parent.makedirs()
        # We specify protocol 2, so that we can mostly go between Python 2
        # and Python 3. We can upgrade to protocol 3 when Python 2 is obsolete.
        with fil.open('wb') as f:
            pickled = pickle.dump(value, f, protocol=2)
        try:
            self.cache[fil] = (value,fil.mtime)
        except OSError as e:
            if e.errno != 2:
                raise

    def hset(self, hashroot, key, value):
        """ hashed set """
        hroot = self.root / hashroot
        if not hroot.isdir():
            hroot.makedirs()
        hfile = hroot / gethashfile(key)
        d = self.get(hfile, {})
        d.update( {key : value})
        self[hfile] = d



    def hget(self, hashroot, key, default = _sentinel, fast_only = True):
        """ hashed get """
        hroot = self.root / hashroot
        hfile = hroot / gethashfile(key)

        d = self.get(hfile, _sentinel )
        #print "got dict",d,"from",hfile
        if d is _sentinel:
            if fast_only:
                if default is _sentinel:
                    raise KeyError(key)

                return default

            # slow mode ok, works even after hcompress()
            d = self.hdict(hashroot)

        return d.get(key, default)

    def hdict(self, hashroot):
        """ Get all data contained in hashed category 'hashroot' as dict """
        hfiles = self.keys(hashroot + "/*")
        hfiles.sort()
        last = len(hfiles) and hfiles[-1] or ''
        if last.endswith('xx'):
            # print "using xx"
            hfiles = [last] + hfiles[:-1]

        all = {}

        for f in hfiles:
            # print "using",f
            try:
                all.update(self[f])
            except KeyError:
                print "Corrupt",f,"deleted - hset is not threadsafe!"
                del self[f]

            self.uncache(f)

        return all

    def hcompress(self, hashroot):
        """ Compress category 'hashroot', so hset is fast again

        hget will fail if fast_only is True for compressed items (that were
        hset before hcompress).

        """
        hfiles = self.keys(hashroot + "/*")
        all = {}
        for f in hfiles:
            # print "using",f
            all.update(self[f])
            self.uncache(f)

        self[hashroot + '/xx'] = all
        for f in hfiles:
            p = self.root / f
            if p.basename() == 'xx':
                continue
            p.remove()



    def __delitem__(self,key):
        """ del db["key"] """
        fil = self.root / key
        self.cache.pop(fil,None)
        try:
            fil.remove()
        except OSError:
            # notfound and permission denied are ok - we
            # lost, the other process wins the conflict
            pass

    def _normalized(self, p):
        """ Make a key suitable for user's eyes """
        return str(self.root.relpathto(p)).replace('\\','/')

    def keys(self, globpat = None):
        """ All keys in DB, or all keys matching a glob"""

        if globpat is None:
            files = self.root.walkfiles()
        else:
            files = [Path(p) for p in glob.glob(self.root/globpat)]
        return [self._normalized(p) for p in files if p.isfile()]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def uncache(self,*items):
        """ Removes all, or specified items from cache

        Use this after reading a large amount of large objects
        to free up memory, when you won't be needing the objects
        for a while.

        """
        if not items:
            self.cache = {}
        for it in items:
            self.cache.pop(it,None)

    def waitget(self,key, maxwaittime = 60 ):
        """ Wait (poll) for a key to get a value

        Will wait for `maxwaittime` seconds before raising a KeyError.
        The call exits normally if the `key` field in db gets a value
        within the timeout period.

        Use this for synchronizing different processes or for ensuring
        that an unfortunately timed "db['key'] = newvalue" operation
        in another process (which causes all 'get' operation to cause a
        KeyError for the duration of pickling) won't screw up your program
        logic.
        """

        wtimes = [0.2] * 3 + [0.5] * 2 + [1]
        tries = 0
        waited = 0
        while 1:
            try:
                val = self[key]
                return val
            except KeyError:
                pass

            if waited > maxwaittime:
                raise KeyError(key)

            time.sleep(wtimes[tries])
            waited+=wtimes[tries]
            if tries < len(wtimes) -1:
                tries+=1

    def getlink(self,folder):
        """ Get a convenient link for accessing items  """
        return PickleShareLink(self, folder)

    def __repr__(self):
        return "PickleShareDB('%s')" % self.root



class PickleShareLink:
    """ A shortdand for accessing nested PickleShare data conveniently.

    Created through PickleShareDB.getlink(), example::

        lnk = db.getlink('myobjects/test')
        lnk.foo = 2
        lnk.bar = lnk.foo + 5

    """
    def __init__(self, db, keydir ):
        self.__dict__.update(locals())

    def __getattr__(self,key):
        return self.__dict__['db'][self.__dict__['keydir']+'/' + key]
    def __setattr__(self,key,val):
        self.db[self.keydir+'/' + key] = val
    def __repr__(self):
        db = self.__dict__['db']
        keys = db.keys( self.__dict__['keydir'] +"/*")
        return "<PickleShareLink '%s': %s>" % (
            self.__dict__['keydir'],
            ";".join([Path(k).basename() for k in keys]))


def test():
    db = PickleShareDB('~/testpickleshare')
    db.clear()
    print "Should be empty:",db.items()
    db['hello'] = 15
    db['aku ankka'] = [1,2,313]
    db['paths/nest/ok/keyname'] = [1,(5,46)]
    db.hset('hash', 'aku', 12)
    db.hset('hash', 'ankka', 313)
    print "12 =",db.hget('hash','aku')
    print "313 =",db.hget('hash','ankka')
    print "all hashed",db.hdict('hash')
    print db.keys()
    print db.keys('paths/nest/ok/k*')
    print dict(db) # snapsot of whole db
    db.uncache() # frees memory, causes re-reads later

    # shorthand for accessing deeply nested files
    lnk = db.getlink('myobjects/test')
    lnk.foo = 2
    lnk.bar = lnk.foo + 5
    print lnk.bar # 7

def stress():
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

        print i,
        sys.stdout.flush()
        if i % 10 == 0:
            db.uncache()

def main():
    import textwrap
    usage = textwrap.dedent("""\
    pickleshare - manage PickleShare databases

    Usage:

        pickleshare dump /path/to/db > dump.txt
        pickleshare load /path/to/db < dump.txt
        pickleshare test /path/to/db
    """)
    DB = PickleShareDB
    import sys
    if len(sys.argv) < 2:
        print usage
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == 'dump':
        if not args: args= ['.']
        db = DB(args[0])
        import pprint
        pprint.pprint(db.items())
    elif cmd == 'load':
        cont = sys.stdin.read()
        db = DB(args[0])
        data = eval(cont)
        db.clear()
        for k,v in db.items():
            db[k] = v
    elif cmd == 'testwait':
        db = DB(args[0])
        db.clear()
        print db.waitget('250')
    elif cmd == 'test':
        test()
        stress()

if __name__== "__main__":
    main()



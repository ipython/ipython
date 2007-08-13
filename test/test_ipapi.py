import IPython.ipapi

IPython.ipapi.make_session()
ip = IPython.ipapi.get()

def test_runlines():
    ip.runlines(['a = 10', 'a+=1'])
    ip.runlines('assert a == 11')
    assert ip.user_ns['a'] == 11

def test_db():
    ip.db['__unittest_'] = 12
    assert ip.db['__unittest_'] == 12
    del ip.db['__unittest_']
    assert '__unittest_' not in ip.db

def test_defalias():
    slot = [None]
    # test callable alias
    def cb(s):
        slot[0] = s
    
    ip.defalias('testalias', cb)
    ip.runlines('testalias foo bar')
    assert slot[0] == 'testalias foo bar'
        

test_runlines()
test_db()
test_defalias

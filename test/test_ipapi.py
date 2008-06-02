import sys
sys.path.append('..')

import IPython.ipapi
IPython.ipapi.make_session()
ip = IPython.ipapi.get()

def test_runlines():
    import textwrap
    ip.runlines(['a = 10', 'a+=1'])
    ip.runlines('assert a == 11\nassert 1')

    assert ip.user_ns['a'] == 11
    complex = textwrap.dedent("""\
    if 1:
        print "hello"
        if 1:
            print "world"
        
    if 1:
        print "foo"
    if 1:
        print "bar"

    if 1:
        print "bar"
    
    """)

    
    ip.runlines(complex)
    

def test_db():
    ip.db['__unittest_'] = 12
    assert ip.db['__unittest_'] == 12
    del ip.db['__unittest_']
    assert '__unittest_' not in ip.db

def test_defalias():
    slot = [None]
    # test callable alias
    def cb(localip,s):
        assert localip is ip
        slot[0] = s
    
    ip.defalias('testalias', cb)
    ip.runlines('testalias foo bar')
    assert slot[0] == 'testalias foo bar'
        

test_runlines()
test_db()
test_defalias

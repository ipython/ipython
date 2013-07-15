import tempfile, os

import nose.tools as nt

ip = get_ipython()
ip.magic('load_ext storemagic')

def test_store_restore():
    ip.user_ns['foo'] = 78
    ip.magic('alias bar echo "hello"')
    tmpd = tempfile.mkdtemp()
    ip.magic('cd ' + tmpd)
    ip.magic('store foo')
    ip.magic('store bar')
    
    # Check storing
    nt.assert_equal(ip.db['autorestore/foo'], 78)
    nt.assert_in('bar', ip.db['stored_aliases'])
    
    # Remove those items
    ip.user_ns.pop('foo', None)
    ip.alias_manager.undefine_alias('bar')
    ip.magic('cd -')
    ip.user_ns['_dh'][:] = []
    
    # Check restoring
    ip.magic('store -r')
    nt.assert_equal(ip.user_ns['foo'], 78)
    nt.assert_in('bar', ip.alias_manager.alias_table)
    nt.assert_in(os.path.realpath(tmpd), ip.user_ns['_dh'])
    
    os.rmdir(tmpd)

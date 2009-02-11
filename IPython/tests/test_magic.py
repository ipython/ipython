""" Tests for various magic functions

Needs to be run by nose (to make ipython session available)

"""
def test_rehashx():
    # clear up everything
    _ip.IP.alias_table.clear()
    del _ip.db['syscmdlist']
    
    _ip.magic('rehashx')
    # Practically ALL ipython development systems will have more than 10 aliases

    assert len(_ip.IP.alias_table) > 10
    for key, val in _ip.IP.alias_table.items():
        # we must strip dots from alias names
        assert '.' not in key

    # rehashx must fill up syscmdlist
    scoms = _ip.db['syscmdlist']
    assert len(scoms) > 10

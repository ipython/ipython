# coding: utf-8
from IPython.lib import passwd
from IPython.lib.security import passwd_check, salt_len
import nose.tools as nt

def test_passwd_structure():
    p = passwd('passphrase')
    algorithm, salt, hashed = p.split(':')
    nt.assert_equal(algorithm, 'sha1')
    nt.assert_equal(len(salt), salt_len)
    nt.assert_equal(len(hashed), 40)

def test_roundtrip():
    p = passwd('passphrase')
    nt.assert_equal(passwd_check(p, 'passphrase'), True)

def test_bad():
    p = passwd('passphrase')
    nt.assert_equal(passwd_check(p, p), False)
    nt.assert_equal(passwd_check(p, 'a:b:c:d'), False)
    nt.assert_equal(passwd_check(p, 'a:b'), False)

def test_passwd_check_unicode():
    # GH issue #4524
    phash = u'sha1:9dc18846ca26:6bb62badc41fde529c258a8a7fbe259a91313df8'
    assert passwd_check(phash, u'mypassword³')
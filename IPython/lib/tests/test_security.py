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


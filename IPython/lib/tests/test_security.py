from IPython.lib import passwd
from IPython.lib.security import passwd_check
import nose.tools as nt

def test_passwd_structure():
    p = passwd('passphrase')
    algorithm, salt, hashed = p.split(':')
    nt.assert_equals(algorithm, 'sha1')
    nt.assert_equals(len(salt), 4)
    nt.assert_equals(len(hashed), 40)

def test_roundtrip():
    p = passwd('passphrase')
    nt.assert_equals(passwd_check(p, 'passphrase'), True)

def test_bad():
    p = passwd('passphrase')
    nt.assert_equals(passwd_check(p, p), False)
    nt.assert_equals(passwd_check(p, 'a:b:c:d'), False)
    nt.assert_equals(passwd_check(p, 'a:b'), False)


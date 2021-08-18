# coding: utf-8
from IPython.lib import passwd
from IPython.lib.security import passwd_check, salt_len

def test_passwd_structure():
    p = passwd("passphrase")
    algorithm, salt, hashed = p.split(":")
    assert algorithm == "sha1"
    assert len(salt) == salt_len
    assert len(hashed) == 40

def test_roundtrip():
    p = passwd("passphrase")
    assert passwd_check(p, "passphrase") is True


def test_bad():
    p = passwd('passphrase')
    assert passwd_check(p, p) is False
    assert passwd_check(p, "a:b:c:d") is False
    assert passwd_check(p, "a:b") is False


def test_passwd_check_unicode():
    # GH issue #4524
    phash = u'sha1:23862bc21dd3:7a415a95ae4580582e314072143d9c382c491e4f'
    assert passwd_check(phash, u"łe¶ŧ←↓→")

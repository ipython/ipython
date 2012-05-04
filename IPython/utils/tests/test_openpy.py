import io
import os.path
import nose.tools as nt

from IPython.utils import openpy

mydir = os.path.dirname(__file__)
nonascii_path = os.path.join(mydir, '../../core/tests/nonascii.py')

def test_detect_encoding():
    f = open(nonascii_path, 'rb')
    enc, lines = openpy.detect_encoding(f.readline)
    nt.assert_equal(enc, 'iso-8859-5')

def test_read_file():
    read_specified_enc = io.open(nonascii_path, encoding='iso-8859-5').read()
    read_detected_enc = openpy.read_py_file(nonascii_path, skip_encoding_cookie=False)
    nt.assert_equal(read_detected_enc, read_specified_enc)
    assert u'coding: iso-8859-5' in read_detected_enc
    
    read_strip_enc_cookie = openpy.read_py_file(nonascii_path, skip_encoding_cookie=True)
    assert u'coding: iso-8859-5' not in read_strip_enc_cookie
    

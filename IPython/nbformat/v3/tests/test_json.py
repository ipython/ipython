import pprint
from base64 import decodestring
from unittest import TestCase

from IPython.utils.py3compat import unicode_type
from ..nbjson import reads, writes
from .. import nbjson
from .nbexamples import nb0

from . import formattest

from .nbexamples import nb0


class TestJSON(formattest.NBFormatTest, TestCase):

    nb0_ref = None
    ext = 'ipynb'
    mod = nbjson

    def test_roundtrip_nosplit(self):
        """Ensure that multiline blobs are still readable"""
        # ensures that notebooks written prior to splitlines change
        # are still readable.
        s = writes(nb0, split_lines=False)
        self.assertEqual(nbjson.reads(s),nb0)

    def test_roundtrip_split(self):
        """Ensure that splitting multiline blocks is safe"""
        # This won't differ from test_roundtrip unless the default changes
        s = writes(nb0, split_lines=True)
        self.assertEqual(nbjson.reads(s),nb0)

    def test_read_png(self):
        """PNG output data is b64 unicode"""
        s = writes(nb0)
        nb1 = nbjson.reads(s)
        found_png = False
        for cell in nb1.worksheets[0].cells:
            if not 'outputs' in cell:
                continue
            for output in cell.outputs:
                if 'png' in output:
                    found_png = True
                    pngdata = output['png']
                    self.assertEqual(type(pngdata), unicode_type)
                    # test that it is valid b64 data
                    b64bytes = pngdata.encode('ascii')
                    raw_bytes = decodestring(b64bytes)
        assert found_png, "never found png output"

    def test_read_jpeg(self):
        """JPEG output data is b64 unicode"""
        s = writes(nb0)
        nb1 = nbjson.reads(s)
        found_jpeg = False
        for cell in nb1.worksheets[0].cells:
            if not 'outputs' in cell:
                continue
            for output in cell.outputs:
                if 'jpeg' in output:
                    found_jpeg = True
                    jpegdata = output['jpeg']
                    self.assertEqual(type(jpegdata), unicode_type)
                    # test that it is valid b64 data
                    b64bytes = jpegdata.encode('ascii')
                    raw_bytes = decodestring(b64bytes)
        assert found_jpeg, "never found jpeg output"





import pprint
from unittest import TestCase

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
        self.assertEquals(nbjson.reads(s),nb0)

    def test_roundtrip_split(self):
        """Ensure that splitting multiline blocks is safe"""
        # This won't differ from test_roundtrip unless the default changes
        s = writes(nb0, split_lines=True)
        self.assertEquals(nbjson.reads(s),nb0)




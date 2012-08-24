import pprint
from unittest import TestCase

from ..nbjson import reads, writes
from .nbexamples import nb0


class TestJSON(TestCase):

    def test_roundtrip(self):
        s = writes(nb0)
#        print
#        print pprint.pformat(nb0,indent=2)
#        print
#        print pprint.pformat(reads(s),indent=2)
#        print
#        print s
        self.assertEqual(reads(s),nb0)
    
    def test_roundtrip_nosplit(self):
        """Ensure that multiline blobs are still readable"""
        # ensures that notebooks written prior to splitlines change
        # are still readable.
        s = writes(nb0, split_lines=False)
        self.assertEqual(reads(s),nb0)

    def test_roundtrip_split(self):
        """Ensure that splitting multiline blocks is safe"""
        # This won't differ from test_roundtrip unless the default changes
        s = writes(nb0, split_lines=True)
        self.assertEqual(reads(s),nb0)




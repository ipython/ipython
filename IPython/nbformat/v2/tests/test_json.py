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
        self.assertEquals(reads(s),nb0)




from unittest import TestCase

from ..nbjson import reads, writes
from .nbexamples import nb0


class TestJSON(TestCase):

    def test_roundtrip(self):
        s = writes(nb0)
        self.assertEquals(reads(s),nb0)




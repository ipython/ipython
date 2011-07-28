from unittest import TestCase

from IPython.nbformat.nbjson import reads, writes
from IPython.nbformat.tests.nbexamples import nb0


class TestJSON(TestCase):

    def test_roundtrip(self):
        s = writes(nb0)
        self.assertEquals(reads(s),nb0)




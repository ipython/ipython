from unittest import TestCase

from IPython.nbformat.nbxml import reads, writes
from IPython.nbformat.tests.nbexamples import nb0


class TestXML(TestCase):

    def test_roundtrip(self):
        s = writes(nb0)
        self.assertEquals(reads(s),nb0)


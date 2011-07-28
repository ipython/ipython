from unittest import TestCase

from IPython.nbformat.nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook
)

from IPython.nbformat.nbpy import reads, writes
from IPython.nbformat.tests.nbexamples import nb0, nb0_py


class TestPy(TestCase):

    def test_write(self):
        s = writes(nb0)
        self.assertEquals(s,nb0_py)



from unittest import TestCase

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook
)

from ..nbpy import reads, writes
from .nbexamples import nb0, nb0_py


class TestPy(TestCase):

    def test_write(self):
        s = writes(nb0)
        self.assertEquals(s,nb0_py)


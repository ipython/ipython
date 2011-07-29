from unittest import TestCase

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_notebook
)

class TestCell(TestCase):

    def test_empty_code_cell(self):
        cc = new_code_cell()
        self.assertEquals(cc.cell_type,'code')
        self.assertEquals('code' not in cc, True)
        self.assertEquals('prompt_number' not in cc, True)

    def test_code_cell(self):
        cc = new_code_cell(code='a=10', prompt_number=0)
        self.assertEquals(cc.code, u'a=10')
        self.assertEquals(cc.prompt_number, 0)

    def test_empty_text_cell(self):
        tc = new_text_cell()
        self.assertEquals(tc.cell_type, 'text')
        self.assertEquals('text' not in tc, True)

    def test_text_cell(self):
        tc = new_text_cell('hi')
        self.assertEquals(tc.text, u'hi')


class TestNotebook(TestCase):

    def test_empty_notebook(self):
        nb = new_notebook()
        self.assertEquals(nb.cells, [])

    def test_notebooke(self):
        cells = [new_code_cell(),new_text_cell()]
        nb = new_notebook(cells=cells)
        self.assertEquals(nb.cells,cells)


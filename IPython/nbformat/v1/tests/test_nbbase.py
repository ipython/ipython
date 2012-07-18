from unittest import TestCase

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_notebook
)

class TestCell(TestCase):

    def test_empty_code_cell(self):
        cc = new_code_cell()
        self.assertEqual(cc.cell_type,'code')
        self.assertEqual('code' not in cc, True)
        self.assertEqual('prompt_number' not in cc, True)

    def test_code_cell(self):
        cc = new_code_cell(code='a=10', prompt_number=0)
        self.assertEqual(cc.code, u'a=10')
        self.assertEqual(cc.prompt_number, 0)

    def test_empty_text_cell(self):
        tc = new_text_cell()
        self.assertEqual(tc.cell_type, 'text')
        self.assertEqual('text' not in tc, True)

    def test_text_cell(self):
        tc = new_text_cell('hi')
        self.assertEqual(tc.text, u'hi')


class TestNotebook(TestCase):

    def test_empty_notebook(self):
        nb = new_notebook()
        self.assertEqual(nb.cells, [])

    def test_notebooke(self):
        cells = [new_code_cell(),new_text_cell()]
        nb = new_notebook(cells=cells)
        self.assertEqual(nb.cells,cells)


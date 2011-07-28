from unittest import TestCase

from IPython.nbformat.nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook
)

class TestCell(TestCase):

    def test_empty_code_cell(self):
        cc = new_code_cell()
        self.assertEquals(cc.cell_type,'code')
        self.assertEquals('input' not in cc, True)
        self.assertEquals('prompt_number' not in cc, True)
        self.assertEquals(cc.output, NotebookNode())

    def test_code_cell(self):
        cc = new_code_cell(input='a=10', prompt_number=0, output_svg='foo', output_text='10')
        self.assertEquals(cc.input, u'a=10')
        self.assertEquals(cc.prompt_number, 0)
        self.assertEquals(cc.output.svg, u'foo')
        self.assertEquals(cc.output.text, u'10')

    def test_empty_text_cell(self):
        tc = new_text_cell()
        self.assertEquals(tc.cell_type, 'text')
        self.assertEquals('text' not in tc, True)

    def test_text_cell(self):
        tc = new_text_cell('hi')
        self.assertEquals(tc.text, u'hi')


class TestWorksheet(TestCase):

    def test_empty_worksheet(self):
        ws = new_worksheet()
        self.assertEquals(ws.cells,[])
        self.assertEquals('name' not in ws, True)

    def test_worksheet(self):
        cells = [new_code_cell(), new_text_cell()]
        ws = new_worksheet(cells=cells,name='foo')
        self.assertEquals(ws.cells,cells)
        self.assertEquals(ws.name,u'foo')

class TestNotebook(TestCase):

    def test_empty_notebook(self):
        nb = new_notebook()
        self.assertEquals('id' in nb, True)
        self.assertEquals(nb.worksheets, [])
        self.assertEquals('name' not in nb, True)

    def test_notebooke(self):
        worksheets = [new_worksheet(),new_worksheet()]
        nb = new_notebook(name='foo',worksheets=worksheets)
        self.assertEquals(nb.name,u'foo')
        self.assertEquals(nb.worksheets,worksheets)


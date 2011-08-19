from unittest import TestCase

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output
)

class TestCell(TestCase):

    def test_empty_code_cell(self):
        cc = new_code_cell()
        self.assertEquals(cc.cell_type,'code')
        self.assertEquals('input' not in cc, True)
        self.assertEquals('prompt_number' not in cc, True)
        self.assertEquals(cc.outputs, [])
        self.assertEquals(cc.collapsed, False)

    def test_code_cell(self):
        cc = new_code_cell(input='a=10', prompt_number=0, collapsed=True)
        cc.outputs = [new_output(output_type='pyout',
            output_svg='foo',output_text='10',prompt_number=0)]
        self.assertEquals(cc.input, u'a=10')
        self.assertEquals(cc.prompt_number, 0)
        self.assertEquals(cc.language, u'python')
        self.assertEquals(cc.outputs[0].svg, u'foo')
        self.assertEquals(cc.outputs[0].text, u'10')
        self.assertEquals(cc.outputs[0].prompt_number, 0)
        self.assertEquals(cc.collapsed, True)

    def test_pyerr(self):
        o = new_output(output_type=u'pyerr', etype=u'NameError',
            evalue=u'Name not found', traceback=[u'frame 0', u'frame 1', u'frame 2']
        )
        self.assertEquals(o.output_type, u'pyerr')
        self.assertEquals(o.etype, u'NameError')
        self.assertEquals(o.evalue, u'Name not found')
        self.assertEquals(o.traceback, [u'frame 0', u'frame 1', u'frame 2'])

    def test_empty_html_cell(self):
        tc = new_text_cell(u'html')
        self.assertEquals(tc.cell_type, u'html')
        self.assertEquals('source' not in tc, True)
        self.assertEquals('rendered' not in tc, True)

    def test_html_cell(self):
        tc = new_text_cell(u'html', 'hi', 'hi')
        self.assertEquals(tc.source, u'hi')
        self.assertEquals(tc.rendered, u'hi')

    def test_empty_markdown_cell(self):
        tc = new_text_cell(u'markdown')
        self.assertEquals(tc.cell_type, u'markdown')
        self.assertEquals('source' not in tc, True)
        self.assertEquals('rendered' not in tc, True)

    def test_markdown_cell(self):
        tc = new_text_cell(u'markdown', 'hi', 'hi')
        self.assertEquals(tc.source, u'hi')
        self.assertEquals(tc.rendered, u'hi')


class TestWorksheet(TestCase):

    def test_empty_worksheet(self):
        ws = new_worksheet()
        self.assertEquals(ws.cells,[])
        self.assertEquals('name' not in ws, True)

    def test_worksheet(self):
        cells = [new_code_cell(), new_text_cell(u'html')]
        ws = new_worksheet(cells=cells,name='foo')
        self.assertEquals(ws.cells,cells)
        self.assertEquals(ws.name,u'foo')

class TestNotebook(TestCase):

    def test_empty_notebook(self):
        nb = new_notebook()
        self.assertEquals(nb.worksheets, [])
        self.assertEquals('name' not in nb, True)
        self.assertEquals(nb.nbformat,2)

    def test_notebook(self):
        worksheets = [new_worksheet(),new_worksheet()]
        nb = new_notebook(name='foo',worksheets=worksheets)
        self.assertEquals(nb.name,u'foo')
        self.assertEquals(nb.worksheets,worksheets)
        self.assertEquals(nb.nbformat,2)


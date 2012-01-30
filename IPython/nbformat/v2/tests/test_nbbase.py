from unittest import TestCase

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output,
    new_author, new_metadata
)

class TestCell(TestCase):

    def test_empty_code_cell(self):
        cc = new_code_cell()
        self.assertEquals(cc.cell_type,u'code')
        self.assertEquals(u'input' not in cc, True)
        self.assertEquals(u'prompt_number' not in cc, True)
        self.assertEquals(cc.outputs, [])
        self.assertEquals(cc.collapsed, False)

    def test_code_cell(self):
        cc = new_code_cell(input='a=10', prompt_number=0, collapsed=True)
        cc.outputs = [new_output(output_type=u'pyout',
            output_svg=u'foo',output_text=u'10',prompt_number=0)]
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
        self.assertEquals(u'source' not in tc, True)
        self.assertEquals(u'rendered' not in tc, True)

    def test_html_cell(self):
        tc = new_text_cell(u'html', 'hi', 'hi')
        self.assertEquals(tc.source, u'hi')
        self.assertEquals(tc.rendered, u'hi')

    def test_empty_markdown_cell(self):
        tc = new_text_cell(u'markdown')
        self.assertEquals(tc.cell_type, u'markdown')
        self.assertEquals(u'source' not in tc, True)
        self.assertEquals(u'rendered' not in tc, True)

    def test_markdown_cell(self):
        tc = new_text_cell(u'markdown', 'hi', 'hi')
        self.assertEquals(tc.source, u'hi')
        self.assertEquals(tc.rendered, u'hi')


class TestWorksheet(TestCase):

    def test_empty_worksheet(self):
        ws = new_worksheet()
        self.assertEquals(ws.cells,[])
        self.assertEquals(u'name' not in ws, True)

    def test_worksheet(self):
        cells = [new_code_cell(), new_text_cell(u'html')]
        ws = new_worksheet(cells=cells,name=u'foo')
        self.assertEquals(ws.cells,cells)
        self.assertEquals(ws.name,u'foo')

class TestNotebook(TestCase):

    def test_empty_notebook(self):
        nb = new_notebook()
        self.assertEquals(nb.worksheets, [])
        self.assertEquals(nb.metadata, NotebookNode())
        self.assertEquals(nb.nbformat,2)

    def test_notebook(self):
        worksheets = [new_worksheet(),new_worksheet()]
        metadata = new_metadata(name=u'foo')
        nb = new_notebook(metadata=metadata,worksheets=worksheets)
        self.assertEquals(nb.metadata.name,u'foo')
        self.assertEquals(nb.worksheets,worksheets)
        self.assertEquals(nb.nbformat,2)

class TestMetadata(TestCase):

    def test_empty_metadata(self):
        md = new_metadata()
        self.assertEquals(u'name' not in md, True)
        self.assertEquals(u'authors' not in md, True)
        self.assertEquals(u'license' not in md, True)
        self.assertEquals(u'saved' not in md, True)
        self.assertEquals(u'modified' not in md, True)
        self.assertEquals(u'gistid' not in md, True)

    def test_metadata(self):
        authors = [new_author(name='Bart Simpson',email='bsimpson@fox.com')]
        md = new_metadata(name=u'foo',license=u'BSD',created=u'today',
            modified=u'now',gistid=u'21341231',authors=authors)
        self.assertEquals(md.name, u'foo')
        self.assertEquals(md.license, u'BSD')
        self.assertEquals(md.created, u'today')
        self.assertEquals(md.modified, u'now')
        self.assertEquals(md.gistid, u'21341231')
        self.assertEquals(md.authors, authors)


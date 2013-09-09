from unittest import TestCase

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output,
    new_author, new_metadata, new_heading_cell, nbformat
)

class TestCell(TestCase):

    def test_empty_code_cell(self):
        cc = new_code_cell()
        self.assertEqual(cc.cell_type,u'code')
        self.assertEqual(u'input' not in cc, True)
        self.assertEqual(u'prompt_number' not in cc, True)
        self.assertEqual(cc.outputs, [])
        self.assertEqual(cc.collapsed, False)

    def test_code_cell(self):
        cc = new_code_cell(input='a=10', prompt_number=0, collapsed=True)
        cc.outputs = [new_output(output_type=u'pyout',
            output_svg=u'foo',output_text=u'10',prompt_number=0)]
        self.assertEqual(cc.input, u'a=10')
        self.assertEqual(cc.prompt_number, 0)
        self.assertEqual(cc.language, u'python')
        self.assertEqual(cc.outputs[0].svg, u'foo')
        self.assertEqual(cc.outputs[0].text, u'10')
        self.assertEqual(cc.outputs[0].prompt_number, 0)
        self.assertEqual(cc.collapsed, True)

    def test_pyerr(self):
        o = new_output(output_type=u'pyerr', ename=u'NameError',
            evalue=u'Name not found', traceback=[u'frame 0', u'frame 1', u'frame 2']
        )
        self.assertEqual(o.output_type, u'pyerr')
        self.assertEqual(o.ename, u'NameError')
        self.assertEqual(o.evalue, u'Name not found')
        self.assertEqual(o.traceback, [u'frame 0', u'frame 1', u'frame 2'])

    def test_empty_html_cell(self):
        tc = new_text_cell(u'html')
        self.assertEqual(tc.cell_type, u'html')
        self.assertEqual(u'source' not in tc, True)
        self.assertEqual(u'rendered' not in tc, True)

    def test_html_cell(self):
        tc = new_text_cell(u'html', 'hi', 'hi')
        self.assertEqual(tc.source, u'hi')
        self.assertEqual(tc.rendered, u'hi')

    def test_empty_markdown_cell(self):
        tc = new_text_cell(u'markdown')
        self.assertEqual(tc.cell_type, u'markdown')
        self.assertEqual(u'source' not in tc, True)
        self.assertEqual(u'rendered' not in tc, True)

    def test_markdown_cell(self):
        tc = new_text_cell(u'markdown', 'hi', 'hi')
        self.assertEqual(tc.source, u'hi')
        self.assertEqual(tc.rendered, u'hi')

    def test_empty_raw_cell(self):
        tc = new_text_cell(u'raw')
        self.assertEqual(tc.cell_type, u'raw')
        self.assertEqual(u'source' not in tc, True)
        self.assertEqual(u'rendered' not in tc, True)

    def test_raw_cell(self):
        tc = new_text_cell(u'raw', 'hi', 'hi')
        self.assertEqual(tc.source, u'hi')
        self.assertEqual(tc.rendered, u'hi')

    def test_empty_heading_cell(self):
        tc = new_heading_cell()
        self.assertEqual(tc.cell_type, u'heading')
        self.assertEqual(u'source' not in tc, True)
        self.assertEqual(u'rendered' not in tc, True)

    def test_heading_cell(self):
        tc = new_heading_cell(u'hi', u'hi', level=2)
        self.assertEqual(tc.source, u'hi')
        self.assertEqual(tc.rendered, u'hi')
        self.assertEqual(tc.level, 2)


class TestWorksheet(TestCase):

    def test_empty_worksheet(self):
        ws = new_worksheet()
        self.assertEqual(ws.cells,[])
        self.assertEqual(u'name' not in ws, True)

    def test_worksheet(self):
        cells = [new_code_cell(), new_text_cell(u'html')]
        ws = new_worksheet(cells=cells,name=u'foo')
        self.assertEqual(ws.cells,cells)
        self.assertEqual(ws.name,u'foo')

class TestNotebook(TestCase):

    def test_empty_notebook(self):
        nb = new_notebook()
        self.assertEqual(nb.worksheets, [])
        self.assertEqual(nb.metadata, NotebookNode())
        self.assertEqual(nb.nbformat,nbformat)

    def test_notebook(self):
        worksheets = [new_worksheet(),new_worksheet()]
        metadata = new_metadata(name=u'foo')
        nb = new_notebook(metadata=metadata,worksheets=worksheets)
        self.assertEqual(nb.metadata.name,u'foo')
        self.assertEqual(nb.worksheets,worksheets)
        self.assertEqual(nb.nbformat,nbformat)

    def test_notebook_name(self):
        worksheets = [new_worksheet(),new_worksheet()]
        nb = new_notebook(name='foo',worksheets=worksheets)
        self.assertEqual(nb.metadata.name,u'foo')
        self.assertEqual(nb.worksheets,worksheets)
        self.assertEqual(nb.nbformat,nbformat)

class TestMetadata(TestCase):

    def test_empty_metadata(self):
        md = new_metadata()
        self.assertEqual(u'name' not in md, True)
        self.assertEqual(u'authors' not in md, True)
        self.assertEqual(u'license' not in md, True)
        self.assertEqual(u'saved' not in md, True)
        self.assertEqual(u'modified' not in md, True)
        self.assertEqual(u'gistid' not in md, True)

    def test_metadata(self):
        authors = [new_author(name='Bart Simpson',email='bsimpson@fox.com')]
        md = new_metadata(name=u'foo',license=u'BSD',created=u'today',
            modified=u'now',gistid=u'21341231',authors=authors)
        self.assertEqual(md.name, u'foo')
        self.assertEqual(md.license, u'BSD')
        self.assertEqual(md.created, u'today')
        self.assertEqual(md.modified, u'now')
        self.assertEqual(md.gistid, u'21341231')
        self.assertEqual(md.authors, authors)

class TestOutputs(TestCase):
    def test_binary_png(self):
        out = new_output(output_png=b'\x89PNG\r\n\x1a\n')

    def test_b64b6tes_png(self):
        out = new_output(output_png=b'iVBORw0KG')

    def test_binary_jpeg(self):
        out = new_output(output_jpeg=b'\xff\xd8')

    def test_b64b6tes_jpeg(self):
        out = new_output(output_jpeg=b'/9')

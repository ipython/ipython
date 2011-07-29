"""Read and write notebooks as regular .py files."""

from .rwbase import NotebookReader, NotebookWriter
from .nbbase import new_code_cell, new_worksheet, new_notebook


class PyReader(NotebookReader):

    def reads(self, s, **kwargs):
        return self.to_notebook(s,**kwargs)

    def to_notebook(self, s, **kwargs):
        lines = s.splitlines()
        cells = []
        cell_lines = []
        for line in lines:
            if line.startswith(u'# <codecell>'):
                cell_lines = []
            if line.startswith(u'# </codecell>'):
                code = u'\n'.join(cell_lines)
                code = code.strip(u'\n')
                if code:
                    cells.append(new_code_cell(input=code))
            else:
                cell_lines.append(line)
        ws = new_worksheet(cells=cells)
        nb = new_notebook(worksheets=[ws])
        return nb


class PyWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        lines = []
        lines.extend(['# <nbformat>2</nbformat>',''])
        for ws in nb.worksheets:
            for cell in ws.cells:
                if cell.cell_type == 'code':
                    input = cell.input
                    lines.extend([u'# <codecell>',u''])
                    lines.extend(input.splitlines())
                    lines.extend([u'',u'# </codecell>'])
        lines.append('')
        return unicode('\n'.join(lines))


_reader = PyReader()
_writer = PyWriter()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook
write = _writer.write
writes = _writer.writes


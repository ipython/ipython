"""Read and write notebooks as regular .py files."""

from .rwbase import NotebookReader, NotebookWriter
from .nbbase import new_code_cell, new_worksheet, new_notebook


class PyReader(NotebookReader):

    def reads(self, s, **kwargs):
        lines = s.splitlines()
        cells = []
        cell_lines = []
        for line in lines:
            if line.startswith(u'# <codecell>'):
                code = u'\n'.join(cell_lines)
                code = code.strip(u'\n')
                if code:
                    cells.append(new_code_cell(input=code))
                    cell_lines = []
            else:
                cell_lines.append(line)
        ws = new_worksheet(cells=cells)
        nb = new_notebook(worksheets=[ws])
        return nb


class PyWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        lines = []
        for ws in nb.worksheets:
            for cell in ws.cells:
                if cell.cell_type == 'code':
                    input = cell.input
                    lines.extend([u'# <codecell>',u''])
                    lines.extend(input.splitlines())
                    lines.append(u'')
        return unicode('\n'.join(lines))


_reader = PyReader()
_writer = PyWriter()

reads = _reader.reads
read = _reader.read
write = _writer.write
writes = _writer.writes

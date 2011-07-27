"""Read and write notebooks as regular .py files."""

from .base import NotebookReader, NotebookWriter
from .nbdict import new_code_cell, new_worksheet, new_notebook


class PyReader(NotebookReader):

    def reads(s, **kwargs):
        lines = s.splitlines()
        cells = []
        cell_lines = []
        for line in lines:
            if line.startswith('# <codecell>'):
                code = '\n'.join(cell_lines)
                code = code.strip('\n')
                if code:
                    cells.append(new_code_cell(input=code))
                    cell_lines = []
            else:
                cell_lines.append(line)
        ws = new_worksheet(cells=cells)
        nb = new_notebook(worksheets=[ws])
        return nb


class PyWriter(NotebookWriter):

    def writes(nb, **kwargs):
        lines = []
        for ws in nb['worksheets']:
            for cell in ws['cells']:
                if cell['cell_type'] == 'code':
                    input = cell['input']
                    lines.extend(input.splitlines())
                    lines.extend(['','# <codecell>',''])
        return ''.join(lines)


_reader = PyReader()
_writer = PyWriter()

reads = _reader.reads
read = _reader.read
write = _writer.write
writes = _writer.writes

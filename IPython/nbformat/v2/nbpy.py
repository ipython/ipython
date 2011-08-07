"""Read and write notebooks as regular .py files."""

from .rwbase import NotebookReader, NotebookWriter
from .nbbase import new_code_cell, new_worksheet, new_notebook


class PyReaderError(Exception):
    pass


class PyReader(NotebookReader):

    def reads(self, s, **kwargs):
        return self.to_notebook(s,**kwargs)

    def to_notebook(self, s, **kwargs):
        lines = s.splitlines()
        cells = []
        cell_lines = []
        code_cell = False
        for line in lines:
            if line.startswith(u'# <codecell>'):
                if code_cell:
                    raise PyReaderError('Unexpected <codecell>')
                if cell_lines:
                    for block in self.split_lines_into_blocks(cell_lines):
                        cells.append(new_code_cell(input=block))
                cell_lines = []
                code_cell = True
            if line.startswith(u'# </codecell>'):
                if not code_cell:
                    raise PyReaderError('Unexpected </codecell>')
                code = u'\n'.join(cell_lines)
                code = code.strip(u'\n')
                if code:
                    cells.append(new_code_cell(input=code))
                code_cell = False
            else:
                cell_lines.append(line)
        # For lines we were not able to process, 
        for block in self.split_lines_into_blocks(cell_lines):
            cells.append(new_code_cell(input=block))
        ws = new_worksheet(cells=cells)
        nb = new_notebook(worksheets=[ws])
        return nb

    def split_lines_into_blocks(self, lines):
        import ast
        source = '\n'.join(lines)
        code = ast.parse(source)
        starts = [x.lineno-1 for x in code.body]
        for i in range(len(starts)-1):
            yield '\n'.join(lines[starts[i]:starts[i+1]]).strip('\n')
        yield '\n'.join(lines[starts[-1]:]).strip('\n')


class PyWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        lines = []
        lines.extend(['# <nbformat>2</nbformat>',''])
        for ws in nb.worksheets:
            for cell in ws.cells:
                if cell.cell_type == 'code':
                    input = cell.get('input')
                    if input is not None:
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


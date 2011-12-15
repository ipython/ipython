"""Read and write notebooks as regular .py files.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import re
from .rwbase import NotebookReader, NotebookWriter
from .nbbase import new_code_cell, new_text_cell, new_worksheet, new_notebook

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

_encoding_declaration_re = re.compile(r"^#.*coding[:=]\s*([-\w.]+)")

class PyReaderError(Exception):
    pass


class PyReader(NotebookReader):

    def reads(self, s, **kwargs):
        return self.to_notebook(s,**kwargs)

    def to_notebook(self, s, **kwargs):
        lines = s.splitlines()
        cells = []
        cell_lines = []
        state = u'codecell'
        for line in lines:
            if line.startswith(u'# <nbformat>') or _encoding_declaration_re.match(line):
                pass
            elif line.startswith(u'# <codecell>'):
                cell = self.new_cell(state, cell_lines)
                if cell is not None:
                    cells.append(cell)
                state = u'codecell'
                cell_lines = []
            elif line.startswith(u'# <htmlcell>'):
                cell = self.new_cell(state, cell_lines)
                if cell is not None:
                    cells.append(cell)
                state = u'htmlcell'
                cell_lines = []
            elif line.startswith(u'# <markdowncell>'):
                cell = self.new_cell(state, cell_lines)
                if cell is not None:
                    cells.append(cell)
                state = u'markdowncell'
                cell_lines = []
            else:
                cell_lines.append(line)
        if cell_lines and state == u'codecell':
            cell = self.new_cell(state, cell_lines)
            if cell is not None:
                cells.append(cell)
        ws = new_worksheet(cells=cells)
        nb = new_notebook(worksheets=[ws])
        return nb

    def new_cell(self, state, lines):
        if state == u'codecell':
            input = u'\n'.join(lines)
            input = input.strip(u'\n')
            if input:
                return new_code_cell(input=input)
        elif state == u'htmlcell':
            text = self._remove_comments(lines)
            if text:
                return new_text_cell(u'html',source=text)
        elif state == u'markdowncell':
            text = self._remove_comments(lines)
            if text:
                return new_text_cell(u'markdown',source=text)

    def _remove_comments(self, lines):
        new_lines = []
        for line in lines:
            if line.startswith(u'#'):
                new_lines.append(line[2:])
            else:
                new_lines.append(line)
        text = u'\n'.join(new_lines)
        text = text.strip(u'\n')
        return text

    def split_lines_into_blocks(self, lines):
        if len(lines) == 1:
            yield lines[0]
            raise StopIteration()
        import ast
        source = '\n'.join(lines)
        code = ast.parse(source)
        starts = [x.lineno-1 for x in code.body]
        for i in range(len(starts)-1):
            yield '\n'.join(lines[starts[i]:starts[i+1]]).strip('\n')
        yield '\n'.join(lines[starts[-1]:]).strip('\n')


class PyWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        lines = [u'# -*- coding: utf-8 -*-']
        lines.extend([u'# <nbformat>2</nbformat>',''])
        for ws in nb.worksheets:
            for cell in ws.cells:
                if cell.cell_type == u'code':
                    input = cell.get(u'input')
                    if input is not None:
                        lines.extend([u'# <codecell>',u''])
                        lines.extend(input.splitlines())
                        lines.append(u'')
                elif cell.cell_type == u'html':
                    input = cell.get(u'source')
                    if input is not None:
                        lines.extend([u'# <htmlcell>',u''])
                        lines.extend([u'# ' + line for line in input.splitlines()])
                        lines.append(u'')
                elif cell.cell_type == u'markdown':
                    input = cell.get(u'source')
                    if input is not None:
                        lines.extend([u'# <markdowncell>',u''])
                        lines.extend([u'# ' + line for line in input.splitlines()])
                        lines.append(u'')
        lines.append('')
        return unicode('\n'.join(lines))


_reader = PyReader()
_writer = PyWriter()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook
write = _writer.write
writes = _writer.writes


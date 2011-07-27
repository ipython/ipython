"""Read and write notebook files as XML."""

from xml.etree import ElementTree as ET

from .base import NotebookReader, NotebookWriter
from .nbdict import new_code_cell, new_worksheet, new_notebook


class XMLReader(NotebookReader):

    def reads(s, **kwargs):
        pass


class XMLWriter(NotebookWriter):

    def writes(nb, **kwargs):
        nb_e = ET.Element('notebook')
        name_e = ET.SubElement(nb_e, 'name')
        name_e.text = nb.get('name','')
        id_e = ET.SubElement(nb_e, 'id')
        id_e.text = nb.get('id','')
        for ws in nb['worksheets']:
            ws_e = ET.SubElement(nb_e, 'worksheet')
            ws_name_e = ET.SubElement(ws_e, 'name')
            ws_name_e.text = ws.get('name','')
            for cell in ws['cells']:
                cell_type = cell['cell_type']
                if cell_type == 'code':
                    output = cell['output']
                    cell_e = ET.SubElement(ws_e, 'cell')
                    input_e = ET.SubElement(cell_e, 'input')
                    input_e.text = cell.get('input','')
                    output_e = ET.SubElement(cell_e, 'output')
                    text_e = ET.SubElement(output_e, 'text')
                    text_e.text = cell.output
                elif cell_type == 'text':
                    pass
                    


_reader = XMLReader()
_writer = XMLWriter()

reads = _reader.reads
read = _reader.read
write = _writer.write
writes = _writer.writes

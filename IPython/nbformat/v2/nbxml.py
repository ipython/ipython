"""Read and write notebook files as XML."""

from base64 import encodestring, decodestring
from xml.etree import ElementTree as ET

from .rwbase import NotebookReader, NotebookWriter
from .nbbase import (
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output
)

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def _get_text(e, tag):
    sub_e = e.find(tag)
    if sub_e is None:
        return None
    else:
        return sub_e.text


def _set_text(nbnode, attr, parent, tag):
    if attr in nbnode:
        e = ET.SubElement(parent, tag)
        e.text = nbnode[attr]


def _get_int(e, tag):
    sub_e = e.find(tag)
    if sub_e is None:
        return None
    else:
        return int(sub_e.text)


def _set_int(nbnode, attr, parent, tag):
    if attr in nbnode:
        e = ET.SubElement(parent, tag)
        e.text = unicode(nbnode[attr])


def _get_binary(e, tag):
    sub_e = e.find(tag)
    if sub_e is None:
        return None
    else:
        return decodestring(sub_e.text)


def _set_binary(nbnode, attr, parent, tag):
    if attr in nbnode:
        e = ET.SubElement(parent, tag)
        e.text = encodestring(nbnode[attr])


class XMLReader(NotebookReader):

    def reads(self, s, **kwargs):
        root = ET.fromstring(s)
        return self.to_notebook(root, **kwargs)

    def to_notebook(self, root, **kwargs):
        nbname = _get_text(root,'name')
        nbid = _get_text(root,'id')
        
        worksheets = []
        for ws_e in root.find('worksheets').getiterator('worksheet'):
            wsname = _get_text(ws_e,'name')
            cells = []
            for cell_e in ws_e.find('cells').getiterator():
                if cell_e.tag == 'codecell':
                    input = _get_text(cell_e,'input')
                    prompt_number = _get_int(cell_e,'prompt_number')
                    language = _get_text(cell_e,'language')
                    outputs = []
                    for output_e in cell_e.find('outputs').getiterator('output'):
                        output_type = _get_text(output_e,'output_type')
                        output_text = _get_text(output_e,'text')
                        output_png = _get_binary(output_e,'png')
                        output_svg = _get_text(output_e,'svg')
                        output_html = _get_text(output_e,'html')
                        output_latex = _get_text(output_e,'latex')
                        output_json = _get_text(output_e,'json')
                        output_javascript = _get_text(output_e,'javascript')
                        output = new_output(output_type=output_type,output_png=output_png,
                            output_text=output_text,output_svg=output_svg,
                            output_html=output_html,output_latex=output_latex,
                            output_json=output_json,output_javascript=output_javascript
                        )
                        outputs.append(output)
                    cc = new_code_cell(input=input,prompt_number=prompt_number,
                                       language=language,outputs=outputs)
                    cells.append(cc)
                if cell_e.tag == 'textcell':
                    text = _get_text(cell_e,'text')
                    cells.append(new_text_cell(text=text))
            ws = new_worksheet(name=wsname,cells=cells)
            worksheets.append(ws)

        nb = new_notebook(name=nbname,id=nbid,worksheets=worksheets)
        return nb


class XMLWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        nb_e = ET.Element('notebook')
        _set_text(nb,'name',nb_e,'name')
        _set_text(nb,'id',nb_e,'id')
        _set_int(nb,'nbformat',nb_e,'nbformat')
        wss_e = ET.SubElement(nb_e,'worksheets')
        for ws in nb.worksheets:
            ws_e = ET.SubElement(wss_e, 'worksheet')
            _set_text(ws,'name',ws_e,'name')
            cells_e = ET.SubElement(ws_e,'cells')
            for cell in ws.cells:
                cell_type = cell.cell_type
                if cell_type == 'code':
                    cell_e = ET.SubElement(cells_e, 'codecell')
                    _set_text(cell,'input',cell_e,'input')
                    _set_text(cell,'language',cell_e,'language')
                    _set_int(cell,'prompt_number',cell_e,'prompt_number')
                    outputs_e = ET.SubElement(cell_e, 'outputs')
                    for output in cell.outputs:
                        output_e = ET.SubElement(outputs_e, 'output')
                        _set_text(output,'output_type',output_e,'output_type')
                        _set_text(output,'text',output_e,'text')
                        _set_binary(output,'png',output_e,'png')
                        _set_text(output,'html',output_e,'html')
                        _set_text(output,'svg',output_e,'svg')
                        _set_text(output,'latex',output_e,'latex')
                        _set_text(output,'json',output_e,'json')
                        _set_text(output,'javascript',output_e,'javascript')
                elif cell_type == 'text':
                    cell_e = ET.SubElement(cells_e, 'textcell')
                    _set_text(cell,'text',cell_e,'text')

        indent(nb_e)
        txt = ET.tostring(nb_e, encoding="utf-8")
        txt = '<?xml version="1.0" encoding="utf-8"?>\n' + txt
        return txt
        
                    
_reader = XMLReader()
_writer = XMLWriter()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook
write = _writer.write
writes = _writer.writes


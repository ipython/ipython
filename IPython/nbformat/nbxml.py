"""Read and write notebook files as XML."""

from xml.etree import ElementTree as ET

from .rwbase import NotebookReader, NotebookWriter
from .nbbase import new_code_cell, new_text_cell, new_worksheet, new_notebook


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


class XMLReader(NotebookReader):

    def reads(self, s, **kwargs):
        root = ET.fromstring(s)

        nbname = _get_text(root,'name')
        nbid = _get_text(root,'id')
        
        worksheets = []
        for ws_e in root.getiterator('worksheet'):
            wsname = _get_text(ws_e,'name')
            cells = []
            for cell_e in ws_e.getiterator():
                if cell_e.tag == 'codecell':
                    input = _get_text(cell_e,'input')
                    output_e = cell_e.find('output')
                    if output_e is not None:
                        output_text = _get_text(output_e,'text')
                        output_png = _get_text(output_e,'png')
                        output_svg = _get_text(output_e,'svg')
                        output_html = _get_text(output_e,'html')
                        output_latex = _get_text(output_e,'latex')
                        output_json = _get_text(output_e,'json')
                        output_javascript = _get_text(output_e,'javascript')
                    cc = new_code_cell(input=input,output_png=output_png,
                        output_text=output_text,output_svg=output_svg,
                        output_html=output_html,output_latex=output_latex,
                        output_json=output_json,output_javascript=output_javascript
                    )
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
        if 'name' in nb:
            name_e = ET.SubElement(nb_e, 'name')
            name_e.text = nb.name
        if 'id' in nb:
            id_e = ET.SubElement(nb_e, 'id')
            id_e.text = nb.id
        for ws in nb.worksheets:
            ws_e = ET.SubElement(nb_e, 'worksheet')
            if 'name' in ws:
                ws_name_e = ET.SubElement(ws_e, 'name')
                ws_name_e.text = ws.name
            for cell in ws.cells:
                cell_type = cell.cell_type
                if cell_type == 'code':
                    output = cell.output
                    cell_e = ET.SubElement(ws_e, 'codecell')
                    output_e = ET.SubElement(cell_e, 'output')

                    if 'input' in cell:
                        input_e = ET.SubElement(cell_e, 'input')
                        input_e.text = cell.input
                    if 'prompt_number' in cell:
                        prompt_number_e = ET.SubElement(cell_e, 'prompt_number')
                        input_e.text = cell.prompt_number

                    if 'text' in output:
                        text_e = ET.SubElement(output_e, 'text')
                        text_e.text = output.text
                    if 'png' in output:
                        png_e = ET.SubElement(output_e, 'png')
                        png_e.text = output.png
                    if 'html' in output:
                        html_e = ET.SubElement(output_e, 'html')
                        html_e.text = output.html
                    if 'svg' in output:
                        svg_e = ET.SubElement(output_e, 'svg')
                        svg_e.text = output.svg
                    if 'latex' in output:
                        latex_e = ET.SubElement(output_e, 'latex')
                        latex_e.text = output.latex
                    if 'json' in output:
                        json_e = ET.SubElement(output_e, 'json')
                        json_e.text = output.json
                    if 'javascript' in output:
                        javascript_e = ET.SubElement(output_e, 'javascript')
                        javascript_e.text = output.javascript
                elif cell_type == 'text':
                    cell_e = ET.SubElement(ws_e, 'textcell')
                    if 'text' in cell:
                        cell_text_e = ET.SubElement(cell_e, 'text')
                        cell_text_e.text = cell.text

        indent(nb_e)
        txt = ET.tostring(nb_e, encoding="utf-8")
        txt = '<?xml version="1.0" encoding="utf-8"?>\n' + txt
        return txt
        
                    
_reader = XMLReader()
_writer = XMLWriter()

reads = _reader.reads
read = _reader.read
write = _writer.write
writes = _writer.writes

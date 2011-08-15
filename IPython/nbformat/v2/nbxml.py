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


def _get_bool(e, tag):
    sub_e = e.find(tag)
    if sub_e is None:
        return None
    else:
        return bool(int(sub_e.text))


def _set_bool(nbnode, attr, parent, tag):
    if attr in nbnode:
        e = ET.SubElement(parent, tag)
        if nbnode[attr]:
            e.text = u'1'
        else:
            e.text = u'0'


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
        nbname = _get_text(root,u'name')
        nbauthor = _get_text(root,u'author')
        nbemail = _get_text(root,u'email')
        nblicense = _get_text(root,u'license')
        nbcreated = _get_text(root,u'created')
        nbsaved = _get_text(root,u'saved')
        
        worksheets = []
        for ws_e in root.find(u'worksheets').getiterator(u'worksheet'):
            wsname = _get_text(ws_e,u'name')
            cells = []
            for cell_e in ws_e.find(u'cells').getiterator():
                if cell_e.tag == u'codecell':
                    input = _get_text(cell_e,u'input')
                    prompt_number = _get_int(cell_e,u'prompt_number')
                    collapsed = _get_bool(cell_e,u'collapsed')
                    language = _get_text(cell_e,u'language')
                    outputs = []
                    for output_e in cell_e.find(u'outputs').getiterator(u'output'):
                        output_type = _get_text(output_e,u'output_type')
                        output_text = _get_text(output_e,u'text')
                        output_png = _get_binary(output_e,u'png')
                        output_jpeg = _get_binary(output_e,u'jpeg')
                        output_svg = _get_text(output_e,u'svg')
                        output_html = _get_text(output_e,u'html')
                        output_latex = _get_text(output_e,u'latex')
                        output_json = _get_text(output_e,u'json')
                        output_javascript = _get_text(output_e,u'javascript')

                        out_prompt_number = _get_int(output_e,u'prompt_number')
                        etype = _get_text(output_e,u'etype')
                        evalue = _get_text(output_e,u'evalue')
                        traceback = []
                        traceback_e = output_e.find(u'traceback')
                        if traceback_e is not None:
                            for frame_e in traceback_e.getiterator(u'frame'):
                                traceback.append(frame_e.text)
                        if len(traceback) == 0:
                            traceback = None
                        output = new_output(output_type=output_type,output_png=output_png,
                            output_text=output_text, output_svg=output_svg,
                            output_html=output_html, output_latex=output_latex,
                            output_json=output_json, output_javascript=output_javascript,
                            output_jpeg=output_jpeg, prompt_number=out_prompt_number,
                            etype=etype, evalue=evalue, traceback=traceback
                        )
                        outputs.append(output)
                    cc = new_code_cell(input=input,prompt_number=prompt_number,
                                       language=language,outputs=outputs,collapsed=collapsed)
                    cells.append(cc)
                if cell_e.tag == u'htmlcell':
                    source = _get_text(cell_e,u'source')
                    rendered = _get_text(cell_e,u'rendered')
                    cells.append(new_text_cell(u'html', source=source, rendered=rendered))
                if cell_e.tag == u'markdowncell':
                    source = _get_text(cell_e,u'source')
                    rendered = _get_text(cell_e,u'rendered')
                    cells.append(new_text_cell(u'markdown', source=source, rendered=rendered))
            ws = new_worksheet(name=wsname,cells=cells)
            worksheets.append(ws)

        nb = new_notebook(name=nbname,worksheets=worksheets,author=nbauthor,
            email=nbemail,license=nblicense,saved=nbsaved,created=nbcreated)
        return nb


class XMLWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        nb_e = ET.Element(u'notebook')
        _set_text(nb,u'name',nb_e,u'name')
        _set_text(nb,u'author',nb_e,u'author')
        _set_text(nb,u'email',nb_e,u'email')
        _set_text(nb,u'license',nb_e,u'license')
        _set_text(nb,u'created',nb_e,u'created')
        _set_text(nb,u'saved',nb_e,u'saved')
        _set_int(nb,u'nbformat',nb_e,u'nbformat')
        wss_e = ET.SubElement(nb_e,u'worksheets')
        for ws in nb.worksheets:
            ws_e = ET.SubElement(wss_e, u'worksheet')
            _set_text(ws,u'name',ws_e,u'name')
            cells_e = ET.SubElement(ws_e,u'cells')
            for cell in ws.cells:
                cell_type = cell.cell_type
                if cell_type == u'code':
                    cell_e = ET.SubElement(cells_e, u'codecell')
                    _set_text(cell,u'input',cell_e,u'input')
                    _set_text(cell,u'language',cell_e,u'language')
                    _set_int(cell,u'prompt_number',cell_e,u'prompt_number')
                    _set_bool(cell,u'collapsed',cell_e,u'collapsed')
                    outputs_e = ET.SubElement(cell_e, u'outputs')
                    for output in cell.outputs:
                        output_e = ET.SubElement(outputs_e, u'output')
                        _set_text(output,u'output_type',output_e,u'output_type')
                        _set_text(output,u'text',output_e,u'text')
                        _set_binary(output,u'png',output_e,u'png')
                        _set_binary(output,u'jpeg',output_e,u'jpeg')
                        _set_text(output,u'html',output_e,u'html')
                        _set_text(output,u'svg',output_e,u'svg')
                        _set_text(output,u'latex',output_e,u'latex')
                        _set_text(output,u'json',output_e,u'json')
                        _set_text(output,u'javascript',output_e,u'javascript')
                        _set_int(output,u'prompt_number',output_e,u'prompt_number')
                        _set_text(output,u'etype',output_e,u'etype')
                        _set_text(output,u'evalue',output_e,u'evalue')
                        if u'traceback' in output:
                            tb_e = ET.SubElement(output_e, u'traceback')
                            for frame in output.traceback:
                                frame_e = ET.SubElement(tb_e, u'frame')
                                frame_e.text = frame
                elif cell_type == u'html':
                    cell_e = ET.SubElement(cells_e, u'htmlcell')
                    _set_text(cell,u'source',cell_e,u'source')
                    _set_text(cell,u'rendered',cell_e,u'rendered')
                elif cell_type == u'markdown':
                    cell_e = ET.SubElement(cells_e, u'markdowncell')
                    _set_text(cell,u'source',cell_e,u'source')
                    _set_text(cell,u'rendered',cell_e,u'rendered')

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


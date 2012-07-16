"""Read and write notebook files as XML.

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

from base64 import encodestring, decodestring
import warnings
from xml.etree import ElementTree as ET

from .rwbase import NotebookReader, NotebookWriter
from .nbbase import (
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output,
    new_metadata
)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

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
        warnings.warn('The XML notebook format is no longer supported, '
                      'please convert your notebooks to JSON.', DeprecationWarning)
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

        md = new_metadata(name=nbname)
        nb = new_notebook(metadata=md,worksheets=worksheets)
        return nb

            
_reader = XMLReader()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook


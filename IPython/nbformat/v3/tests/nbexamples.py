# -*- coding: utf-8 -*-

import os
from base64 import encodestring

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output,
    new_metadata, new_author, new_heading_cell, nbformat, nbformat_minor
)

# some random base64-encoded *text*
png = encodestring(os.urandom(5)).decode('ascii')
jpeg = encodestring(os.urandom(6)).decode('ascii')

ws = new_worksheet(name='worksheet1')

ws.cells.append(new_text_cell(
    u'html',
    source='Some NumPy Examples',
    rendered='Some NumPy Examples'
))


ws.cells.append(new_code_cell(
    input='import numpy',
    prompt_number=1,
    collapsed=False
))

ws.cells.append(new_text_cell(
    u'markdown',
    source='A random array',
    rendered='A random array'
))

ws.cells.append(new_text_cell(
    u'raw',
    source='A random array',
))

ws.cells.append(new_heading_cell(
    u'My Heading',
    level=2
))

ws.cells.append(new_code_cell(
    input='a = numpy.random.rand(100)',
    prompt_number=2,
    collapsed=True
))
ws.cells.append(new_code_cell(
    input='a = 10\nb = 5\n',
    prompt_number=3,
))
ws.cells.append(new_code_cell(
    input='a = 10\nb = 5',
    prompt_number=4,
))

ws.cells.append(new_code_cell(
    input=u'print "ünîcødé"',
    prompt_number=3,
    collapsed=False,
    outputs=[new_output(
        output_type=u'pyout',
        output_text=u'<array a>',
        output_html=u'The HTML rep',
        output_latex=u'$a$',
        output_png=png,
        output_jpeg=jpeg,
        output_svg=u'<svg>',
        output_json=u'json data',
        output_javascript=u'var i=0;',
        prompt_number=3
    ),new_output(
        output_type=u'display_data',
        output_text=u'<array a>',
        output_html=u'The HTML rep',
        output_latex=u'$a$',
        output_png=png,
        output_jpeg=jpeg,
        output_svg=u'<svg>',
        output_json=u'json data',
        output_javascript=u'var i=0;'
    ),new_output(
        output_type=u'pyerr',
        ename=u'NameError',
        evalue=u'NameError was here',
        traceback=[u'frame 0', u'frame 1', u'frame 2']
    ),new_output(
        output_type=u'stream',
        output_text='foo\rbar\r\n'
    ),new_output(
        output_type=u'stream',
        stream='stderr',
        output_text='\rfoo\rbar\n'
    )]
))

authors = [new_author(name='Bart Simpson',email='bsimpson@fox.com',
           affiliation=u'Fox',url=u'http://www.fox.com')]
md = new_metadata(name=u'My Notebook',license=u'BSD',created=u'8601_goes_here',
    modified=u'8601_goes_here',gistid=u'21341231',authors=authors)

nb0 = new_notebook(
    worksheets=[ws, new_worksheet(name='worksheet2')],
    metadata=md
)

nb0_py = u"""# -*- coding: utf-8 -*-
# <nbformat>%i.%i</nbformat>

# <htmlcell>

# Some NumPy Examples

# <codecell>

import numpy

# <markdowncell>

# A random array

# <rawcell>

# A random array

# <headingcell level=2>

# My Heading

# <codecell>

a = numpy.random.rand(100)

# <codecell>

a = 10
b = 5

# <codecell>

a = 10
b = 5

# <codecell>

print "ünîcødé"

""" % (nbformat, nbformat_minor)



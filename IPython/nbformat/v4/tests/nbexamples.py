# -*- coding: utf-8 -*-

import os
from base64 import encodestring

from ..nbbase import (
    new_code_cell, new_heading_cell, new_markdown_cell, new_notebook,
    new_output, new_raw_cell
)

# some random base64-encoded *text*
png = encodestring(os.urandom(5)).decode('ascii')
jpeg = encodestring(os.urandom(6)).decode('ascii')

cells = []
cells.append(new_markdown_cell(
    source='Some NumPy Examples',
))


cells.append(new_code_cell(
    source='import numpy',
    prompt_number=1,
))

cells.append(new_markdown_cell(
    source='A random array',
))

cells.append(new_raw_cell(
    source='A random array',
))

cells.append(new_heading_cell(
    source=u'My Heading',
    level=2,
))

cells.append(new_code_cell(
    source='a = numpy.random.rand(100)',
    prompt_number=2,
))
cells.append(new_code_cell(
    source='a = 10\nb = 5\n',
    prompt_number=3,
))
cells.append(new_code_cell(
    source='a = 10\nb = 5',
    prompt_number=4,
))

cells.append(new_code_cell(
    source=u'print "ünîcødé"',
    prompt_number=3,
    outputs=[new_output(
        output_type=u'execute_result',
        mime_bundle={
            'text/plain': u'<array a>',
            'text/html': u'The HTML rep',
            'text/latex': u'$a$',
            'image/png': png,
            'image/jpeg': jpeg,
            'image/svg+xml': u'<svg>',
            'application/json': {
                'key': 'value'
            },
            'application/javascript': u'var i=0;'
        },
        prompt_number=3
    ),new_output(
        output_type=u'display_data',
        mime_bundle={
            'text/plain': u'<array a>',
            'text/html': u'The HTML rep',
            'text/latex': u'$a$',
            'image/png': png,
            'image/jpeg': jpeg,
            'image/svg+xml': u'<svg>',
            'application/json': {
                'key': 'value'
            },
            'application/javascript': u'var i=0;'
        },
    ),new_output(
        output_type=u'error',
        ename=u'NameError',
        evalue=u'NameError was here',
        traceback=[u'frame 0', u'frame 1', u'frame 2']
    ),new_output(
        output_type=u'stream',
        text='foo\rbar\r\n'
    ),new_output(
        output_type=u'stream',
        stream='stderr',
        text='\rfoo\rbar\n'
    )]
))

nb0 = new_notebook(cells=cells,
    metadata={
        'language': 'python',
    }
)



# -*- coding: utf-8 -*-

import os
from base64 import encodestring

from ..nbbase import (
    new_code_cell, new_markdown_cell, new_notebook,
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
    execution_count=1,
))

cells.append(new_markdown_cell(
    source='A random array',
))

cells.append(new_raw_cell(
    source='A random array',
))

cells.append(new_markdown_cell(
    source=u'## My Heading',
))

cells.append(new_code_cell(
    source='a = numpy.random.rand(100)',
    execution_count=2,
))
cells.append(new_code_cell(
    source='a = 10\nb = 5\n',
    execution_count=3,
))
cells.append(new_code_cell(
    source='a = 10\nb = 5',
    execution_count=4,
))

cells.append(new_code_cell(
    source=u'print "ünîcødé"',
    execution_count=3,
    outputs=[new_output(
        output_type=u'execute_result',
        data={
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
        execution_count=3
    ),new_output(
        output_type=u'display_data',
        data={
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
        name='stderr',
        text='\rfoo\rbar\n'
    )]
))

nb0 = new_notebook(cells=cells,
    metadata={
        'language': 'python',
    }
)



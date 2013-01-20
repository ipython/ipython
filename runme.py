#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function
import sys
import io
from converters.template import *

template_file = sys.argv[1]

if template_file.startswith('latex'):
    tex_environement=True
else:
    tex_environement=False

C = ConverterTemplate(tplfile=sys.argv[1], tex_environement=tex_environement)
C.read(sys.argv[2])

output,rest = C.convert()

print(output.encode('utf-8'))

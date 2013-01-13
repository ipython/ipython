#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function
import sys
import io
from converters.template import *
C = ConverterTemplate(tplfile=sys.argv[1])
C.read(sys.argv[2])

print(C.convert().encode('utf-8'))

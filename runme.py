#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function
import sys
import io
from converters.template import *
C = ConverterTemplate(tplfile=sys.argv[1])
C.read('tests/ipynbref/IntroNumPy.orig.ipynb')

print(C.convert().encode('utf-8'))

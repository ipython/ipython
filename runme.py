#!/usr/bin/env python
# coding: utf-8
import sys
import io
from converters.template import *
C = ConverterTemplate(tplfile=sys.argv[1])
C.read('tests/ipynbref/IntroNumPy.orig.ipynb')

print C.convert()

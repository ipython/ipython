# coding: utf-8
import sys
import io
from converters.template import *
C = ConverterTemplate(tplfile=sys.argv[1])
C.read('tests/ipynbref/IntroNumPy.orig.ipynb')

S = C.convert()
with io.open('temp.txt','w') as f:
    f.write(S)

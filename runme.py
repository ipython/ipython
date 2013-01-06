# coding: utf-8
from converters.template import *
C = ConverterTemplate()
C.read('tests/ipynbref/IntroNumPy.orig.ipynb')
S = C.convert()
with open('temp.txt','w') as f:
    f.write(S)

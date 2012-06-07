from nbconvert import ConverterNotebook
import nose.tools as nt
import os

fname = 'tests/test.ipynb'
outbase1 = 'newtest1'
outbase2 = 'newtest2'

def test_roundtrip():
    converter = ConverterNotebook(fname, outbase1)
    converter.render()

    converter2 = ConverterNotebook(outbase1+'.ipynb', outbase2)
    converter2.render()

    s1 = open(outbase1+'.ipynb', 'rb').read()
    s2 = open(outbase2+'.ipynb', 'rb').read()
    nt.assert_true(s1.replace(outbase1, outbase2) == s2)
    os.remove(outbase1+'.ipynb')
    os.remove(outbase2+'.ipynb')

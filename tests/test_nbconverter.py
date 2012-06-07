from nbconvert import ConverterNotebook
import nose.tools as nt
import os, json

fname = 'tests/test.ipynb'
outbase1 = 'newtest1'
outbase2 = 'test' # will output to ./test.ipynb

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

    s0 = json.dumps(json.load(file(fname)), indent=1, sort_keys=True)
    nt.assert_true(s0 == s2)


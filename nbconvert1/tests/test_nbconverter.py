from converters import ConverterNotebook
import nose.tools as nt
import os
import json
import shutil
import tempfile


# name = os.path.join(os.path.dirname(os.path.abspath(__file__), test.ipynb')
outbase1 = 'newtest1'
outbase2 = 'test'  # will output to ./test.ipynb


def test_roundtrip():
    directory = tempfile.mkdtemp()
    out1 = os.path.join(directory, outbase1)
    out2 = os.path.join(directory, outbase2)
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'test.ipynb')
    converter = ConverterNotebook(infile=fname, outbase=out1)
    converter.render()
    converter2 = ConverterNotebook(infile=out1 + '.ipynb', outbase=out2)
    converter2.render()

    with open(out1 + '.ipynb', 'rb') as f:
        s1 = f.read()
    with open(out2 + '.ipynb', 'rb') as f:
        s2 = f.read()

    nt.assert_true(s1.replace(outbase1, outbase2) == s2)
    shutil.rmtree(directory)
    s0 = json.dumps(json.load(file(fname)), indent=1, sort_keys=True)
    nt.assert_true(s0 == s2)

from nbconvert import ConverterRST
import nose.tools as nt

import os
import glob

def clean_dir():
    "Remove .rst files created during conversion"
    map(os.remove, glob.glob("*.rst"))
    map(os.remove, glob.glob("*.png"))


@nt.with_setup(clean_dir, clean_dir)
def test_simple():
    fname = 'test.ipynb'
    c = ConverterRST(fname)
    f = c.render()
    nt.assert_true('rst' in f, 'changed file extension to rst')


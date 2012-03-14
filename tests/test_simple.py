from nbconvert import ConverterRST, main
import nose.tools as nt

import os
import glob

fname = 'tests/test.ipynb'
out_fname = 'tests/test.rst'


def clean_dir():
    "Remove .rst files created during conversion"
    map(os.remove, glob.glob("./tests/*.rst"))
    map(os.remove, glob.glob("./tests/*.png"))


@nt.with_setup(clean_dir, clean_dir)
def test_simple():
    c = ConverterRST(fname)
    f = c.render()
    nt.assert_true('rst' in f, 'changed file extension to rst')


@nt.with_setup(clean_dir, clean_dir)
def test_main():
    """
    Test main entry point
    """
    main(fname)
    nt.assert_true(os.path.exists(out_fname))

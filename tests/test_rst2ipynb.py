import os
import errno
import subprocess
import nose.tools as nt

test_rst_fname = 'tests/tutorial.rst.ref'
ref_ipynb_fname = 'tests/tutorial.ipynb.ref'
test_generate_ipynb_fname = 'tests/tutorial.ipynb'


def clean_dir():
    "Remove generated ipynb file created during conversion"
    try:
        os.unlink(test_generate_ipynb_fname)
    except OSError, e:
        if e.errno != errno.ENOENT:
            raise


@nt.with_setup(clean_dir, clean_dir)
def test_command_line():
    with open(ref_ipynb_fname, 'rb') as f:
        ref_output = f.read()
    output = subprocess.check_output(['./rst2ipynb.py', test_rst_fname])
    nt.assert_equal(ref_output, output)

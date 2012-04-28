import os
import errno
import os.path
import subprocess
import nose.tools as nt

test_rst_fname = os.path.join('tests', 'tutorial.rst.ref')
ref_ipynb_fname = os.path.join('tests', 'tutorial.ipynb.ref')
test_generate_ipynb_fname = os.path.join('tests', 'tutorial.ipynb')


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
    proc = subprocess.Popen(['./rst2ipynb.py', test_rst_fname],
                            stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    nt.assert_equal(ref_output, output)

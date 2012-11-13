import errno
import os.path
import subprocess
import nose.tools as nt

test_rst_fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'tutorial.rst.ref')
ref_ipynb_fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'tutorial.ipynb.ref')


def test_command_line():
    with open(ref_ipynb_fname, 'rb') as f:
        ref_output = f.read()
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(tests_dir)
    rst2ipynb_script = os.path.join(root_dir, 'rst2ipynb.py')
    proc = subprocess.Popen([rst2ipynb_script, test_rst_fname],
                            stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    nt.assert_equal(ref_output.strip('\n'), output.strip('\n'))

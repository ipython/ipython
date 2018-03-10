"""Tests for the line-based transformers in IPython.core.inputtransformer2

Line-based transformers are the simpler ones; token-based transformers are
more complex.
"""
import nose.tools as nt

from IPython.core import inputtransformer2 as ipt2

SIMPLE = ("""\
%%foo arg
body 1
body 2
""", """\
get_ipython().run_cell_magic('foo', 'arg', 'body 1\\nbody 2\\n')
""")

def test_cell_magic():
    for sample, expected in [SIMPLE]:
        nt.assert_equal(ipt2.cell_magic(sample.splitlines(keepends=True)),
                        expected.splitlines(keepends=True))

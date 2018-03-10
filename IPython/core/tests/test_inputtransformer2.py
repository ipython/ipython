import nose.tools as nt

from IPython.core import inputtransformer2
from IPython.core.inputtransformer2 import make_tokens_by_line

MULTILINE_MAGIC_ASSIGN = ("""\
a = f()
b = %foo \\
  bar
g()
""".splitlines(keepends=True), """\
a = f()
b = get_ipython().run_line_magic('foo', '   bar')
g()
""".splitlines(keepends=True))

MULTILINE_SYSTEM_ASSIGN = ("""\
a = f()
b = !foo \\
  bar
g()
""".splitlines(keepends=True), """\
a = f()
b = get_ipython().getoutput('foo   bar')
g()
""".splitlines(keepends=True))

def test_find_assign_magic():
    tbl = make_tokens_by_line(MULTILINE_MAGIC_ASSIGN[0])
    nt.assert_equal(inputtransformer2.MagicAssign.find(tbl), (2, 4))

    tbl = make_tokens_by_line(MULTILINE_SYSTEM_ASSIGN[0]) # Nothing to find
    nt.assert_equal(inputtransformer2.MagicAssign.find(tbl), None)

def test_transform_assign_magic():
    res = inputtransformer2.MagicAssign.transform(MULTILINE_MAGIC_ASSIGN[0], (2, 4))
    nt.assert_equal(res, MULTILINE_MAGIC_ASSIGN[1])

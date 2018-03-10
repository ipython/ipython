import nose.tools as nt

from IPython.core import inputtransformer2 as ipt2
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
b = get_ipython().getoutput('foo    bar')
g()
""".splitlines(keepends=True))

def test_continued_line():
    lines = MULTILINE_MAGIC_ASSIGN[0]
    nt.assert_equal(ipt2.find_end_of_continued_line(lines, 1), 2)

    nt.assert_equal(ipt2.assemble_continued_line(lines, (1, 5), 2), "foo    bar")

def test_find_assign_magic():
    tbl = make_tokens_by_line(MULTILINE_MAGIC_ASSIGN[0])
    nt.assert_equal(ipt2.MagicAssign.find(tbl), (2, 4))

    tbl = make_tokens_by_line(MULTILINE_SYSTEM_ASSIGN[0])  # Nothing to find
    nt.assert_equal(ipt2.MagicAssign.find(tbl), None)

def test_transform_assign_magic():
    res = ipt2.MagicAssign.transform(MULTILINE_MAGIC_ASSIGN[0], (2, 4))
    nt.assert_equal(res, MULTILINE_MAGIC_ASSIGN[1])

def test_find_assign_system():
    tbl = make_tokens_by_line(MULTILINE_SYSTEM_ASSIGN[0])
    nt.assert_equal(ipt2.SystemAssign.find(tbl), (2, 4))

    tbl = make_tokens_by_line(["a =  !ls\n"])
    nt.assert_equal(ipt2.SystemAssign.find(tbl), (1, 5))

    tbl = make_tokens_by_line(["a=!ls\n"])
    nt.assert_equal(ipt2.SystemAssign.find(tbl), (1, 2))

    tbl = make_tokens_by_line(MULTILINE_MAGIC_ASSIGN[0])  # Nothing to find
    nt.assert_equal(ipt2.SystemAssign.find(tbl), None)

def test_transform_assign_system():
    res = ipt2.SystemAssign.transform(MULTILINE_SYSTEM_ASSIGN[0], (2, 4))
    nt.assert_equal(res, MULTILINE_SYSTEM_ASSIGN[1])

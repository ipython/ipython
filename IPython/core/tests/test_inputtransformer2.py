import nose.tools as nt

from IPython.core import inputtransformer2 as ipt2
from IPython.core.inputtransformer2 import make_tokens_by_line

MULTILINE_MAGIC = ("""\
a = f()
%foo \\
bar
g()
""".splitlines(keepends=True), """\
a = f()
get_ipython().run_line_magic('foo', ' bar')
g()
""".splitlines(keepends=True))

INDENTED_MAGIC = ("""\
for a in range(5):
    %ls
""".splitlines(keepends=True), """\
for a in range(5):
    get_ipython().run_line_magic('ls', '')
""".splitlines(keepends=True))

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

AUTOCALL_QUOTE = (
    [",f 1 2 3\n"],
    ['f("1", "2", "3")\n']
)

AUTOCALL_QUOTE2 = (
    [";f 1 2 3\n"],
    ['f("1 2 3")\n']
)

AUTOCALL_PAREN = (
    ["/f 1 2 3\n"],
    ['f(1, 2, 3)\n']
)

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

def test_find_magic_escape():
    tbl = make_tokens_by_line(MULTILINE_MAGIC[0])
    nt.assert_equal(ipt2.EscapedCommand.find(tbl), (2, 0))

    tbl = make_tokens_by_line(INDENTED_MAGIC[0])
    nt.assert_equal(ipt2.EscapedCommand.find(tbl), (2, 4))

    tbl = make_tokens_by_line(MULTILINE_MAGIC_ASSIGN[0])  # Shouldn't find a = %foo
    nt.assert_equal(ipt2.EscapedCommand.find(tbl), None)

def test_transform_magic_escape():
    res = ipt2.EscapedCommand.transform(MULTILINE_MAGIC[0], (2, 0))
    nt.assert_equal(res, MULTILINE_MAGIC[1])

    res = ipt2.EscapedCommand.transform(INDENTED_MAGIC[0], (2, 4))
    nt.assert_equal(res, INDENTED_MAGIC[1])

def test_find_autocalls():
    for sample, _ in [AUTOCALL_QUOTE, AUTOCALL_QUOTE2, AUTOCALL_PAREN]:
        print("Testing %r" % sample)
        tbl = make_tokens_by_line(sample)
        nt.assert_equal(ipt2.EscapedCommand.find(tbl), (1, 0))

def test_transform_autocall():
    for sample, expected in [AUTOCALL_QUOTE, AUTOCALL_QUOTE2, AUTOCALL_PAREN]:
        print("Testing %r" % sample)
        res = ipt2.EscapedCommand.transform(sample, (1, 0))
        nt.assert_equal(res, expected)

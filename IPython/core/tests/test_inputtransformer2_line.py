"""Tests for the line-based transformers in IPython.core.inputtransformer2

Line-based transformers are the simpler ones; token-based transformers are
more complex. See test_inputtransformer2 for tests for token-based transformers.
"""

from IPython.core import inputtransformer2 as ipt2

CELL_MAGIC = ("""\
%%foo arg
body 1
body 2
""", """\
get_ipython().run_cell_magic('foo', 'arg', 'body 1\\nbody 2\\n')
""")

def test_cell_magic():
    for sample, expected in [CELL_MAGIC]:
        assert ipt2.cell_magic(sample.splitlines(keepends=True)) == expected.splitlines(
            keepends=True
        )

CLASSIC_PROMPT = ("""\
>>> for a in range(5):
...     print(a)
""", """\
for a in range(5):
    print(a)
""")

CLASSIC_PROMPT_L2 = ("""\
for a in range(5):
...     print(a)
...     print(a ** 2)
""", """\
for a in range(5):
    print(a)
    print(a ** 2)
""")

def test_classic_prompt():
    for sample, expected in [CLASSIC_PROMPT, CLASSIC_PROMPT_L2]:
        assert ipt2.classic_prompt(
            sample.splitlines(keepends=True)
        ) == expected.splitlines(keepends=True)

IPYTHON_PROMPT = ("""\
In [1]: for a in range(5):
   ...:     print(a)
""", """\
for a in range(5):
    print(a)
""")

IPYTHON_PROMPT_L2 = ("""\
for a in range(5):
   ...:     print(a)
   ...:     print(a ** 2)
""", """\
for a in range(5):
    print(a)
    print(a ** 2)
""")


IPYTHON_PROMPT_VI_INS = (
    """\
[ins] In [11]: def a():
          ...:     123
          ...:
          ...: 123
""",
    """\
def a():
    123

123
""",
)

IPYTHON_PROMPT_VI_NAV = (
    """\
[nav] In [11]: def a():
          ...:     123
          ...:
          ...: 123
""",
    """\
def a():
    123

123
""",
)

AUTOBALANCE = (
    ("(1+1)/2", "(1+1)/2"),
    ("1+1)/2", "(1+1)/2"),
    ("1+1/(2+3", "1+1/(2+3)"),
    ("i+1)/2 for i in range(10)]", "[(i+1)/2 for i in range(10)]"),
)


def test_ipython_prompt():
    for sample, expected in [
        IPYTHON_PROMPT,
        IPYTHON_PROMPT_L2,
        IPYTHON_PROMPT_VI_INS,
        IPYTHON_PROMPT_VI_NAV,
    ]:
        assert ipt2.ipython_prompt(
            sample.splitlines(keepends=True)
        ) == expected.splitlines(keepends=True)


INDENT_SPACES = ("""\
     if True:
        a = 3
""", """\
if True:
   a = 3
""")

INDENT_TABS = ("""\
\tif True:
\t\tb = 4
""", """\
if True:
\tb = 4
""")

def test_leading_indent():
    for sample, expected in [INDENT_SPACES, INDENT_TABS]:
        assert ipt2.leading_indent(
            sample.splitlines(keepends=True)
        ) == expected.splitlines(keepends=True)


INDENT_SPACES_COMMENT = (
    """\
    # comment
if True:
    a = 3
""",
    """\
    # comment
if True:
   a = 3
""",
)

INDENT_TABS_COMMENT = (
    """\
\t# comment
if True:
\tb = 4
""",
    """\
\t# comment
if True:
\tb = 4
""",
)


def test_leading_indent():
    for sample, expected in [INDENT_SPACES, INDENT_TABS]:
        assert ipt2.leading_indent(
            sample.splitlines(keepends=True)
        ) == expected.splitlines(keepends=True)

LEADING_EMPTY_LINES = ("""\
    \t

if True:
    a = 3

b = 4
""", """\
if True:
    a = 3

b = 4
""")

ONLY_EMPTY_LINES = ("""\
    \t

""", """\
    \t

""")

def test_leading_empty_lines():
    for sample, expected in [LEADING_EMPTY_LINES, ONLY_EMPTY_LINES]:
        assert ipt2.leading_empty_lines(
            sample.splitlines(keepends=True)
        ) == expected.splitlines(keepends=True)

CRLF_MAGIC = ([
    "%%ls\r\n"
], [
    "get_ipython().run_cell_magic('ls', '', '')\n"
])

def test_crlf_magic():
    for sample, expected in [CRLF_MAGIC]:
        assert ipt2.cell_magic(sample) == expected


def test_autobalance_no_changes():
    autobalance = ipt2.AutoBalancer(default=False)
    for sample, _ in AUTOBALANCE:
        assert autobalance([sample]) == [sample]


def test_autobalance_changes():
    autobalance = ipt2.AutoBalancer(default=True)
    for sample, expected in AUTOBALANCE:
        assert autobalance([sample]) == [expected]

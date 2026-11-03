"""Tests for the line-based transformers in IPython.core.inputtransformer2

Line-based transformers are the simpler ones; token-based transformers are
more complex. See test_inputtransformer2 for tests for token-based transformers.
"""

import pytest

from IPython.core import inputtransformer2 as ipt2

CELL_MAGIC = (
    """\
%%foo arg
body 1
body 2
""",
    """\
get_ipython().run_cell_magic('foo', 'arg', 'body 1\\nbody 2\\n')
""",
)


def test_cell_magic():
    sample, expected = CELL_MAGIC
    assert ipt2.cell_magic(sample.splitlines(keepends=True)) == expected.splitlines(keepends=True)


CLASSIC_PROMPT = (
    """\
>>> for a in range(5):
...     print(a)
""",
    """\
for a in range(5):
    print(a)
""",
)

CLASSIC_PROMPT_L2 = (
    """\
for a in range(5):
...     print(a)
...     print(a ** 2)
""",
    """\
for a in range(5):
...     print(a)
...     print(a ** 2)
""",
)

CLASSIC_PROMPT_L3 = (
    """\
>>> \"\"\"
... This code is inside a triple-quoted string.
... >>> for a in range(5):
... ...     print(a)
... \"\"\"
>>> for a in range(5):
...     print(a)
""",
    """\
>>> \"\"\"
... This code is inside a triple-quoted string.
... >>> for a in range(5):
... ...     print(a)
... \"\"\"
for a in range(5):
    print(a)
""",
)

CLASSIC_PROMPT_DEDENT_SINGLE_LINE = (
    ">>>     print(1)\n",
    "print(1)\n",
)

CLASSIC_PROMPT_DEDENT_LEADING_WS = (
    "    >>>     print(1)\n",
    "print(1)\n",
)

CLASSIC_PROMPT_MULTILINE_DOCTEST = (
    """\
>>> for i in range(2):
...     print(i)
""",
    """\
for i in range(2):
    print(i)
""",
)

CLASSIC_PROMPT_STANDALONE_CONTINUATION = (
    "...     print(1)\n",
    "...     print(1)\n",
)


CLASSIC_PROMPT_DOCTEST_MULTILINE_STRING_ARG = (
    ">>> source = (\n"
    "...     r'''\n"
    "...     hello\n"
    "...\n"
    "...     world\n"
    "...     ''')\n",
    "source = (\n"
    "    r'''\n"
    "    hello\n"
    "\n"
    "    world\n"
    "    ''')\n",
)

CLASSIC_PROMPT_XDOCTEST_MULTILINE_STRING_ARG = (
    ">>> source = (\n"
    ">>>     r'''\n"
    ">>>     hello\n"
    ">>>\n"
    ">>>     world\n"
    ">>>     ''')\n",
    "source = (\n"
    "    r'''\n"
    "    hello\n"
    "\n"
    "    world\n"
    "    ''')\n",
)

CLASSIC_PROMPT_INDENTED_LITERAL_MULTILINE_STRING = (
    "def example():\n"
    "    '''\n"
    ">>> literal_doctest_prompt()\n"
    "... literal_continuation_prompt()\n"
    "    '''\n",
    "def example():\n"
    "    '''\n"
    ">>> literal_doctest_prompt()\n"
    "... literal_continuation_prompt()\n"
    "    '''\n",
)


@pytest.mark.parametrize(
    "sample,expected",
    [
        CLASSIC_PROMPT,
        CLASSIC_PROMPT_L2,
        CLASSIC_PROMPT_L3,
        CLASSIC_PROMPT_DEDENT_SINGLE_LINE,
        CLASSIC_PROMPT_DEDENT_LEADING_WS,
        CLASSIC_PROMPT_MULTILINE_DOCTEST,
        CLASSIC_PROMPT_STANDALONE_CONTINUATION,
        CLASSIC_PROMPT_DOCTEST_MULTILINE_STRING_ARG,
        CLASSIC_PROMPT_XDOCTEST_MULTILINE_STRING_ARG,
        CLASSIC_PROMPT_INDENTED_LITERAL_MULTILINE_STRING,
    ],
)
def test_classic_prompt(sample, expected):
    assert ipt2.classic_prompt(sample.splitlines(keepends=True)) == expected.splitlines(
        keepends=True
    )


IPYTHON_PROMPT = (
    """\
In [1]: for a in range(5):
   ...:     print(a)
""",
    """\
for a in range(5):
    print(a)
""",
)

IPYTHON_PROMPT_L2 = (
    """\
for a in range(5):
   ...:     print(a)
   ...:     print(a ** 2)
""",
    """\
for a in range(5):
    print(a)
    print(a ** 2)
""",
)


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


@pytest.mark.parametrize("sample,expected", [
    IPYTHON_PROMPT,
    IPYTHON_PROMPT_L2,
    IPYTHON_PROMPT_VI_INS,
    IPYTHON_PROMPT_VI_NAV,
])
def test_ipython_prompt(sample, expected):
    assert ipt2.ipython_prompt(sample.splitlines(keepends=True)) == expected.splitlines(keepends=True)


INDENT_SPACES = (
    """\
     if True:
        a = 3
""",
    """\
if True:
   a = 3
""",
)

INDENT_TABS = (
    """\
\tif True:
\t\tb = 4
""",
    """\
if True:
\tb = 4
""",
)


@pytest.mark.parametrize("sample,expected", [INDENT_SPACES, INDENT_TABS])
def test_leading_indent(sample, expected):
    assert ipt2.leading_indent(sample.splitlines(keepends=True)) == expected.splitlines(keepends=True)


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


INDENTED_CODE_WITH_ALIGNED_COMMENT = (
    """\
    # comment
    x = 1
    print(x)
""",
    """\
# comment
x = 1
print(x)
""",
)


@pytest.mark.parametrize(
    "sample, expected",
    [INDENT_SPACES_COMMENT, INDENT_TABS_COMMENT, INDENTED_CODE_WITH_ALIGNED_COMMENT],
)
def test_leading_indent_comment(sample, expected):
    assert ipt2.leading_indent(sample.splitlines(keepends=True)) == expected.splitlines(
        keepends=True
    )


LEADING_EMPTY_LINES = (
    """\
    \t

if True:
    a = 3

b = 4
""",
    """\
if True:
    a = 3

b = 4
""",
)

ONLY_EMPTY_LINES = (
    """\
    \t

""",
    """\
    \t

""",
)


@pytest.mark.parametrize("sample,expected", [LEADING_EMPTY_LINES, ONLY_EMPTY_LINES])
def test_leading_empty_lines(sample, expected):
    assert ipt2.leading_empty_lines(sample.splitlines(keepends=True)) == expected.splitlines(keepends=True)


COMMENT_THEN_CELL_MAGIC = (
    """\
# setup
%%foo arg
body
""",
    """\
%%foo arg
body
""",
)

COMMENTS_BLANKS_THEN_CELL_MAGIC = (
    """\
# setup

# more
%%foo
body
""",
    """\
%%foo
body
""",
)

COMMENT_THEN_PYTHON = (
    """\
# setup
x = 1
""",
    """\
# setup
x = 1
""",
)

COMMENT_THEN_LINE_MAGIC = (
    """\
# setup
%foo
""",
    """\
# setup
%foo
""",
)

ONLY_COMMENTS = (
    """\
# only
# comments
""",
    """\
# only
# comments
""",
)

CELL_MAGIC_ALREADY_FIRST = (
    """\
%%foo arg
body 1
body 2
""",
    """\
%%foo arg
body 1
body 2
""",
)


@pytest.mark.parametrize(
    "sample,expected",
    [
        COMMENT_THEN_CELL_MAGIC,
        COMMENTS_BLANKS_THEN_CELL_MAGIC,
        COMMENT_THEN_PYTHON,
        COMMENT_THEN_LINE_MAGIC,
        ONLY_COMMENTS,
        CELL_MAGIC_ALREADY_FIRST,
    ],
)
def test_leading_comment_lines(sample, expected):
    assert ipt2.leading_comment_lines(
        sample.splitlines(keepends=True)
    ) == expected.splitlines(keepends=True)


def test_transform_cell_comment_before_cell_magic():
    mgr = ipt2.TransformerManager()
    out = mgr.transform_cell("# setup\n%%foo arg\nbody 1\nbody 2\n")
    assert out == "get_ipython().run_cell_magic('foo', 'arg', 'body 1\\nbody 2\\n')\n"


CRLF_MAGIC = (["%%ls\r\n"], ["get_ipython().run_cell_magic('ls', '', '')\n"])


def test_crlf_magic():
    sample, expected = CRLF_MAGIC
    assert ipt2.cell_magic(sample) == expected

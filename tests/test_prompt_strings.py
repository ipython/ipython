"""Prompt removal must preserve string values as well as valid Python syntax."""

import sys
from unittest.mock import patch

import pytest

from IPython.core.inputtransformer2 import TransformerManager, classic_prompt
from IPython.core.interactiveshell import InteractiveShell


PREFIXES = ["", "r", "u", "b", "br", "rb", "f", "fr", "rf", "R", "F", "BR"]
CONTEXTS = [
    "result = {literal}\n",
    "result: object = {literal}\n",
    "result = (\n    {literal}\n)\n",
    "result = [\n    {literal}\n][0]\n",
    "result = dict(value={literal})['value']\n",
    "def get_value():\n    return {literal}\nresult = get_value()\n",
    "result = (lambda: {literal})()\n",
]


def paste(source, style):
    if style == "plain":
        return source
    lines = source.splitlines(keepends=True)
    return (
        ">>> "
        + lines[0]
        + "".join(
            (">>> " if style == "xdoctest" else "... ") + line for line in lines[1:]
        )
    )


def assert_transform(sample, expected):
    transformed = TransformerManager().transform_cell(sample)
    assert transformed == expected
    expected_ns, actual_ns = {}, {}
    exec(compile(expected, "<expected>", "exec"), expected_ns)
    exec(compile(transformed, "<transformed>", "exec"), actual_ns)
    if "result" in expected_ns:
        assert actual_ns["result"] == expected_ns["result"]


@pytest.mark.parametrize("quote", ["'''", '"""'])
@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("context", CONTEXTS)
@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_contexts(quote, prefix, context, style):
    literal = prefix + quote + "\n>>> literal\n... tail\n" + quote
    source = context.format(literal=literal)
    assert_transform(paste(source, style), source)


@pytest.mark.parametrize("quote", ["'''", '"""'])
@pytest.mark.parametrize("marker", [">>>", "..."])
@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_originals(quote, marker, style):
    source = f"{quote}\n{marker}\n{quote}\n"
    transformed = TransformerManager().transform_cell(paste(source, style))
    assert transformed == source
    assert eval(compile(transformed, "<literal>", "eval")) == f"\n{marker}\n"


@pytest.mark.parametrize(
    "literal",
    [
        "'''\n>>> \\''' still inside\n... tail\n'''",
        "r'''\n>>> \\''' still inside\n... tail\n'''",
        "'''\n>>> end\\\\'''",
        "'''\n>>> \"\"\" different delimiter\n... tail\n'''",
        '"first\\\n>>> second\\\n... third"',
        'f"""\n>>> {1 + 2}\n... {"value"}\n"""',
        'f"""\n>>> {dict(value=1)["value"]}\n... tail\n"""',
    ],
)
@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_lexical_edges(literal, style):
    source = f"result = {literal}\n"
    assert_transform(paste(source, style), source)


@pytest.mark.parametrize(
    "source",
    [
        "# '''\nresult = 1\n",
        "marker = \"'''\"\nresult = 1\n",
        "# '''\nresult = '''\n>>> value\n... tail\n'''\n",
        'marker = "\'\'\'"\nresult = """\n>>> value\n... tail\n"""\n',
        '"""one line"""\nresult = 1\n',
        'def f():\n    """\n    >>> f()\n    ... 1\n    """\n    return 1\nresult = f()\n',
        "result = [\n    1,\n\n    2,\n]\n",
    ],
)
@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_false_delimiters_and_controls(source, style):
    assert_transform(paste(source, style), source)


@pytest.mark.parametrize("quote", ["'''", '"""'])
def test_prompt_string_mixed_paste(quote):
    literal = f"value = {quote}\n>>> literal\n... tail\n{quote}\n"
    assert_transform(literal + ">>> result = value\n", literal + "result = value\n")
    source = ">>> x = (\n    " + quote + "\n>>> literal\n... tail\n" + quote + ")\n"
    assert_transform(source, source.removeprefix(">>> "))


@pytest.mark.parametrize("prefix", ["", "r", "f"])
@pytest.mark.parametrize("quote", ["'''", '"""'])
def test_prompt_string_incomplete(prefix, quote):
    source = f"result = {prefix}{quote}\n>>> literal\n... tail\n"
    assert classic_prompt(source.splitlines(keepends=True)) == source.splitlines(
        keepends=True
    )
    assert TransformerManager().check_complete(source)[0] == "incomplete"


@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
@pytest.mark.skipif(
    sys.version_info < (3, 14), reason="Template strings require Python 3.14"
)
def test_prompt_string_template(style):
    source = 'result = t"""\n>>> {1}\n... tail\n"""\n'
    transformed = TransformerManager().transform_cell(paste(source, style))
    assert transformed == source
    ns = {}
    exec(transformed, ns)
    assert ns["result"].strings == ("\n>>> ", "\n... tail\n")


@pytest.mark.parametrize("command", ["!echo don't", "%time print('hello')", "x = 0b2"])
def test_prompt_string_after_non_python_input(command):
    literal = 'result = """\n>>> literal\n... tail\n"""\n'
    sample = f">>> {command}\n" + literal + ">>> result\n"
    expected = command + "\n" + literal + "result\n"
    assert "".join(classic_prompt(sample.splitlines(keepends=True))) == expected


@pytest.mark.parametrize("prefix", ["", "r", "f"])
def test_prompt_string_incomplete_backslash(prefix):
    source = f'result = {prefix}"first\\\n>>> second\\\n'
    assert classic_prompt(source.splitlines(keepends=True)) == source.splitlines(
        keepends=True
    )


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_line_endings(newline, style):
    source = 'result = """\n>>> value\n... tail\n"""\n'.replace("\n", newline)
    assert_transform(paste(source, style), source)


def test_prompt_string_shell_syntax():
    source = ">>> !echo don't\n"
    assert (
        TransformerManager().transform_cell(source)
        == 'get_ipython().system("echo don\'t")\n'
    )


@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_after_even_backslashes(style):
    source = "result = '''\n>>> end\\\\'''\nresult += 'done'\n"
    assert_transform(paste(source, style), source)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 701 requires Python 3.12")
@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_nested_fstring(style):
    source = 'result = f"""\n>>> {f"""nested\n... value\n"""}\n... tail\n"""\n'
    assert_transform(paste(source, style), source)


def test_prompt_string_mixed_paste_keeps_block_indentation():
    source = 'def f():\n    value = """\n>>> literal\n... tail\n"""\n'
    sample = source + ">>>     return value\n"
    expected = source + "    return value\n"
    assert_transform(sample, expected)


@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_indented_cell(style):
    source = 'result = """\n>>> value\n... tail\n"""\n'
    sample = "".join(
        "    " + line for line in paste(source, style).splitlines(keepends=True)
    )
    assert_transform(sample, source)


@pytest.mark.parametrize("style", ["plain", "doctest", "xdoctest"])
def test_prompt_string_run_cell(style):
    source = '_prompt_string_result = f"""\n>>> {1 + 2}\n... tail\n"""\n'
    shell = InteractiveShell.instance()
    with patch.dict(shell.user_ns):
        result = shell.run_cell(paste(source, style))
        assert result.success
        assert shell.user_ns["_prompt_string_result"] == "\n>>> 3\n... tail\n"

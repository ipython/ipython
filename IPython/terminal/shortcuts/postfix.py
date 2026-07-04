"""Postfix completions for the terminal prompt."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import ast
import re
import tokenize
from dataclasses import dataclass
from io import StringIO
from typing import Callable

from prompt_toolkit.key_binding import KeyPressEvent

from IPython.core.getipython import get_ipython

from .filters import pass_through


@dataclass(frozen=True)
class PostfixExpansion:
    text: str
    start_position: int


@dataclass(frozen=True)
class PostfixCompletion:
    key: str
    prefix: str
    expansion: PostfixExpansion

    @property
    def start_position(self) -> int:
        return self.expansion.start_position


PostfixTemplate = Callable[[str, str], str]


def _block(keyword: str) -> PostfixTemplate:
    def template(expr: str, indent: str) -> str:
        return f"{keyword} {expr}:\n{indent}    "

    return template


def _call(function: str) -> PostfixTemplate:
    def template(expr: str, indent: str) -> str:
        return f"{function}({expr})"

    return template


POSTFIX_TEMPLATES: dict[str, PostfixTemplate] = {
    "not": lambda expr, indent: f"not {expr}",
    "par": lambda expr, indent: f"({expr})",
    "return": lambda expr, indent: f"return {expr}",
    "if": _block("if"),
    "while": _block("while"),
    "print": _call("print"),
    "len": _call("len"),
    "raise": lambda expr, indent: f"raise {expr}",
    "yield": lambda expr, indent: f"yield {expr}",
    "str": _call("str"),
    "list": _call("list"),
    "set": _call("set"),
    "dict": _call("dict"),
    "tuple": _call("tuple"),
}


def _is_valid_expression(expr: str) -> bool:
    try:
        tokens = tokenize.generate_tokens(StringIO(expr).readline)
        if any(
            token.type in {tokenize.COMMENT, tokenize.ERRORTOKEN} for token in tokens
        ):
            return False
    except tokenize.TokenError:
        return False
    try:
        ast.parse(expr, mode="eval")
    except SyntaxError:
        return False
    return True


def _match_postfix(
    line_before_cursor: str,
    trigger: str,
    *,
    key_required: bool,
) -> re.Match[str] | None:
    if not trigger:
        return None

    key_pattern = (
        r"(?P<key>[A-Za-z_]\w*)"
        if key_required
        else r"(?P<key>[A-Za-z_]\w*)?"
    )
    pattern = (
        r"^(?P<indent>[ \t]*)(?P<expr>.+?)"
        + re.escape(trigger)
        + key_pattern
        + r"$"
    )
    return re.match(pattern, line_before_cursor)


def _valid_postfix_expression(expr: str) -> bool:
    return bool(expr) and _is_valid_expression(expr)


def postfix_completions(
    line_before_cursor: str,
    trigger: str,
    enabled_templates: list[str] | tuple[str, ...],
) -> list[PostfixCompletion]:
    """Return postfix template completions for the current line."""
    match = _match_postfix(line_before_cursor, trigger, key_required=False)
    if match is None:
        return []

    expr = match.group("expr").strip()
    if not _valid_postfix_expression(expr):
        return []

    prefix = match.group("key") or ""
    indent = match.group("indent")
    return [
        PostfixCompletion(
            key,
            prefix,
            PostfixExpansion(
                text=indent + POSTFIX_TEMPLATES[key](expr, indent),
                start_position=-len(line_before_cursor),
            ),
        )
        for key in enabled_templates
        if key.startswith(prefix) and key in POSTFIX_TEMPLATES
    ]


def expand_postfix(
    line_before_cursor: str,
    trigger: str,
    enabled_templates: list[str] | tuple[str, ...],
) -> PostfixExpansion | None:
    """Expand a postfix template in the current line before the cursor."""
    match = _match_postfix(line_before_cursor, trigger, key_required=True)
    if match is None:
        return None

    key = match.group("key")
    if key not in enabled_templates:
        return None

    template = POSTFIX_TEMPLATES.get(key)
    if template is None:
        return None

    indent = match.group("indent")
    expr = match.group("expr").strip()
    if not _valid_postfix_expression(expr):
        return None

    return PostfixExpansion(
        text=indent + template(expr, indent),
        start_position=-len(line_before_cursor),
    )


def postfix_completion(event: KeyPressEvent) -> None:
    """Expand a postfix template or pass Tab through to normal completion."""
    shell = get_ipython()
    document = event.current_buffer.document
    expansion = expand_postfix(
        document.current_line_before_cursor,
        shell.postfix_completion_trigger,
        shell.postfix_completion_templates,
    )
    if expansion is None:
        pass_through.reply(event)
        return

    event.current_buffer.delete_before_cursor(-expansion.start_position)
    event.current_buffer.insert_text(expansion.text)

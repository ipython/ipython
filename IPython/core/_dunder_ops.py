"""Mapping from AST operator nodes to the dunder methods that implement them.

This lives in its own module, rather than in `IPython.core.guarded_eval` where
it is mostly used, so that the terminal shortcut filters can resolve operators
in a filter expression without importing the whole of `guarded_eval` -- and
with it `typing_extensions`, `dataclasses` and `inspect` -- on every startup.

The names are re-exported from `IPython.core.guarded_eval`, which remains
their documented home.
"""

import ast
from collections.abc import Mapping
from typing import Any

__all__ = [
    "BINARY_OP_DUNDERS",
    "COMP_OP_DUNDERS",
    "UNARY_OP_DUNDERS",
]

BINARY_OP_DUNDERS: dict[type[ast.operator], tuple[str]] = {
    ast.Add: ("__add__",),
    ast.Sub: ("__sub__",),
    ast.Mult: ("__mul__",),
    ast.Div: ("__truediv__",),
    ast.FloorDiv: ("__floordiv__",),
    ast.Mod: ("__mod__",),
    ast.Pow: ("__pow__",),
    ast.LShift: ("__lshift__",),
    ast.RShift: ("__rshift__",),
    ast.BitOr: ("__or__",),
    ast.BitXor: ("__xor__",),
    ast.BitAnd: ("__and__",),
    ast.MatMult: ("__matmul__",),
}

COMP_OP_DUNDERS: dict[type[ast.cmpop], tuple[str, ...]] = {
    ast.Eq: ("__eq__",),
    ast.NotEq: ("__ne__", "__eq__"),
    ast.Lt: ("__lt__", "__gt__"),
    ast.LtE: ("__le__", "__ge__"),
    ast.Gt: ("__gt__", "__lt__"),
    ast.GtE: ("__ge__", "__le__"),
    ast.In: ("__contains__",),
    # Note: ast.Is, ast.IsNot, ast.NotIn are handled specially
}

UNARY_OP_DUNDERS: dict[type[ast.unaryop], tuple[str, ...]] = {
    ast.USub: ("__neg__",),
    ast.UAdd: ("__pos__",),
    # we have to check both __inv__ and __invert__!
    ast.Invert: ("__invert__", "__inv__"),
    ast.Not: ("__not__",),
}


def _find_dunder(
    node_op: ast.AST, dunders: Mapping[type[Any], tuple[str, ...]]
) -> tuple[str, ...] | None:
    dunder = None
    for op, candidate_dunder in dunders.items():
        if isinstance(node_op, op):
            dunder = candidate_dunder
    return dunder

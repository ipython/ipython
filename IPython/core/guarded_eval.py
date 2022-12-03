from typing import Callable, Set, Tuple, NamedTuple, Literal, Union, TYPE_CHECKING
import collections
import sys
import ast
from functools import cached_property
from dataclasses import dataclass, field

from IPython.utils.docs import GENERATING_DOCUMENTATION


if TYPE_CHECKING or GENERATING_DOCUMENTATION:
    from typing_extensions import Protocol
else:
    # do not require on runtime
    Protocol = object  # requires Python >=3.8


class HasGetItem(Protocol):
    def __getitem__(self, key) -> None:
        ...


class InstancesHaveGetItem(Protocol):
    def __call__(self) -> HasGetItem:
        ...


class HasGetAttr(Protocol):
    def __getattr__(self, key) -> None:
        ...


class DoesNotHaveGetAttr(Protocol):
    pass


# By default `__getattr__` is not explicitly implemented on most objects
MayHaveGetattr = Union[HasGetAttr, DoesNotHaveGetAttr]


def unbind_method(func: Callable) -> Union[Callable, None]:
    """Get unbound method for given bound method.

    Returns None if cannot get unbound method."""
    owner = getattr(func, "__self__", None)
    owner_class = type(owner)
    name = getattr(func, "__name__", None)
    instance_dict_overrides = getattr(owner, "__dict__", None)
    if (
        owner is not None
        and name
        and (
            not instance_dict_overrides
            or (instance_dict_overrides and name not in instance_dict_overrides)
        )
    ):
        return getattr(owner_class, name)


@dataclass
class EvaluationPolicy:
    allow_locals_access: bool = False
    allow_globals_access: bool = False
    allow_item_access: bool = False
    allow_attr_access: bool = False
    allow_builtins_access: bool = False
    allow_any_calls: bool = False
    allowed_calls: Set[Callable] = field(default_factory=set)

    def can_get_item(self, value, item):
        return self.allow_item_access

    def can_get_attr(self, value, attr):
        return self.allow_attr_access

    def can_call(self, func):
        if self.allow_any_calls:
            return True

        if func in self.allowed_calls:
            return True

        owner_method = unbind_method(func)
        if owner_method and owner_method in self.allowed_calls:
            return True


def has_original_dunder_external(
    value,
    module_name,
    access_path,
    method_name,
):
    try:
        if module_name not in sys.modules:
            return False
        member_type = sys.modules[module_name]
        for attr in access_path:
            member_type = getattr(member_type, attr)
        value_type = type(value)
        if type(value) == member_type:
            return True
        if isinstance(value, member_type):
            method = getattr(value_type, method_name, None)
            member_method = getattr(member_type, method_name, None)
            if member_method == method:
                return True
    except (AttributeError, KeyError):
        return False


def has_original_dunder(
    value, allowed_types, allowed_methods, allowed_external, method_name
):
    # note: Python ignores `__getattr__`/`__getitem__` on instances,
    # we only need to check at class level
    value_type = type(value)

    # strict type check passes → no need to check method
    if value_type in allowed_types:
        return True

    method = getattr(value_type, method_name, None)

    if not method:
        return None

    if method in allowed_methods:
        return True

    for module_name, *access_path in allowed_external:
        if has_original_dunder_external(value, module_name, access_path, method_name):
            return True

    return False


@dataclass
class SelectivePolicy(EvaluationPolicy):
    allowed_getitem: Set[HasGetItem] = field(default_factory=set)
    allowed_getitem_external: Set[Tuple[str, ...]] = field(default_factory=set)
    allowed_getattr: Set[MayHaveGetattr] = field(default_factory=set)
    allowed_getattr_external: Set[Tuple[str, ...]] = field(default_factory=set)

    def can_get_attr(self, value, attr):
        has_original_attribute = has_original_dunder(
            value,
            allowed_types=self.allowed_getattr,
            allowed_methods=self._getattribute_methods,
            allowed_external=self.allowed_getattr_external,
            method_name="__getattribute__",
        )
        has_original_attr = has_original_dunder(
            value,
            allowed_types=self.allowed_getattr,
            allowed_methods=self._getattr_methods,
            allowed_external=self.allowed_getattr_external,
            method_name="__getattr__",
        )
        # Many objects do not have `__getattr__`, this is fine
        if has_original_attr is None and has_original_attribute:
            return True

        # Accept objects without modifications to `__getattr__` and `__getattribute__`
        return has_original_attr and has_original_attribute

    def get_attr(self, value, attr):
        if self.can_get_attr(value, attr):
            return getattr(value, attr)

    def can_get_item(self, value, item):
        """Allow accessing `__getiitem__` of allow-listed instances unless it was not modified."""
        return has_original_dunder(
            value,
            allowed_types=self.allowed_getitem,
            allowed_methods=self._getitem_methods,
            allowed_external=self.allowed_getitem_external,
            method_name="__getitem__",
        )

    @cached_property
    def _getitem_methods(self) -> Set[Callable]:
        return self._safe_get_methods(self.allowed_getitem, "__getitem__")

    @cached_property
    def _getattr_methods(self) -> Set[Callable]:
        return self._safe_get_methods(self.allowed_getattr, "__getattr__")

    @cached_property
    def _getattribute_methods(self) -> Set[Callable]:
        return self._safe_get_methods(self.allowed_getattr, "__getattribute__")

    def _safe_get_methods(self, classes, name) -> Set[Callable]:
        return {
            method
            for class_ in classes
            for method in [getattr(class_, name, None)]
            if method
        }


class DummyNamedTuple(NamedTuple):
    pass


class EvaluationContext(NamedTuple):
    locals_: dict
    globals_: dict
    evaluation: Literal[
        "forbidden", "minimal", "limitted", "unsafe", "dangerous"
    ] = "forbidden"
    in_subscript: bool = False


class IdentitySubscript:
    def __getitem__(self, key):
        return key


IDENTITY_SUBSCRIPT = IdentitySubscript()
SUBSCRIPT_MARKER = "__SUBSCRIPT_SENTINEL__"


class GuardRejection(ValueError):
    pass


def guarded_eval(code: str, context: EvaluationContext):
    locals_ = context.locals_

    if context.evaluation == "forbidden":
        raise GuardRejection("Forbidden mode")

    # note: not using `ast.literal_eval` as it does not implement
    # getitem at all, for example it fails on simple `[0][1]`

    if context.in_subscript:
        # syntatic sugar for ellipsis (:) is only available in susbcripts
        # so we need to trick the ast parser into thinking that we have
        # a subscript, but we need to be able to later recognise that we did
        # it so we can ignore the actual __getitem__ operation
        if not code:
            return tuple()
        locals_ = locals_.copy()
        locals_[SUBSCRIPT_MARKER] = IDENTITY_SUBSCRIPT
        code = SUBSCRIPT_MARKER + "[" + code + "]"
        context = EvaluationContext(**{**context._asdict(), **{"locals_": locals_}})

    if context.evaluation == "dangerous":
        return eval(code, context.globals_, context.locals_)

    expression = ast.parse(code, mode="eval")

    return eval_node(expression, context)


def eval_node(node: Union[ast.AST, None], context: EvaluationContext):
    """
    Evaluate AST node in provided context.

    Applies evaluation restrictions defined in the context.

    Currently does not support evaluation of functions with arguments.

    Does not evaluate actions which always have side effects:
    - class definitions (``class sth: ...``)
    - function definitions (``def sth: ...``)
    - variable assignments (``x = 1``)
    - augumented assignments (``x += 1``)
    - deletions (``del x``)

    Does not evaluate operations which do not return values:
    - assertions (``assert x``)
    - pass (``pass``)
    - imports (``import x``)
    - control flow
       - conditionals (``if x:``) except for terenary IfExp (``a if x else b``)
       - loops (``for`` and `while``)
       - exception handling

    The purpose of this function is to guard against unwanted side-effects;
    it does not give guarantees on protection from malicious code execution.
    """
    policy = EVALUATION_POLICIES[context.evaluation]
    if node is None:
        return None
    if isinstance(node, ast.Expression):
        return eval_node(node.body, context)
    if isinstance(node, ast.BinOp):
        # TODO: add guards
        left = eval_node(node.left, context)
        right = eval_node(node.right, context)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            return left**right
        if isinstance(node.op, ast.LShift):
            return left << right
        if isinstance(node.op, ast.RShift):
            return left >> right
        if isinstance(node.op, ast.BitOr):
            return left | right
        if isinstance(node.op, ast.BitXor):
            return left ^ right
        if isinstance(node.op, ast.BitAnd):
            return left & right
        if isinstance(node.op, ast.MatMult):
            return left @ right
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Index):
        return eval_node(node.value, context)
    if isinstance(node, ast.Tuple):
        return tuple(eval_node(e, context) for e in node.elts)
    if isinstance(node, ast.List):
        return [eval_node(e, context) for e in node.elts]
    if isinstance(node, ast.Set):
        return {eval_node(e, context) for e in node.elts}
    if isinstance(node, ast.Dict):
        return dict(
            zip(
                [eval_node(k, context) for k in node.keys],
                [eval_node(v, context) for v in node.values],
            )
        )
    if isinstance(node, ast.Slice):
        return slice(
            eval_node(node.lower, context),
            eval_node(node.upper, context),
            eval_node(node.step, context),
        )
    if isinstance(node, ast.ExtSlice):
        return tuple([eval_node(dim, context) for dim in node.dims])
    if isinstance(node, ast.UnaryOp):
        # TODO: add guards
        value = eval_node(node.operand, context)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.Invert):
            return ~value
        if isinstance(node.op, ast.Not):
            return not value
        raise ValueError("Unhandled unary operation:", node.op)
    if isinstance(node, ast.Subscript):
        value = eval_node(node.value, context)
        slice_ = eval_node(node.slice, context)
        if policy.can_get_item(value, slice_):
            return value[slice_]
        raise GuardRejection(
            "Subscript access (`__getitem__`) for",
            type(value),  # not joined to avoid calling `repr`
            f" not allowed in {context.evaluation} mode",
        )
    if isinstance(node, ast.Name):
        if policy.allow_locals_access and node.id in context.locals_:
            return context.locals_[node.id]
        if policy.allow_globals_access and node.id in context.globals_:
            return context.globals_[node.id]
        if policy.allow_builtins_access and node.id in __builtins__:
            return __builtins__[node.id]
        if not policy.allow_globals_access and not policy.allow_locals_access:
            raise GuardRejection(
                f"Namespace access not allowed in {context.evaluation} mode"
            )
        else:
            raise NameError(f"{node.id} not found in locals nor globals")
    if isinstance(node, ast.Attribute):
        value = eval_node(node.value, context)
        if policy.can_get_attr(value, node.attr):
            return getattr(value, node.attr)
        raise GuardRejection(
            "Attribute access (`__getattr__`) for",
            type(value),  # not joined to avoid calling `repr`
            f"not allowed in {context.evaluation} mode",
        )
    if isinstance(node, ast.IfExp):
        test = eval_node(node.test, context)
        if test:
            return eval_node(node.body, context)
        else:
            return eval_node(node.orelse, context)
    if isinstance(node, ast.Call):
        func = eval_node(node.func, context)
        print(node.keywords)
        if policy.can_call(func) and not node.keywords:
            args = [eval_node(arg, context) for arg in node.args]
            return func(*args)
        raise GuardRejection(
            "Call for",
            func,  # not joined to avoid calling `repr`
            f"not allowed in {context.evaluation} mode",
        )
    raise ValueError("Unhandled node", node)


SUPPORTED_EXTERNAL_GETITEM = {
    ("pandas", "core", "indexing", "_iLocIndexer"),
    ("pandas", "core", "indexing", "_LocIndexer"),
    ("pandas", "DataFrame"),
    ("pandas", "Series"),
    ("numpy", "ndarray"),
    ("numpy", "void"),
}

BUILTIN_GETITEM = {
    dict,
    str,
    bytes,
    list,
    tuple,
    collections.defaultdict,
    collections.deque,
    collections.OrderedDict,
    collections.ChainMap,
    collections.UserDict,
    collections.UserList,
    collections.UserString,
    DummyNamedTuple,
    IdentitySubscript,
}


def _list_methods(cls, source=None):
    """For use on immutable objects or with methods returning a copy"""
    return [getattr(cls, k) for k in (source if source else dir(cls))]


dict_non_mutating_methods = ("copy", "keys", "values", "items")
list_non_mutating_methods = ("copy", "index", "count")
set_non_mutating_methods = set(dir(set)) & set(dir(frozenset))


dict_keys = type({}.keys())
method_descriptor = type(list.copy)

ALLOWED_CALLS = {
    bytes,
    *_list_methods(bytes),
    dict,
    *_list_methods(dict, dict_non_mutating_methods),
    dict_keys.isdisjoint,
    list,
    *_list_methods(list, list_non_mutating_methods),
    set,
    *_list_methods(set, set_non_mutating_methods),
    frozenset,
    *_list_methods(frozenset),
    range,
    str,
    *_list_methods(str),
    tuple,
    *_list_methods(tuple),
    collections.deque,
    *_list_methods(collections.deque, list_non_mutating_methods),
    collections.defaultdict,
    *_list_methods(collections.defaultdict, dict_non_mutating_methods),
    collections.OrderedDict,
    *_list_methods(collections.OrderedDict, dict_non_mutating_methods),
    collections.UserDict,
    *_list_methods(collections.UserDict, dict_non_mutating_methods),
    collections.UserList,
    *_list_methods(collections.UserList, list_non_mutating_methods),
    collections.UserString,
    *_list_methods(collections.UserString, dir(str)),
    collections.Counter,
    *_list_methods(collections.Counter, dict_non_mutating_methods),
    collections.Counter.elements,
    collections.Counter.most_common,
}

EVALUATION_POLICIES = {
    "minimal": EvaluationPolicy(
        allow_builtins_access=True,
        allow_locals_access=False,
        allow_globals_access=False,
        allow_item_access=False,
        allow_attr_access=False,
        allowed_calls=set(),
        allow_any_calls=False,
    ),
    "limitted": SelectivePolicy(
        # TODO:
        # - should reject binary and unary operations if custom methods would be dispatched
        allowed_getitem=BUILTIN_GETITEM,
        allowed_getitem_external=SUPPORTED_EXTERNAL_GETITEM,
        allowed_getattr={
            *BUILTIN_GETITEM,
            set,
            frozenset,
            object,
            type,  # `type` handles a lot of generic cases, e.g. numbers as in `int.real`.
            dict_keys,
            method_descriptor,
        },
        allowed_getattr_external={
            # pandas Series/Frame implements custom `__getattr__`
            ("pandas", "DataFrame"),
            ("pandas", "Series"),
        },
        allow_builtins_access=True,
        allow_locals_access=True,
        allow_globals_access=True,
        allowed_calls=ALLOWED_CALLS,
    ),
    "unsafe": EvaluationPolicy(
        allow_builtins_access=True,
        allow_locals_access=True,
        allow_globals_access=True,
        allow_attr_access=True,
        allow_item_access=True,
        allow_any_calls=True,
    ),
}

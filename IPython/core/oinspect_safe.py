# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file is based on https://github.com/googlecolab/colabtools/blob/feb5dde3839251fd6fd8bf23e081d0a8b9a8187b/google/colab/_inspector.py
# Another take on a safe_repr is at
# https://github.com/microsoft/debugpy/blob/04403ddc1c2f67e783cdc1b13789ddff7d8f3b9c/src/debugpy/_vendored/pydevd/_pydevd_bundle/pydevd_safe_repr.py,
# but while it does do a lot of checking, it also calls __repr__ at
# https://github.com/microsoft/debugpy/blob/04403ddc1c2f67e783cdc1b13789ddff7d8f3b9c/src/debugpy/_vendored/pydevd/_pydevd_bundle/pydevd_safe_repr.py#L350
# Same for the upstream pydev version: https://github.com/fabioz/PyDev.Debugger/blob/c604fe20cd87b186d2191c2528d21aa01b4e15cb/_pydevd_bundle/pydevd_safe_repr.py

"""Tools for inspecting Python objects in a "safe" way.

Similar to the oinspect module, but we go to great lengths to not call
a __repr__ method, except for a small whitelist of objects.

Based on the Colab _inspector.py module (Apache 2.0 license)
"""

import builtins
import collections.abc as collections_abc
import inspect
import logging
import math
import types
from typing import Union


from IPython.core import oinspect
from IPython.utils import dir2

# We also iterate over dicts, but the logic differs slightly (due to compound
# entries), so they don't appear in this mapping.
_APPROVED_ITERABLES = {
    set: ("{", "}"),
    frozenset: ("frozenset({", "})"),
    list: ("[", "]"),
    tuple: ("(", ")"),
}
_ITERABLE_SIZE_THRESHOLD = 5
_MAX_RECURSION_DEPTH = 4
_STRING_ABBREV_LIMIT = 40


# Fully qualified names of types which are OK to call the default repr.
_APPROVED_REPRS = (
    "numpy.datetime64",
    "numpy.float128",
    "numpy.float16",
    "numpy.float32",
    "numpy.float64",
    "numpy.int16",
    "numpy.int32",
    "numpy.int64",
    "numpy.int8",
)

_UNAVAILABLE_MODULE_NAME = "<unknown>"


@undoc
def getargspec(obj):
    """Wrapper around :func:`inspect.getfullargspec`

    In addition to functions and methods, this can also handle objects with a
    ``__call__`` attribute.

    DEPRECATED: Deprecated since 7.10. Do not use, will be removed.
    """

    warnings.warn(
        "`getargspec` function is deprecated as of IPython 7.10"
        "and will be removed in future versions.",
        DeprecationWarning,
        stacklevel=2,
    )

    if safe_hasattr(obj, "__call__") and not is_simple_callable(obj):
        obj = obj.__call__

    return inspect.getfullargspec(obj)


def _safe_repr(obj, depth=0, visited=None):
    """Return a repr for obj that is guaranteed to avoid expensive computation.

    Colab's UI is aggressive about inspecting objects, and we've discovered that
    in practice, too many objects can have a repr which is expensive to compute.

    To make this work, we specify a set of types for which we compute a repr:
     * builtin types which aren't Iterable are safe
     * Sized objects with a `.shape` tuple attribute (eg ndarrays and dataframes)
       get a summary with type name and shape
     * list, dict, set, frozenset, and tuple objects we format recursively, up to
       a fixed depth, and up to a fixed length
     * other Iterables get a summary with type name and len
     * all other objects get a summary with type name

    In all cases, we limit:
     * the number of elements we'll format in an iterable
     * the total depth we'll recur
     * the size of any single entry
    Any time we cross one of these thresholds, we use `...` to imply additional
    elements were elided, just as python does when printing circular objects.

    See https://docs.python.org/3/library/collections.abc.html for definitions of
    the various types of collections.

    For more backstory, see b/134847514.

    Args:
      obj: A python object to provide a repr for.
      depth: (optional) The current recursion depth.
      visited: (optional) A set of ids of objects visited so far.

    Returns:
      A (potentially abbreviated) string representation for obj.
    """
    visited = visited or frozenset()

    # First, terminate if we're already too deep in a nested structure..
    if depth > _MAX_RECURSION_DEPTH:
        return "..."

    type_name = type(obj).__name__
    module_name = getattr(type(obj), "__module__", _UNAVAILABLE_MODULE_NAME)
    if not isinstance(module_name, str):
        module_name = _UNAVAILABLE_MODULE_NAME
    fully_qualified_type_name = ".".join(
        (
            module_name,
            getattr(type(obj), "__qualname__", type_name),
        )
    )

    # Next, we want to allow printing for ~all builtin types other than iterables.
    if isinstance(obj, (bytes, str)):
        if len(obj) > _STRING_ABBREV_LIMIT:
            ellipsis = b"..." if isinstance(obj, bytes) else "..."
            return repr(obj[:_STRING_ABBREV_LIMIT] + ellipsis)
        return repr(obj)
    # Bound methods will include the full repr of the object they're bound to,
    # which we need to avoid.
    if isinstance(obj, types.MethodType):
        return "{} method".format(obj.__qualname__)
    # Matching by module name is ugly; we do this because many types (eg
    # type(None)) don't appear in the dir() of any module in py3.
    if (
        not isinstance(obj, collections_abc.Iterable)
        and module_name == builtins.__name__
    ):
        # The only arbitrary-sized builtin type is int; we compute the first and
        # last 10 digits if the number is larger than 30 digits.
        if obj and isinstance(obj, int):
            sign = "-" if obj < 0 else ""
            a = abs(obj)
            ndigits = int(math.log10(a) + 1)
            if ndigits > 30:
                start = int(a // 10 ** (ndigits - 10))
                # Our log10 might be wrong, due to rounding errors; we recalculate based
                # on how many digits remain here (which is either 9 or 10).
                ndigits = (ndigits - 10) + len(str(start))
                end = a % (10**10)
                return "{}{}...{} ({} digit int)".format(sign, start, end, ndigits)
        return repr(obj)

    # If it wasn't a primitive object, we may need to recur; we see if we've
    # already seen this object, and if not, add its id to the list of visited
    # objects.
    if id(obj) in visited:
        return "..."
    visited = visited.union({id(obj)})

    # Sized & shaped objects get a simple summary.
    if isinstance(obj, collections_abc.Sized):
        shape = getattr(obj, "shape", None)

        if (
            isinstance(shape, tuple)
            and module_name.startswith("pandas.")
            and type_name == "Series"
        ):
            return f"{type_name} with shape {shape} and dtype {obj.dtype}"

    # We recur on the types allowed above; the logic is slightly different for
    # dicts, as they have compound entries.
    if isinstance(obj, dict):
        s = []
        # If this is a subclass of dict, include that in the print repr.
        type_prefix = ""
        length_prefix = ""
        if depth == 0:
            length_prefix = (
                "({} items) ".format(len(obj)) if len(obj) != 1 else "(1 item) "
            )
        if dict is not type(obj):
            type_prefix = fully_qualified_type_name
        for i, (k, v) in enumerate(obj.items()):
            if i >= _ITERABLE_SIZE_THRESHOLD:
                s.append("...")
                break
            # This is cosmetic: without it, we'd end up with {...: ...}, which is
            # uglier than {...}.
            if depth == _MAX_RECURSION_DEPTH:
                s.append("...")
                break
            s.append(
                ": ".join(
                    (
                        _safe_repr(k, depth=depth + 1, visited=visited),
                        _safe_repr(v, depth=depth + 1, visited=visited),
                    )
                )
            )
        return "".join((length_prefix, type_prefix, "{", ", ".join(s), "}"))

    if isinstance(obj, tuple(_APPROVED_ITERABLES)):
        # Empty sets and frozensets get special treatment.
        if not obj and isinstance(obj, (set, frozenset)):
            return "{}()".format(type_name)
        # The object we're formatting is just a subclass of one of the
        # _APPROVED_ITERABLES; we iterate through to find the first such iterable,
        # and then format the result.
        for collection_type, (start, end) in _APPROVED_ITERABLES.items():
            if isinstance(obj, collection_type):
                # If this is a subclass of one of the basic types, include that in the
                # print repr.
                type_prefix = ""
                length_prefix = ""
                if depth == 0:
                    length_prefix = (
                        "({} items) ".format(len(obj)) if len(obj) != 1 else "(1 item) "
                    )
                if collection_type is not type(obj):
                    type_prefix = fully_qualified_type_name
                s = []
                for i, v in enumerate(obj):
                    if i >= _ITERABLE_SIZE_THRESHOLD:
                        s.append("...")
                        break
                    s.append(_safe_repr(v, depth=depth + 1, visited=visited))
                return "".join((length_prefix, type_prefix, start, ", ".join(s), end))

    # Other sized objects get a simple summary.
    if isinstance(obj, collections_abc.Sized):
        try:
            obj_len = len(obj)
            return "{} with {} items".format(type_name, obj_len)
        except Exception:  # pylint: disable=broad-except
            pass

    if fully_qualified_type_name in _APPROVED_REPRS:
        try:
            return repr(obj)
        except Exception:  # pylint: disable=broad-except
            pass

    # We didn't know what it was; we give up and just give the type name.
    return "{} instance".format(fully_qualified_type_name)


class _SafeRepr:
    """A safe repr wrapper for an object

    This class wraps a value to provide a repr that is safe for that value"""

    def __init__(self, value):
        self._repr = _safe_repr(value)

    def __repr__(self):
        return self._repr


class SafeInspector(oinspect.Inspector):
    """Safe object inspector that does not invoke an arbitray objects __repr__ method."""

    def _getdef(self, obj, oname="") -> Union[str, None]:
        """Safe variant of oinspect.Inspector._getdef.

        The upstream _getdef method includes the full string representation of all
        default arguments, which may run arbitrary code. We intercede to apply our
        custom getargspec wrapper, which uses _safe_repr.

        Args:
          obj: function whose definition we want to format.
          oname: (optional) If provided, prefix the definition with this name.

        Returns:
          A formatted definition or None.
        """
        try:
            try:
                sig = inspect.signature(obj)
            except (TypeError, ValueError):
                # TODO: when does this happen? Should the main oinspect._getdef guard for this too?
                return None

            # Replace defaults and annotations with safe repr equivalents
            new_params = []
            for v in sig.parameters.values():
                new_params.append(
                    v.replace(
                        default=_SafeRepr(v.default)
                        if v.default != v.empty
                        else v.default,
                        annotation=_SafeRepr(v.annotation)
                        if v.annotation != v.empty
                        else v.annotation,
                    )
                )
            sig = sig.replace(parameters=new_params)

            # oinspect._render_signature adds linebreaks between parameters if the name and signature is long
            return oinspect._render_signature(sig, oname)
        except:  # pylint: disable=bare-except
            logging.exception("Exception raised in SafeInspector._getdef")

    def getstr(self, obj):
        return _safe_repr(obj)

    def getlen(self, obj):
        # TODO: figure out when it is safe to call len(obj)
        # for example, it can stall a long time on lazy objects
        # so perhaps we just have a whitelist of things it is safe to call on?
        return None

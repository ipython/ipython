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

import ast
import builtins
import collections.abc as collections_abc
import inspect
import logging
import math
import re
import types

import astor
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
_MAX_DECORATOR_DEPTH = 12
_STRING_ABBREV_LIMIT = 40

# Unhelpful docstrings we avoid surfacing to users.
_BASE_CALL_DOC = types.FunctionType.__call__.__doc__
_BASE_INIT_DOC = object.__init__.__doc__

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


def _getdoc(obj):
    """Custom wrapper for inspect.getdoc.

    IPython.core.oinspect.getdoc wraps Python's inspect.getdoc to catch exceptions
    and allow for objects with a custom getdoc() method. However, there are two
    problems:
     * inspect.getdoc already catches any exceptions
     * it then calls get_encoding, which calls inspect.getfile, which may call
       repr(obj) (to use in an error string, which oinspect.getdoc throws away).

    We replace this with our own wrapper which still allows for custom getdoc()
    methods, but avoids calling inspect.getfile.

    Args:
      obj: an object to fetch a docstring for

    Returns:
      A docstring or ''.
    """
    if hasattr(obj, "getdoc"):
        try:
            docstring = obj.getdoc()
        except Exception:  # pylint: disable=broad-except
            pass
        else:
            if isinstance(docstring, str):
                return docstring

    return inspect.getdoc(obj) or ""


def _unwrap(obj):
    """Safe version of inspect.unwrap.

    If the object is decorated with more than _MAX_DECORATOR_DEPTH decorators,
    the original object is returned.

    Args:
      obj: object to unwrap

    Returns:
      The unwrapped object.
    """
    original = obj
    for _ in range(_MAX_DECORATOR_DEPTH):
        if not hasattr(obj, "__wrapped__"):
            return obj
        obj = obj.__wrapped__
    return original


def _getargspec(obj):
    """Wrapper for oinspect.getargspec.

    This wraps the parent to swallow exceptions.

    Args:
      obj: object whose argspec we return

    Returns:
      The result of getargspec or None.
    """
    obj = _unwrap(obj)
    try:
        argspec = oinspect.getargspec(obj)
    except (TypeError, AttributeError):
        return None
    if argspec.args and argspec.args[0] == "self":
        argspec = argspec._replace(args=argspec.args[1:])
    return argspec


def _getargspec_dict(obj):
    """Py2/Py3 compability wrapper for _getargspec.

    Python's `inspect.getargspec` returns different types in python2 and python3,
    and this function exists to paper over the difference: we always move
    `spec.keywords` to `spec.varkw`; in order to make this possible, we return a
    dict instead of a namedtuple.

    We also call `_safe_repr` on all values in `defaults`, to avoid potentially
    expensive computation of string representations.

    Args:
      obj: object whose argspec we return

    Returns:
      a dict with the argspec, or None.
    """
    argspec = _getargspec(obj)
    if argspec is None:
        return None
    # We need to avoid potentially computing expensive string representations, so
    # we proactively call _safe_repr ourselves.
    if argspec.defaults:
        argspec = argspec._replace(
            defaults=[_safe_repr(val) for val in argspec.defaults]
        )
    return argspec._asdict()


def _getsource(obj):
    """Safe oinspect.getsource wrapper.

    **NOTE**: this function is may call repr(obj).

    Args:
      obj: object whose source we want to fetch.

    Returns:
      source code or None.
    """
    try:
        return oinspect.getsource(obj)
    except TypeError:
        return None


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

        if (
            isinstance(shape, tuple)
            or hasattr(shape, "__module__")
            and isinstance(shape.__module__, str)
            and "tensorflow." in shape.__module__
        ):
            return "{} with shape {}".format(type_name, shape)

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


# The `inspect.Parameter` class hardcodes the use of `repr()` for formatting
# default values; this is a small shim for replacing defaults using our
# `_safe_repr` function.
class _SafeReprParam:
    def __init__(self, v):
        self._repr = _safe_repr(v)

    def __repr__(self):
        return self._repr


class SafeInspector(oinspect.Inspector):
    """Safe object inspector that does not invoke an arbitray objects __repr__ method."""

    def _getdef(self, obj, oname=""):
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
        if dir2.safe_hasattr(obj, "__call__") and not oinspect.is_simple_callable(obj):
            obj = obj.__call__

        try:
            try:
                sig = inspect.signature(obj)
            except (TypeError, ValueError):
                return None
            new_params = []
            for v in sig.parameters.values():
                new_default = v.default
                if v.default != v.empty:
                    new_default = _SafeReprParam(v.default)
                new_params.append(v.replace(default=new_default))
            new_sig = sig.replace(parameters=new_params)
            return f"{oname}{new_sig}"
        except:  # pylint: disable=bare-except
            logging.exception("Exception raised in SafeInspector._getdef")

    def info(self, obj, oname="", formatter=None, info=None, detail_level=0):
        """Compute a dict with detailed information about an object.

        This overrides the superclass method for two main purposes:
         * avoid calling str() or repr() on the object
         * use our custom repr

        Args:
          obj: object to inspect.
          oname: (optional) string reference to this object
          formatter: (optional) custom docstring formatter
          info: (optional) previously computed information about obj
          detail_level: (optional) 0 or 1; 1 means "include more detail"

        Returns:
          A dict with information about obj.
        """

        # We want to include the following list of keys for all objects:
        # * name
        # * found
        # * isclass
        # * string_form
        # * type_name
        #
        # For callables, we want to add a subset of:
        # * argspec
        # * call_docstring
        # * definition
        # * docstring
        # * file
        # * init_definition
        # * init_docstring
        # * source_end_line
        # * source_start_line
        # * source_definition
        #
        # For detail_level 1, we include:
        # * file
        # This can be expensive, as the stdlib mechanisms for looking up the file
        # containing obj may call repr(obj).
        #
        # NOTE: These keys should stay in sync with the corresponding list in our
        # frontend code.
        #
        # We want non-None values for:
        # * isalias
        # * ismagic
        # * namespace
        #
        # TODO(b/138128444): Handle class_docstring and call_def, or determine that
        # we're safe ignoring them.

        obj_type = type(obj)
        out = {
            "name": oname,
            "found": True,
            "is_class": inspect.isclass(obj),
            "string_form": None,
            # Fill in empty values.
            "docstring": None,
            "file": None,
            "isalias": False,
            "ismagic": info.ismagic if info else False,
            "namespace": info.namespace if info else "",
        }
        if detail_level >= self.str_detail_level:
            out["string_form"] = _safe_repr(obj)

        if getattr(info, "ismagic", False):
            out["type_name"] = "Magic function"
        else:
            out["type_name"] = obj_type.__name__

        # If the object is callable, we want to compute a docstring and related
        # information. We could exit early, but all the code below is in conditional
        # blocks, so there's no need.
        #
        # We can't simply call into the superclass method, as we need to avoid
        # (transitively) calling inspect.getfile(): this function will end up
        # calling repr() on our object.

        # We want to include a docstring if we don't have source, which happens
        # when:
        # * detail_level == 0, or
        # * detail_level == 1 but we can't find source
        # So we first try dealing with detail_level == 1, and then set
        # the docstring if no source is set.
        if detail_level == 1:
            # This should only ever happen if the user has asked for source (eg via
            # `obj??`), so we're OK with potentially calling repr for now.
            # TODO(b/138128444): Ensure we don't call str() or repr().
            source = _getsource(obj)
            if source is None and hasattr(obj, "__class__"):
                source = _getsource(obj.__class__)
            if source is not None:
                out["source"] = source
        if "source" not in out:
            formatter = formatter or (lambda x: x)
            docstring = formatter(_getdoc(obj) or "<no docstring>")
            if docstring:
                out["docstring"] = docstring

        if _iscallable(obj):
            filename = oinspect.find_file(obj)
            if filename and (
                filename.endswith((".py", ".py3", ".pyc"))
                or "<ipython-input" in filename
            ):
                out["file"] = filename

            line = oinspect.find_source_lines(obj)
            out["source_start_line"] = line
            # inspect.getsourcelines exposes the length of the source as well, which
            # can be used to highlight the entire code block, but find_source_lines
            # currently does not expose this. For now just highlight the first line.
            out["source_end_line"] = line

        # The remaining attributes only apply to classes or callables.
        if inspect.isclass(obj):
            # For classes with an __init__, we set init_definition and init_docstring.
            init = getattr(obj, "__init__", None)
            if init:
                init_docstring = _getdoc(init)
                if init_docstring and init_docstring != _BASE_INIT_DOC:
                    out["init_docstring"] = init_docstring
                init_def = _get_source_definition(init)
                if not init_def:
                    init_def = self._getdef(init, oname)
                if init_def:
                    out["init_definition"] = init_def

            # For classes, the __init__ method is the method invoked on call, but
            # old-style classes may not have an __init__ method.
            if init:
                argspec = _getargspec_dict(init)
                if argspec:
                    out["argspec"] = argspec
        elif callable(obj):
            definition = _get_source_definition(obj)
            if not definition:
                definition = self._getdef(obj, oname)
            if definition:
                out["definition"] = definition

            if not oinspect.is_simple_callable(obj):
                call_docstring = _getdoc(obj.__call__)
                if call_docstring and call_docstring != _BASE_CALL_DOC:
                    out["call_docstring"] = call_docstring

            out["argspec"] = _getargspec_dict(obj)

        return oinspect.object_info(**out)


def _iscallable(obj):
    """Check if an object is a callable object safe for inspect.find_file."""
    return (
        inspect.ismodule(obj)
        or inspect.isclass(obj)
        or inspect.ismethod(obj)
        or inspect.isfunction(obj)
        or inspect.iscode(obj)
    )


def _get_source_definition(obj):
    """Get a source representation of the function definition."""
    try:
        obj = _unwrap(obj)

        if dir2.safe_hasattr(obj, "__call__") and not oinspect.is_simple_callable(obj):
            obj = obj.__call__

        lines, lnum = inspect.findsource(obj)
        block = inspect.getblock(lines[lnum:])

        # Trim leading whitespace for all lines.
        prefix = re.match("^([ \t]*)", block[0]).group()
        trimmed = []
        for line in block:
            if line.startswith(prefix):
                line = line[len(prefix) :]
            trimmed.append(line)

        # Override the default join to avoid wrapping.
        def join_lines(source):
            return "".join(source)

        module = ast.parse("\n".join(trimmed), mode="exec")
        function = module.body[0]
        # Remove 'self' if it's the first arg.
        if function.args.args and function.args.args[0].arg == "self":
            function.args.args.pop(0)

        function.body = []
        function.decorator_list = []
        decl = astor.to_source(
            function, indent_with="", pretty_source=join_lines
        ).strip()
        # Strip the trailing `:`
        if decl.endswith(":"):
            decl = decl[:-1]
        return decl
    except Exception:  # pylint: disable=broad-except
        return None

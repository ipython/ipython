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
import linecache
import logging
import math
import re
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



def _unwrap(obj):
    """Safe best-effort version of inspect.unwrap    

    Args:
      obj: object to unwrap

    Returns:
      The unwrapped object if there was no error unwrapping it, otherwise the original object.
    """
    try:
        return inspect.unwrap(obj)
    except:
        # For example, there could be a cycle in the unwraps, or there could be
        # an error on accessing the __wrapped__ attribute
        return obj


@undoc
def getargspec(obj):
    """Wrapper around :func:`inspect.getfullargspec`

    In addition to functions and methods, this can also handle objects with a
    ``__call__`` attribute.

    DEPRECATED: Deprecated since 7.10. Do not use, will be removed.
    """

    warnings.warn('`getargspec` function is deprecated as of IPython 7.10'
                  'and will be removed in future versions.', DeprecationWarning, stacklevel=2)

    if safe_hasattr(obj, '__call__') and not is_simple_callable(obj):
        obj = obj.__call__

    return inspect.getfullargspec(obj)



# TODO: strip out self from arginspect

# Call signature, then call safe_repr on the default values

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
        # TODO: oinspect.getargspec is deprecated
        argspec = oinspect.getargspec(obj)
    except (TypeError, AttributeError):
        return None

    # Strip out self from the args
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

    def _getdef(self, obj, oname="") -> Union[str,None]:
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
                new_params.append(v.replace(
                    default=_SafeRepr(v.default) if v.default != v.empty else v.default,
                    annotation=_SafeRepr(v.annotation) if v.annotation != v.empty else v.annotation
                ))
            sig = sig.replace(parameters=new_params)

            # oinspect._render_signature adds linebreaks between parameters if the name and signature is long
            return oinspect._render_signature(sig, oname)
        except: # pylint: disable=bare-except
            logging.exception("Exception raised in SafeInspector._getdef")

    def getstr(self, obj):
        return _safe_repr(obj)

    def getlen(self, obj):
        # TODO: figure out when it is safe to call len(obj)
        # for example, it can stall a long time on lazy objects
        # so perhaps we just have a whitelist of things it is safe to call on?
        return None

    def info(self, obj, oname="", info=None, detail_level=0) -> dict:
        """Compute a dict with detailed information about an object.

        This overrides the superclass method for two main purposes:
         * avoid calling str() or repr() on the object
         * use our custom repr

        Args:
          obj: object to inspect.
          oname: (optional) string reference to this object
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
        # We want non-None values for:
        # * isalias
        # * ismagic
        # * namespace
        # * subclasses
        #
        # TODO(b/138128444): Handle class_docstring and call_def, or determine that
        # we're safe ignoring them.

        ismagic = getattr(info, 'magic', False)
        isalias = getattr(info, 'isalias', False)
        ospace = getattr(info, 'namespace', None)

        # TODO: upstream function has code here to get the docstring, probably prematurely.
        # Check to see if we are handling, for example, the isalias case below where we get the docstring


        # store output in a dict, we initialize it here and fill it as we go
        out = dict(
            name=oname,
            found=True,
            isalias=isalias,
            ismagic=ismagic,
            isclass=inspect.isclass(obj),
            subclasses=None,
        )

        if ospace:
            out['namespace'] = ospace

        if ismagic:
            out['type_name'] = 'Magic function'
        elif isalias:
            out['type_name'] = 'System alias'
        else:
            out['type_name'] = type(obj).__name__

        try:
            bclass = obj.__class__
            # TODO: PROBLEM!!! calling str...
            out['base_class'] = str(bclass)
        except:
            pass

        # Length (for strings and lists)
        try:
            # TODO: is calling len an issue? Presumably for some lazy objects it may take a long time
            # to calculate the length
            out['length'] = str(len(obj))
        except Exception:
            pass


        # Find the file if it is safe
        binary_file = False
        if _iscallable(obj):
            fname = oinspect.find_file(obj)
            if fname is None:
                # if anything goes wrong, we don't want to show source, so it's as
                # if the file was binary
                binary_file = True
            else:
                if fname.endswith(('.so', '.dll', '.pyd')):
                    binary_file = True
                elif fname.endswith('<string>'):
                    fname = 'Dynamically generated function. No source code available.'
                out['file'] = oinspect.compress_user(fname)
                line = oinspect.find_source_lines(obj, return_length=True)
                if line is not None:
                    out["source_start_line"] = line[0]
                    out["source_end_line"] = line[0] + line[1] - 1



        # TODO: match up the functionality for string_form
        if detail_level >= self.str_detail_level:
            # TODO: elide strings that are too long
            # TODO: indent string
            # TODO: is all that done in _safe_repr???
            out["string_form"] = _safe_repr(obj)

            # Other implementation...
            # string_max = 200 # max size of strings to show (snipped if longer)
            # shalf = int((string_max - 5) / 2)

            # try:
            #     ostr = str(obj)
            #     str_head = 'string_form'
            #     if not detail_level and len(ostr)>string_max:
            #         ostr = ostr[:shalf] + ' <...> ' + ostr[-shalf:]
            #         ostr = ("\n" + " " * len(str_head.expandtabs())).\
            #                 join(q.strip() for q in ostr.split("\n"))
            #     out[str_head] = ostr
            # except:
            #     pass

        # BEGIN OLD IMPLEMENTATION


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
        if detail_level > 0:
            # This should only ever happen if the user has asked for source (eg via
            # `obj??`), so we're OK with potentially calling repr for now.


            # Flush the source cache because inspect can return out-of-date
            # source
            linecache.checkcache()

            try:
                if isinstance(obj, property) or not binary_file:
                    src = oinspect.getsource(obj, oname)

                    # TODO: When does this happen? Should we port this part upstream, getting the source for .__class__??
                    if src is None and hasattr(obj, "__class__"):
                        src = oinspect.getsource(obj.__class__)

                    if src is not None:
                        src = src.rstrip()
                    out['source'] = src

            except Exception:
                pass
  
        # Get docstring, special-casing aliases:
        # TODO: calling str(obj) all over here!
        if isalias:
            if not callable(obj):
                try:
                    docstring = "Alias to the system command:\n  %s" % obj[1]
                except:
                    docstring = "Alias: " + str(obj)
            else:
                docstring = "Alias to " + str(obj)
                if obj.__doc__:
                    docstring += "\nDocstring:\n" + obj.__doc__
        else:
            docstring = oinspect.getdoc(obj)
            if docstring is None:
                docstring = '<no docstring>'

        # Add docstring only if source does not have it (avoid repetitions).
        if docstring and not self._source_contains_docstring(out.get('source'), docstring):
            out['docstring'] = docstring


        if docstring is not None:
            # Add docstring if source does not have it (avoid repetitions).
            if 'source' in out:
                if not self._source_contains_docstring(out['source'], docstring):
                    out['docstring'] = docstring
            else:
                out['docstring'] = docstring
        else:
            out['docstring'] = '<no docstring>'


        # TODO: MADE IT TO HERE IN COMPARING WITH UPSTREAM

        # The remaining attributes only apply to classes or callables.
        if inspect.isclass(obj):
            # get the init signature:
            init_def = self._getdef(obj, oname)

            # get the __init__ docstring and, if still needed, the __init__ signature
            obj_init = getattr(obj, "__init__", None)
            if obj_init:
               init_docstring = oinspect.getdoc(obj_init)
                # Skip Python's auto-generated docstrings
                if init_docstring == oinspect._object_init_docstring:
                    init_docstring = None

                if not init_def:
                    # Get signature from init if top-level sig failed.
                    # Can happen for built-in types (dict, etc.).
                    init_def = self._getdef(obj_init, oname)

            if init_def:
                out['init_definition'] = init_def

            if init_docstring:
                out['init_docstring'] = init_docstring


            names = [sub.__name__ for sub in type.__subclasses__(obj)]
            if len(names) < 10:
                all_names = ", ".join(names)
            else:
                all_names = ", ".join(names[:10] + ["..."])
            out["subclasses"] = all_names
        elif callable(obj):
            definition = _get_source_definition(obj)
            if not definition:
                definition = self._getdef(obj, oname)
            if definition:
                out["definition"] = definition

            if not oinspect.is_simple_callable(obj):
                call_docstring = oinspect.getdoc(obj.__call__)
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
        decl = ast.unparse(function).strip()
        # Strip the trailing `:`
        if decl.endswith(":"):
            decl = decl[:-1]
        return decl
    except Exception:  # pylint: disable=broad-except
        return None

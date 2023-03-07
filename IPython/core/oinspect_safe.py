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

import inspect
import logging
from typing import Union

from . import oinspect
from IPython.utils.decorators import undoc
from . import oinspect_safe_signature
from .oinspect_safe_repr import safe_repr

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


class _SafeRepr:
    """A safe repr wrapper for an object

    This class wraps a value to provide a repr that is safe for that value"""

    def __init__(self, value):
        self._repr = safe_repr(value)

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
                sig = oinspect_safe_signature.signature(obj)
            except (TypeError, ValueError):
                # TODO: when does this happen? Should the main oinspect._getdef guard for this too?
                return None

            # oinspect._render_signature adds linebreaks between parameters if the name and signature is long
            return oinspect._render_signature(sig, oname)
        except:  # pylint: disable=bare-except
            logging.exception("Exception raised in SafeInspector._getdef")

    def getstr(self, obj):
        return safe_repr(obj)

    def getlen(self, obj):
        # TODO: figure out when it is safe to call len(obj)
        # for example, it can stall a long time on lazy objects
        # so perhaps we just have a whitelist of things it is safe to call on?
        return None

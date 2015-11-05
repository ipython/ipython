"""Function signature objects for callables.

Use the standard library version if available, as it is more up to date.
Fallback on backport otherwise.
"""


try:
    from inspect import BoundArguments, Parameter, Signature, signature
except ImportError:
    from ._signatures import  BoundArguments, Parameter, Signature, signature

"""Decorator for warning about deprecated widget classes"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from warnings import warn


def DeprecatedClass(base, class_name):
    """Warn about a deprecated class on instantiation"""
    # Hook the init method of the base class.
    def init_hook(self, *pargs, **kwargs):
        base.__init__(self, *pargs, **kwargs)

        # Warn once per class.
        if base not in DeprecatedClass._warned_classes:
            DeprecatedClass._warned_classes.append(base)
            warn('"{}" is deprecated, please use "{}" instead.'.format(
                class_name, base.__name__))
    return type(class_name, (base,), {'__init__': init_hook})

DeprecatedClass._warned_classes = []

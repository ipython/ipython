import os
from pathlib import Path

from traitlets.traitlets import TraitType


class PathObject(TraitType):
    """A trait for unicode strings."""

    default_value = Path()
    info_text = "a path-like object"

    def validate(self, obj, value):
        if isinstance(value, os.PathLike):
            return value
        if isinstance(value, str):
            return Path(value)
        self.error(obj, value)

    def from_string(self, s):
        if self.allow_none and s == "None":
            return None
        return Path(s)

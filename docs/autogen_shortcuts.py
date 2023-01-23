from dataclasses import dataclass
from inspect import getsource
from pathlib import Path
from typing import cast, Callable, List, Union
from html import escape as html_escape
import re

from prompt_toolkit.keys import KEY_ALIASES
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.filters import Filter, Condition
from prompt_toolkit.shortcuts import PromptSession

from IPython.terminal.shortcuts import create_ipython_shortcuts


@dataclass
class Shortcut:
    #: a sequence of keys (each element on the list corresponds to pressing one or more keys)
    keys_sequence: list[str]
    filter: str


@dataclass
class Handler:
    description: str
    identifier: str


@dataclass
class Binding:
    handler: Handler
    shortcut: Shortcut


class _NestedFilter(Filter):
    """Protocol reflecting non-public prompt_toolkit's `_AndList` and `_OrList`."""

    filters: List[Filter]


class _Invert(Filter):
    """Protocol reflecting non-public prompt_toolkit's `_Invert`."""

    filter: Filter


conjunctions_labels = {"_AndList": "and", "_OrList": "or"}

ATOMIC_CLASSES = {"Never", "Always", "Condition"}


def format_filter(
    filter_: Union[Filter, _NestedFilter, Condition, _Invert],
    is_top_level=True,
    skip=None,
) -> str:
    """Create easily readable description of the filter."""
    s = filter_.__class__.__name__
    if s == "Condition":
        func = cast(Condition, filter_).func
        name = func.__name__
        if name == "<lambda>":
            source = getsource(func)
            return source.split("=")[0].strip()
        return func.__name__
    elif s == "_Invert":
        operand = cast(_Invert, filter_).filter
        if operand.__class__.__name__ in ATOMIC_CLASSES:
            return f"not {format_filter(operand, is_top_level=False)}"
        return f"not ({format_filter(operand, is_top_level=False)})"
    elif s in conjunctions_labels:
        filters = cast(_NestedFilter, filter_).filters
        conjunction = conjunctions_labels[s]
        glue = f" {conjunction} "
        result = glue.join(format_filter(x, is_top_level=False) for x in filters)
        if len(filters) > 1 and not is_top_level:
            result = f"({result})"
        return result
    elif s in ["Never", "Always"]:
        return s.lower()
    else:
        raise ValueError(f"Unknown filter type: {filter_}")


def sentencize(s) -> str:
    """Extract first sentence"""
    s = re.split(r"\.\W", s.replace("\n", " ").strip())
    s = s[0] if len(s) else ""
    if not s.endswith("."):
        s += "."
    try:
        return " ".join(s.split())
    except AttributeError:
        return s


class _DummyTerminal:
    """Used as a buffer to get prompt_toolkit bindings
    """
    handle_return = None
    input_transformer_manager = None
    display_completions = None
    editing_mode = "emacs"
    auto_suggest = None


def create_identifier(handler: Callable):
    parts = handler.__module__.split(".")
    name = handler.__name__
    package = parts[0]
    if len(parts) > 1:
        final_module = parts[-1]
        return f"{package}:{final_module}.{name}"
    else:
        return f"{package}:{name}"


def bindings_from_prompt_toolkit(prompt_bindings: KeyBindingsBase) -> List[Binding]:
    """Collect bindings to a simple format that does not depend on prompt-toolkit internals"""
    bindings: List[Binding] = []

    for kb in prompt_bindings.bindings:
        bindings.append(
            Binding(
                handler=Handler(
                    description=kb.handler.__doc__ or "",
                    identifier=create_identifier(kb.handler),
                ),
                shortcut=Shortcut(
                    keys_sequence=[
                        str(k.value) if hasattr(k, "value") else k for k in kb.keys
                    ],
                    filter=format_filter(kb.filter, skip={"has_focus_filter"}),
                ),
            )
        )
    return bindings


INDISTINGUISHABLE_KEYS = {**KEY_ALIASES, **{v: k for k, v in KEY_ALIASES.items()}}


def format_prompt_keys(keys: str, add_alternatives=True) -> str:
    """Format prompt toolkit key with modifier into an RST representation."""

    def to_rst(key):
        escaped = key.replace("\\", "\\\\")
        return f":kbd:`{escaped}`"

    keys_to_press: list[str]

    prefixes = {
        "c-s-": [to_rst("ctrl"), to_rst("shift")],
        "s-c-": [to_rst("ctrl"), to_rst("shift")],
        "c-": [to_rst("ctrl")],
        "s-": [to_rst("shift")],
    }

    for prefix, modifiers in prefixes.items():
        if keys.startswith(prefix):
            remainder = keys[len(prefix) :]
            keys_to_press = [*modifiers, to_rst(remainder)]
            break
    else:
        keys_to_press = [to_rst(keys)]

    result = " + ".join(keys_to_press)

    if keys in INDISTINGUISHABLE_KEYS and add_alternatives:
        alternative = INDISTINGUISHABLE_KEYS[keys]

        result = (
            result
            + " (or "
            + format_prompt_keys(alternative, add_alternatives=False)
            + ")"
        )

    return result

if __name__ == '__main__':
    here = Path(__file__).parent
    dest = here / "source" / "config" / "shortcuts"

    ipy_bindings = create_ipython_shortcuts(_DummyTerminal(), for_all_platforms=True)

    session = PromptSession(key_bindings=ipy_bindings)
    prompt_bindings = session.app.key_bindings

    assert prompt_bindings
    # Ensure that we collected the default shortcuts
    assert len(prompt_bindings.bindings) > len(ipy_bindings.bindings)

    bindings = bindings_from_prompt_toolkit(prompt_bindings)

    def sort_key(binding: Binding):
        return binding.handler.identifier, binding.shortcut.filter

    filters = []
    with (dest / "table.tsv").open("w", encoding="utf-8") as csv:
        for binding in sorted(bindings, key=sort_key):
            sequence = ", ".join(
                [format_prompt_keys(keys) for keys in binding.shortcut.keys_sequence]
            )
            if binding.shortcut.filter == "always":
                condition_label = "-"
            else:
                # we cannot fit all the columns as the filters got too complex over time
                condition_label = "ⓘ"

            csv.write(
                "\t".join(
                    [
                        sequence,
                        sentencize(binding.handler.description)
                        + f" :raw-html:`<br>` `{binding.handler.identifier}`",
                        f':raw-html:`<span title="{html_escape(binding.shortcut.filter)}" style="cursor: help">{condition_label}</span>`',
                    ]
                )
                + "\n"
            )

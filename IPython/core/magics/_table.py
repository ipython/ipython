"""Static description of the magics IPython ships with.

Importing a magics module and instantiating the ``Magics`` classes it defines
is expensive, and most magics are never used in a given session, so IPython
declares its own to ``MagicsManager.lazy_magics`` instead of registering them.

These tables are therefore hand maintained. ``tests/test_magic_table.py``
imports every magics module, instantiates every ``Magics`` subclass, and fails
-- printing the corrected table -- if anything here has drifted.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import os
import typing as t

if t.TYPE_CHECKING:
    from traitlets.config import Config


#: Public name re-exported by :mod:`IPython.core.magics` -> module defining it,
#: for that package's ``__getattr__``.
MAGICS_CLASSES: dict[str, str] = {
    "AsyncMagics": "IPython.core.magics.basic",
    "AutoMagics": "IPython.core.magics.auto",
    "BasicMagics": "IPython.core.magics.basic",
    "CodeMagics": "IPython.core.magics.code",
    "ConfigMagics": "IPython.core.magics.config",
    "DisplayMagics": "IPython.core.magics.display",
    "ExecutionMagics": "IPython.core.magics.execution",
    "ExtensionMagics": "IPython.core.magics.extension",
    "HistoryMagics": "IPython.core.magics.history",
    "LoggingMagics": "IPython.core.magics.logging",
    "MacroToEdit": "IPython.core.magics.code",
    "NamespaceMagics": "IPython.core.magics.namespace",
    "OSMagics": "IPython.core.magics.osm",
    "PackagingMagics": "IPython.core.magics.packaging",
    "PylabMagics": "IPython.core.magics.pylab",
    "ScriptMagics": "IPython.core.magics.script",
}

#: The magics IPython ships with, as ``kind -> {name -> "module:Class"}``, fed
#: to ``MagicsManager.register_lazy`` by ``InteractiveShell.init_magics``.
#: ``ScriptMagics`` also generates a cell magic per configured interpreter,
#: see :func:`configured_script_magics`.
BUILTIN_LAZY_MAGICS: dict[str, dict[str, str]] = {
    "line": {
        # AutoMagics
        "autocall": "IPython.core.magics.auto:AutoMagics",
        "automagic": "IPython.core.magics.auto:AutoMagics",
        # BasicMagics
        "alias_magic": "IPython.core.magics.basic:BasicMagics",
        "colors": "IPython.core.magics.basic:BasicMagics",
        "doctest_mode": "IPython.core.magics.basic:BasicMagics",
        "gui": "IPython.core.magics.basic:BasicMagics",
        "lsmagic": "IPython.core.magics.basic:BasicMagics",
        "magic": "IPython.core.magics.basic:BasicMagics",
        "notebook": "IPython.core.magics.basic:BasicMagics",
        "page": "IPython.core.magics.basic:BasicMagics",
        "pprint": "IPython.core.magics.basic:BasicMagics",
        "precision": "IPython.core.magics.basic:BasicMagics",
        "quickref": "IPython.core.magics.basic:BasicMagics",
        "xmode": "IPython.core.magics.basic:BasicMagics",
        # CodeMagics
        "edit": "IPython.core.magics.code:CodeMagics",
        "load": "IPython.core.magics.code:CodeMagics",
        "loadpy": "IPython.core.magics.code:CodeMagics",
        "pastebin": "IPython.core.magics.code:CodeMagics",
        "save": "IPython.core.magics.code:CodeMagics",
        # ConfigMagics
        "config": "IPython.core.magics.config:ConfigMagics",
        # ExecutionMagics
        "code_wrap": "IPython.core.magics.execution:ExecutionMagics",
        "debug": "IPython.core.magics.execution:ExecutionMagics",
        "macro": "IPython.core.magics.execution:ExecutionMagics",
        "pdb": "IPython.core.magics.execution:ExecutionMagics",
        "prun": "IPython.core.magics.execution:ExecutionMagics",
        "run": "IPython.core.magics.execution:ExecutionMagics",
        "tb": "IPython.core.magics.execution:ExecutionMagics",
        "time": "IPython.core.magics.execution:ExecutionMagics",
        "timeit": "IPython.core.magics.execution:ExecutionMagics",
        # ExtensionMagics
        "load_ext": "IPython.core.magics.extension:ExtensionMagics",
        "reload_ext": "IPython.core.magics.extension:ExtensionMagics",
        "unload_ext": "IPython.core.magics.extension:ExtensionMagics",
        # HistoryMagics
        "history": "IPython.core.magics.history:HistoryMagics",
        "recall": "IPython.core.magics.history:HistoryMagics",
        "rerun": "IPython.core.magics.history:HistoryMagics",
        # LoggingMagics
        "logoff": "IPython.core.magics.logging:LoggingMagics",
        "logon": "IPython.core.magics.logging:LoggingMagics",
        "logstart": "IPython.core.magics.logging:LoggingMagics",
        "logstate": "IPython.core.magics.logging:LoggingMagics",
        "logstop": "IPython.core.magics.logging:LoggingMagics",
        # NamespaceMagics
        "pdef": "IPython.core.magics.namespace:NamespaceMagics",
        "pdoc": "IPython.core.magics.namespace:NamespaceMagics",
        "pfile": "IPython.core.magics.namespace:NamespaceMagics",
        "pinfo": "IPython.core.magics.namespace:NamespaceMagics",
        "pinfo2": "IPython.core.magics.namespace:NamespaceMagics",
        "psearch": "IPython.core.magics.namespace:NamespaceMagics",
        "psource": "IPython.core.magics.namespace:NamespaceMagics",
        "reset": "IPython.core.magics.namespace:NamespaceMagics",
        "reset_selective": "IPython.core.magics.namespace:NamespaceMagics",
        "who": "IPython.core.magics.namespace:NamespaceMagics",
        "who_ls": "IPython.core.magics.namespace:NamespaceMagics",
        "whos": "IPython.core.magics.namespace:NamespaceMagics",
        "xdel": "IPython.core.magics.namespace:NamespaceMagics",
        # OSMagics
        "alias": "IPython.core.magics.osm:OSMagics",
        "bookmark": "IPython.core.magics.osm:OSMagics",
        "cd": "IPython.core.magics.osm:OSMagics",
        "dhist": "IPython.core.magics.osm:OSMagics",
        "dirs": "IPython.core.magics.osm:OSMagics",
        "env": "IPython.core.magics.osm:OSMagics",
        "popd": "IPython.core.magics.osm:OSMagics",
        "pushd": "IPython.core.magics.osm:OSMagics",
        "pwd": "IPython.core.magics.osm:OSMagics",
        "pycat": "IPython.core.magics.osm:OSMagics",
        "rehashx": "IPython.core.magics.osm:OSMagics",
        "sc": "IPython.core.magics.osm:OSMagics",
        "set_env": "IPython.core.magics.osm:OSMagics",
        "sx": "IPython.core.magics.osm:OSMagics",
        "system": "IPython.core.magics.osm:OSMagics",
        "unalias": "IPython.core.magics.osm:OSMagics",
        # PackagingMagics
        "conda": "IPython.core.magics.packaging:PackagingMagics",
        "mamba": "IPython.core.magics.packaging:PackagingMagics",
        "micromamba": "IPython.core.magics.packaging:PackagingMagics",
        "pip": "IPython.core.magics.packaging:PackagingMagics",
        "uv": "IPython.core.magics.packaging:PackagingMagics",
        # PylabMagics
        "matplotlib": "IPython.core.magics.pylab:PylabMagics",
        "pylab": "IPython.core.magics.pylab:PylabMagics",
        # ScriptMagics
        "killbgscripts": "IPython.core.magics.script:ScriptMagics",
        # AsyncMagics
        "autoawait": "IPython.core.magics.basic:AsyncMagics",
    },
    "cell": {
        # DisplayMagics
        "html": "IPython.core.magics.display:DisplayMagics",
        "javascript": "IPython.core.magics.display:DisplayMagics",
        "js": "IPython.core.magics.display:DisplayMagics",
        "latex": "IPython.core.magics.display:DisplayMagics",
        "markdown": "IPython.core.magics.display:DisplayMagics",
        "svg": "IPython.core.magics.display:DisplayMagics",
        # ExecutionMagics
        "capture": "IPython.core.magics.execution:ExecutionMagics",
        "code_wrap": "IPython.core.magics.execution:ExecutionMagics",
        "debug": "IPython.core.magics.execution:ExecutionMagics",
        "prun": "IPython.core.magics.execution:ExecutionMagics",
        "time": "IPython.core.magics.execution:ExecutionMagics",
        "timeit": "IPython.core.magics.execution:ExecutionMagics",
        # OSMagics
        "!": "IPython.core.magics.osm:OSMagics",
        "sx": "IPython.core.magics.osm:OSMagics",
        "system": "IPython.core.magics.osm:OSMagics",
        "writefile": "IPython.core.magics.osm:OSMagics",
        # ScriptMagics
        "script": "IPython.core.magics.script:ScriptMagics",
    },
}


def default_script_magics() -> list[str]:
    """Default value of the ``ScriptMagics.script_magics`` trait.

    Here so the lazy declaration knows the generated ``%%<interpreter>`` names
    without importing :mod:`IPython.core.magics.script`.
    """
    defaults = [
        "sh",
        "bash",
        "perl",
        "ruby",
        "python",
        "python2",
        "python3",
        "pypy",
    ]
    if os.name == "nt":
        defaults.extend(
            [
                "cmd",
            ]
        )

    return defaults


def configured_script_magics(config: Config | None) -> list[str]:
    """Cell magic names ``ScriptMagics`` will provide for the given config.

    Peeks at the config rather than instantiating the class, which is what we
    are trying to avoid.
    """
    section = getattr(config, "ScriptMagics", None) if config is not None else None
    if section is not None and "script_magics" in section:
        return list(section["script_magics"])
    return default_script_magics()

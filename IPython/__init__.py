# PYTHON_ARGCOMPLETE_OK
"""
IPython: tools for interactive and parallel computing in Python.

https://ipython.org
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2008-2011, IPython Development Team.
#  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import warnings
from typing import Any

#-----------------------------------------------------------------------------
# Setup everything
#-----------------------------------------------------------------------------

# Don't forget to also update setup.py when this changes!
#
# NOTE: these imports look like they could be made lazy (PEP 562) to speed up
# `import IPython` considerably, but downstream projects (pyflyby at least)
# rely on the transitive side effects: they do `import IPython` and then
# access attribute chains like `IPython.terminal.ipapp.TerminalIPythonApp`,
# which only resolve because the imports below load those submodules.
#
# `embed`, `Application` and `get_ipython` are the exceptions, and are
# deferred via module `__getattr__` below:
#
#  - `embed` drags in the whole terminal / prompt_toolkit stack, by far
#    the most expensive of these imports, and is only needed by code that
#    calls `IPython.embed()`;
#  - `Application` is only a re-export of `traitlets.config.application
#    .Application`, but importing it pulled in `IPython.core.application`
#    and with it the crash handler; no known downstream imports it from
#    here (ipykernel imports `BaseIPythonApplication` from
#    `IPython.core.application` directly);
#  - `get_ipython` costs nothing to defer -- `IPython.core.getipython`
#    ends up imported anyway via `IPython.core.magic` -- but is kept
#    alongside the others so all three top-level names resolve the same
#    way.
#
# This does mean that code relying on `import IPython` to transitively
# populate `IPython.terminal.embed` / `IPython.core.application` (or
# submodules only reachable through them) as a side effect will need to
# import those submodules explicitly instead. `Application` raises a
# `DeprecationWarning` when accessed here, both because such code is worth
# spotting and because the name should be imported from traitlets;
# `embed` and `get_ipython` stay silent, being widely and legitimately
# used from here.
from .core import release

from .core.interactiveshell import InteractiveShell
from .utils.sysinfo import sys_info
from .utils.frame import extract_module_locals

__all__ = ["start_ipython", "embed", "embed_kernel"]


# Nothing below is cached in `globals()`: the lookups stay lazy on every
# access, so that the `Application` warning keeps firing instead of only
# on the first access, and so that these names never silently turn into
# plain module attributes that later code could mistake for eagerly
# imported ones.
#
# `Application` is deliberately absent from `_lazy_attrs`, and hence from
# `__dir__`: anything that walks `dir(IPython)` and getattr()s the result
# -- our own module completer does, and so do other introspection tools --
# would otherwise trigger its `DeprecationWarning` without any code
# actually wanting the name. Explicit `IPython.Application` access still
# resolves, and still warns, which is the access we want to hear about.
_lazy_attrs = frozenset({"embed", "get_ipython"})


def __getattr__(name: str) -> Any:
    if name == "embed":
        from .terminal.embed import embed

        return embed
    if name == "get_ipython":
        from .core.getipython import get_ipython

        return get_ipython
    if name == "Application":
        warnings.warn(
            "`IPython.Application` is only a re-export of"
            " `traitlets.config.application.Application`; import it from"
            " traitlets directly. Accessing it here triggers an import of"
            " `IPython.core.application`, which is no longer imported when"
            " IPython is -- import that module explicitly if you rely on"
            " that import happening, in particular if you also rely on other"
            " submodules being transitively imported as a side effect.",
            DeprecationWarning,
            stacklevel=2,
        )
        from .core.application import Application

        return Application
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return [*globals(), *_lazy_attrs]

# Release data
__author__ = '{} <{}>'.format(release.author, release.author_email)
__license__  = release.license
__version__  = release.version
version_info = release.version_info
# list of CVEs that should have been patched in this release.
# this is informational and should not be relied upon.
__patched_cves__ = {"CVE-2022-21699", "CVE-2023-24816"}


def embed_kernel(module=None, local_ns=None, **kwargs):
    """Embed and start an IPython kernel in a given scope.

    If you don't want the kernel to initialize the namespace
    from the scope of the surrounding function,
    and/or you want to load full IPython configuration,
    you probably want `IPython.start_kernel()` instead.

    This is a deprecated alias for `ipykernel.embed.embed_kernel()`,
    to be removed in the future.
    You should import directly from `ipykernel.embed`; this wrapper
    fails anyway if you don't have `ipykernel` package installed.

    Parameters
    ----------
    module : types.ModuleType, optional
        The module to load into IPython globals (default: caller)
    local_ns : dict, optional
        The namespace to load into IPython user namespace (default: caller)
    **kwargs : various, optional
        Further keyword args are relayed to the IPKernelApp constructor,
        such as `config`, a traitlets :class:`Config` object (see :ref:`configure_start_ipython`),
        allowing configuration of the kernel.  Will only have an effect
        on the first embed_kernel call for a given process.
    """

    warnings.warn(
        "import embed_kernel from ipykernel.embed directly (since 2013)."
        " Importing from IPython will be removed in the future",
        DeprecationWarning,
        stacklevel=2,
    )

    (caller_module, caller_locals) = extract_module_locals(1)
    if module is None:
        module = caller_module
    if local_ns is None:
        local_ns = dict(**caller_locals)

    # Only import .zmq when we really need it
    from ipykernel.embed import embed_kernel as real_embed_kernel
    real_embed_kernel(module=module, local_ns=local_ns, **kwargs)

def start_ipython(argv: list[str] | None = None, **kwargs: Any) -> Any:
    """Launch a normal IPython instance (as opposed to embedded)

    `IPython.embed()` puts a shell in a particular calling scope,
    such as a function or method for debugging purposes,
    which is often not desirable.

    `start_ipython()` does full, regular IPython initialization,
    including loading startup files, configuration, etc.
    much of which is skipped by `embed()`.

    This is a public API method, and will survive implementation changes.

    Parameters
    ----------
    argv : list or None, optional
        If unspecified or None, IPython will parse command-line options from sys.argv.
        To prevent any command-line parsing, pass an empty list: `argv=[]`.
    user_ns : dict, optional
        specify this dictionary to initialize the IPython user namespace with particular values.
    **kwargs : various, optional
        Any other kwargs will be passed to the Application constructor,
        such as `config`, a traitlets :class:`Config` object (see :ref:`configure_start_ipython`),
        allowing configuration of the instance (see :ref:`terminal_options`).
    """
    from IPython.terminal.ipapp import launch_new_instance
    return launch_new_instance(argv=argv, **kwargs)

# -*- coding: utf-8 -*-
"""DEPRECATED: old import location of TerminalInteractiveShell"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from warnings import warn

from IPython.utils.decorators import undoc
from .ptshell import TerminalInteractiveShell as PromptToolkitShell

warn("Since IPython 5.0 `IPython.terminal.interactiveshell` is deprecated in favor of `IPython.terminal.ptshell`.",
      DeprecationWarning)

@undoc
class TerminalInteractiveShell(PromptToolkitShell):
    def __init__(self, *args, **kwargs):
        warn("Since IPython 5.0 this is a deprecated alias for IPython.terminal.ptshell.TerminalInteractiveShell. "
             "The terminal interface of this class now uses prompt_toolkit instead of readline.",
             DeprecationWarning, stacklevel=2)
        PromptToolkitShell.__init__(self, *args, **kwargs)

# -*- coding: utf-8 -*-
"""DEPRECATED: old import location of TerminalInteractiveShell"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from warnings import warn

from IPython.utils.decorators import undoc
from .ptshell import TerminalInteractiveShell as PromptToolkitShell

@undoc
class TerminalInteractiveShell(PromptToolkitShell):
    def __init__(self, *args, **kwargs):
        warn("This is a deprecated alias for IPython.terminal.ptshell.TerminalInteractiveShell. "
             "The terminal interface of this class now uses prompt_toolkit instead of readline.",
             DeprecationWarning, stacklevel=2)
        PromptToolkitShell.__init__(self, *args, **kwargs)

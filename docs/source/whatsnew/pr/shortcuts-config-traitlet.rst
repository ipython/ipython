Terminal shortcuts customization
================================

Previously modifying shortcuts was only possible by hooking into startup files
and practically limited to adding new shortcuts or removing all shortcuts bound
to a specific key. This release enables users to override existing terminal
shortcuts, disable them or add new keybindings.

For example, to set the :kbd:`right` to accept a single character of auto-suggestion
you could use::

    my_shortcuts = [
        {
            "command": "IPython:auto_suggest.accept_character",
            "new_keys": ["right"]
        }
    ]
    %config TerminalInteractiveShell.shortcuts = my_shortcuts

You can learn more in :std:configtrait:`TerminalInteractiveShell.shortcuts`
configuration reference.
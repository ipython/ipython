import asyncio
import signal
import sys

from IPython.core.debugger import Pdb

from IPython.core.completer import IPCompleter
from .ptutils import IPythonPTCompleter
from .shortcuts import suspend_to_bg, cursor_in_leading_ws

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import (Condition, has_focus, has_selection,
    vi_insert_mode, emacs_insert_mode)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline
from pygments.token import Token
from prompt_toolkit.shortcuts.prompt import PromptSession
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import PygmentsTokens

from prompt_toolkit import __version__ as ptk_version
PTK3 = ptk_version.startswith('3.')


class TerminalPdb(Pdb):
    """Standalone IPython debugger."""

    def __init__(self, *args, **kwargs):
        Pdb.__init__(self, *args, **kwargs)
        self._ptcomp = None
        self.pt_init()

    def pt_init(self):
        def get_prompt_tokens():
            return [(Token.Prompt, self.prompt)]

        if self._ptcomp is None:
            compl = IPCompleter(shell=self.shell,
                                        namespace={},
                                        global_namespace={},
                                        parent=self.shell,
                                       )
            self._ptcomp = IPythonPTCompleter(compl)

        kb = KeyBindings()
        supports_suspend = Condition(lambda: hasattr(signal, 'SIGTSTP'))
        kb.add('c-z', filter=supports_suspend)(suspend_to_bg)

        if self.shell.display_completions == 'readlinelike':
            kb.add('tab', filter=(has_focus(DEFAULT_BUFFER)
                                  & ~has_selection
                                  & vi_insert_mode | emacs_insert_mode
                                  & ~cursor_in_leading_ws
                              ))(display_completions_like_readline)

        options = dict(
            message=(lambda: PygmentsTokens(get_prompt_tokens())),
            editing_mode=getattr(EditingMode, self.shell.editing_mode.upper()),
            key_bindings=kb,
            history=self.shell.debugger_history,
            completer=self._ptcomp,
            enable_history_search=True,
            mouse_support=self.shell.mouse_support,
            complete_style=self.shell.pt_complete_style,
            style=self.shell.style,
            color_depth=self.shell.color_depth,
        )

        if not PTK3:
            options['inputhook'] = self.shell.inputhook
        self.pt_loop = asyncio.new_event_loop()
        self.pt_app = PromptSession(**options)

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        override the same methods from cmd.Cmd to provide prompt toolkit replacement.
        """
        if not self.use_rawinput:
            raise ValueError('Sorry ipdb does not support use_rawinput=False')

        # In order to make sure that asyncio code written in the
        # interactive shell doesn't interfere with the prompt, we run the
        # prompt in a different event loop.
        # If we don't do this, people could spawn coroutine with a
        # while/true inside which will freeze the prompt.

        try:
            old_loop = asyncio.get_event_loop()
        except RuntimeError:
            # This happens when the user used `asyncio.run()`.
            old_loop = None


        self.preloop()

        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    self._ptcomp.ipy_completer.namespace = self.curframe_locals
                    self._ptcomp.ipy_completer.global_namespace = self.curframe.f_globals

                    asyncio.set_event_loop(self.pt_loop)
                    try:
                        line = self.pt_app.prompt()
                    except EOFError:
                        line = 'EOF'
                    finally:
                        # Restore the original event loop.
                        asyncio.set_event_loop(old_loop)

                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        except Exception:
            raise


def set_trace(frame=None):
    """
    Start debugging from `frame`.

    If frame is not specified, debugging starts from caller's frame.
    """
    TerminalPdb().set_trace(frame or sys._getframe().f_back)


if __name__ == '__main__':
    import pdb
    # IPython.core.debugger.Pdb.trace_dispatch shall not catch
    # bdb.BdbQuit. When started through __main__ and an exception
    # happened after hitting "c", this is needed in order to
    # be able to quit the debugging session (see #9950).
    old_trace_dispatch = pdb.Pdb.trace_dispatch
    pdb.Pdb = TerminalPdb
    pdb.Pdb.trace_dispatch = old_trace_dispatch
    pdb.main()

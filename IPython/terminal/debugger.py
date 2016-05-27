from IPython.core.debugger import Pdb

from IPython.core.completer import IPCompleter
from .ptutils import IPythonPTCompleter

from prompt_toolkit.token import Token
from prompt_toolkit.shortcuts import create_prompt_application
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.enums import EditingMode

class TerminalPdb(Pdb):
    def __init__(self, *args, **kwargs):
        Pdb.__init__(self, *args, **kwargs)
        self._ptcomp = None
        self.pt_init()

    def pt_init(self):
        def get_prompt_tokens(cli):
            return [(Token.Prompt, self.prompt)]

        if self._ptcomp is None:
            compl = IPCompleter(shell=self.shell,
                                        namespace={},
                                        global_namespace={},
                                        use_readline=False,
                                        parent=self.shell,
                                       )
            self._ptcomp = IPythonPTCompleter(compl)

        self._pt_app = create_prompt_application(
                            editing_mode=getattr(EditingMode, self.shell.editing_mode.upper()),
                            history=self.shell.debugger_history,
                            completer= self._ptcomp,
                            enable_history_search=True,
                            mouse_support=self.shell.mouse_support,
                            get_prompt_tokens=get_prompt_tokens
        )
        self.pt_cli = CommandLineInterface(self._pt_app, eventloop=self.shell._eventloop)

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        override the same methods from cmd.Cmd to provide prompt toolkit replacement.
        """
        if not self.use_rawinput:
            raise ValueError('Sorry ipdb does not support use_rawinput=False')

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
                    try:
                        line = self.pt_cli.run(reset_current_buffer=True).text
                    except EOFError:
                        line = 'EOF'
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        except Exception:
            raise

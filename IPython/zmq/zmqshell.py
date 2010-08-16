import sys
from subprocess import Popen, PIPE
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC


class ZMQInteractiveShell(InteractiveShell):
    """A subclass of InteractiveShell for ZMQ."""

    def system(self, cmd):
        cmd = self.var_expand(cmd, depth=2)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        for line in p.stdout.read().split('\n'):
            if len(line) > 0:
                print line
        for line in p.stderr.read().split('\n'):
            if len(line) > 0:
                print line
        return p.wait()

InteractiveShellABC.register(ZMQInteractiveShell)

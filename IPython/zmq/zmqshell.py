import sys
from subprocess import Popen, PIPE
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC


class ZMQInteractiveShell(InteractiveShell):
    """A subclass of InteractiveShell for ZMQ."""

    def system(self, cmd):
        cmd = self.var_expand(cmd, depth=2)
        sys.stdout.flush()
        sys.stderr.flush()
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        for line in p.stdout.read().split('\n'):
            if len(line) > 0:
                print line
        for line in p.stderr.read().split('\n'):
            if len(line) > 0:
                print line
        p.wait()

    def init_io(self):
        # This will just use sys.stdout and sys.stderr. If you want to
        # override sys.stdout and sys.stderr themselves, you need to do that
        # *before* instantiating this class, because Term holds onto 
        # references to the underlying streams.
        import IPython.utils.io
        Term = IPython.utils.io.IOTerm()
        IPython.utils.io.Term = Term

InteractiveShellABC.register(ZMQInteractiveShell)

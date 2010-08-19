import sys
from subprocess import Popen, PIPE

from IPython.core.interactiveshell import (
    InteractiveShell, InteractiveShellABC
)
from IPython.core.displayhook import DisplayHook
from IPython.utils.traitlets import Instance, Type, Dict
from IPython.zmq.session import extract_header


class ZMQDisplayHook(DisplayHook):

    session = Instance('IPython.zmq.session.Session')
    pub_socket = Instance('zmq.Socket')
    parent_header = Dict({})

    def set_parent(self, parent):
        """Set the parent for outbound messages."""
        self.parent_header = extract_header(parent)

    def start_displayhook(self):
        self.msg = self.session.msg(u'pyout', {}, parent=self.parent_header)

    def write_output_prompt(self):
        """Write the output prompt."""
        if self.do_full_cache:
            self.msg['content']['output_sep'] = self.output_sep
            self.msg['content']['prompt_string'] = str(self.prompt_out)
            self.msg['content']['prompt_number'] = self.prompt_count
            self.msg['content']['output_sep2'] = self.output_sep2

    def write_result_repr(self, result_repr):
        self.msg['content']['data'] = result_repr

    def finish_displayhook(self):
        """Finish up all displayhook activities."""
        self.pub_socket.send_json(self.msg)
        self.msg = None


class ZMQInteractiveShell(InteractiveShell):
    """A subclass of InteractiveShell for ZMQ."""

    displayhook_class = Type(ZMQDisplayHook)

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




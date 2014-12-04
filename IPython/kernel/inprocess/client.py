"""A client for in-process kernels."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# IPython imports
from IPython.kernel.inprocess.socket import DummySocket
from IPython.utils.traitlets import Type, Instance
from IPython.kernel.clientabc import KernelClientABC
from IPython.kernel.client import KernelClient

# Local imports
from .channels import (
    InProcessChannel,
    InProcessHBChannel,

)

#-----------------------------------------------------------------------------
# Main kernel Client class
#-----------------------------------------------------------------------------

class InProcessKernelClient(KernelClient):
    """A client for an in-process kernel.

    This class implements the interface of
    `IPython.kernel.clientabc.KernelClientABC` and allows
    (asynchronous) frontends to be used seamlessly with an in-process kernel.

    See `IPython.kernel.client.KernelClient` for docstrings.
    """

    # The classes to use for the various channels.
    shell_channel_class = Type(InProcessChannel)
    iopub_channel_class = Type(InProcessChannel)
    stdin_channel_class = Type(InProcessChannel)
    hb_channel_class = Type(InProcessHBChannel)

    kernel = Instance('IPython.kernel.inprocess.ipkernel.InProcessKernel')

    #--------------------------------------------------------------------------
    # Channel management methods
    #--------------------------------------------------------------------------

    def start_channels(self, *args, **kwargs):
        super(InProcessKernelClient, self).start_channels(self)
        self.kernel.frontends.append(self)

    @property
    def shell_channel(self):
        if self._shell_channel is None:
            self._shell_channel = self.shell_channel_class(self)
        return self._shell_channel

    @property
    def iopub_channel(self):
        if self._iopub_channel is None:
            self._iopub_channel = self.iopub_channel_class(self)
        return self._iopub_channel

    @property
    def stdin_channel(self):
        if self._stdin_channel is None:
            self._stdin_channel = self.stdin_channel_class(self)
        return self._stdin_channel

    @property
    def hb_channel(self):
        if self._hb_channel is None:
            self._hb_channel = self.hb_channel_class(self)
        return self._hb_channel

    # Methods for sending specific messages
    # -------------------------------------

    def execute(self, code, silent=False, store_history=True,
                user_expressions={}, allow_stdin=None):
        if allow_stdin is None:
            allow_stdin = self.allow_stdin
        content = dict(code=code, silent=silent, store_history=store_history,
                       user_expressions=user_expressions,
                       allow_stdin=allow_stdin)
        msg = self.session.msg('execute_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def complete(self, code, cursor_pos=None):
        if cursor_pos is None:
            cursor_pos = len(code)
        content = dict(code=code, cursor_pos=cursor_pos)
        msg = self.session.msg('complete_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def inspect(self, code, cursor_pos=None, detail_level=0):
        if cursor_pos is None:
            cursor_pos = len(code)
        content = dict(code=code, cursor_pos=cursor_pos,
            detail_level=detail_level,
        )
        msg = self.session.msg('inspect_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def history(self, raw=True, output=False, hist_access_type='range', **kwds):
        content = dict(raw=raw, output=output,
                       hist_access_type=hist_access_type, **kwds)
        msg = self.session.msg('history_request', content)
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def shutdown(self, restart=False):
        # FIXME: What to do here?
        raise NotImplementedError('Cannot shutdown in-process kernel')

    def kernel_info(self):
        """Request kernel info."""
        msg = self.session.msg('kernel_info_request')
        self._dispatch_to_kernel(msg)
        return msg['header']['msg_id']

    def input(self, string):
        if self.kernel is None:
            raise RuntimeError('Cannot send input reply. No kernel exists.')
        self.kernel.raw_input_str = string


    def _dispatch_to_kernel(self, msg):
        """ Send a message to the kernel and handle a reply.
        """
        kernel = self.kernel
        if kernel is None:
            raise RuntimeError('Cannot send request. No kernel exists.')

        stream = DummySocket()
        self.session.send(stream, msg)
        msg_parts = stream.recv_multipart()
        kernel.dispatch_shell(stream, msg_parts)

        idents, reply_msg = self.session.recv(stream, copy=False)
        self.shell_channel.call_handlers_later(reply_msg)


#-----------------------------------------------------------------------------
# ABC Registration
#-----------------------------------------------------------------------------

KernelClientABC.register(InProcessKernelClient)

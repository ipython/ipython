"""Base class to manage comms"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config import LoggingConfigurable
from IPython.core.prompts import LazyEvaluate
from IPython.core.getipython import get_ipython

from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Instance, Unicode, Dict, Any

from .comm import Comm

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def lazy_keys(dikt):
    """Return lazy-evaluated string representation of a dictionary's keys
    
    Key list is only constructed if it will actually be used.
    Used for debug-logging.
    """
    return LazyEvaluate(lambda d: list(d.keys()))


class CommManager(LoggingConfigurable):
    """Manager for Comms in the Kernel"""
    
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    def _shell_default(self):
        return get_ipython()
    iopub_socket = Any()
    def _iopub_socket_default(self):
        return self.shell.parent.iopub_socket
    session = Instance('IPython.kernel.zmq.session.Session')
    def _session_default(self):
        if self.shell is None:
            return
        return self.shell.parent.session
    
    comms = Dict()
    targets = Dict()
    
    # Public APIs
    
    def register_target(self, target, f):
        """Register a callable f for a given target
        
        f will be called with a Comm object as its only argument
        when a comm_open message is received with `target`.
        
        f can be a Python callable or an import string for one.
        """
        if isinstance(f, basestring):
            f = import_item(f)
        
        self.targets[target] = f
    
    def register_comm(self, comm):
        """Register a new comm"""
        comm_id = comm.comm_id
        comm.shell = self.shell
        comm.iopub_socket = self.iopub_socket
        self.comms[comm_id] = comm
        return comm_id
    
    def unregister_comm(self, comm_id):
        """Unregister a comm, and close its counterpart"""
        # unlike get_comm, this should raise a KeyError
        comm = self.comms.pop(comm_id)
        comm.close()
    
    def get_comm(self, comm_id):
        """Get a comm with a particular id
        
        Returns the comm if found, otherwise None.
        
        This will not raise an error,
        it will log messages if the comm cannot be found.
        """
        if comm_id not in self.comms:
            self.log.error("No such comm: %s", comm_id)
            self.log.debug("Current comms: %s", lazy_keys(self.comms))
            return
        # call, because we store weakrefs
        comm = self.comms[comm_id]
        return comm
    
    # Message handlers
    
    def comm_open(self, stream, ident, msg):
        """Handler for comm_open messages"""
        content = msg['content']
        comm_id = content['comm_id']
        target = content['target']
        callback = self.targets.get(target, None)
        comm = Comm(comm_id=comm_id,
                    shell=self.shell,
                    iopub_socket=self.iopub_socket,
                    _open_data=content['data'],
                    primary=False,
        )
        if callback is None:
            self.log.error("No such comm target registered: %s", target)
            comm.close()
            return
        callback(comm)
        self.register_comm(comm)
    
    def comm_msg(self, stream, ident, msg):
        """Handler for comm_msg messages"""
        content = msg['content']
        comm_id = content['comm_id']
        comm = self.get_comm(comm_id)
        if comm is None:
            # no such comm
            return
        comm.handle_msg(content['data'])
    
    def comm_close(self, stream, ident, msg):
        """Handler for comm_close messages"""
        content = msg['content']
        comm_id = content['comm_id']
        comm = self.get_comm(comm_id)
        if comm is None:
            # no such comm
            return
        comm.handle_close(content['data'])
        del self.comms[comm_id]


__all__ = ['CommManager']

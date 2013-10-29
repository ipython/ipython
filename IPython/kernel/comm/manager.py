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

import sys

from IPython.config import LoggingConfigurable
from IPython.core.prompts import LazyEvaluate
from IPython.core.getipython import get_ipython

from IPython.utils.importstring import import_item
from IPython.utils.py3compat import string_types
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


def with_output(method):
    """method decorator for ensuring output is handled properly in a message handler
    
    - sets parent header before entering the method
    - publishes busy/idle
    - flushes stdout/stderr after
    """
    def method_with_output(self, stream, ident, msg):
        parent = msg['header']
        self.shell.set_parent(parent)
        self.shell.kernel._publish_status('busy', parent)
        try:
            return method(self, stream, ident, msg)
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            self.shell.kernel._publish_status('idle', parent)
    
    return method_with_output


class CommManager(LoggingConfigurable):
    """Manager for Comms in the Kernel"""
    
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    def _shell_default(self):
        return get_ipython()
    iopub_socket = Any()
    def _iopub_socket_default(self):
        return self.shell.kernel.iopub_socket
    session = Instance('IPython.kernel.zmq.session.Session')
    def _session_default(self):
        if self.shell is None:
            return
        return self.shell.kernel.session
    
    comms = Dict()
    targets = Dict()
    
    # Public APIs
    
    def register_target(self, target_name, f):
        """Register a callable f for a given target name
        
        f will be called with two arguments when a comm_open message is received with `target`:
        
        - the Comm instance
        - the `comm_open` message itself.
        
        f can be a Python callable or an import string for one.
        """
        if isinstance(f, string_types):
            f = import_item(f)
        
        self.targets[target_name] = f
    
    def unregister_target(self, target_name, f):
        """Unregister a callable registered with register_target"""
        return self.targets.pop(target_name);
    
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
    @with_output
    def comm_open(self, stream, ident, msg):
        """Handler for comm_open messages"""
        content = msg['content']
        comm_id = content['comm_id']
        target_name = content['target_name']
        f = self.targets.get(target_name, None)
        comm = Comm(comm_id=comm_id,
                    shell=self.shell,
                    iopub_socket=self.iopub_socket,
                    primary=False,
        )
        if f is None:
            self.log.error("No such comm target registered: %s", target_name)
            comm.close()
            return
        self.register_comm(comm)
        try:
            f(comm, msg)
        except Exception:
            self.log.error("Exception opening comm with target: %s", target_name, exc_info=True)
            comm.close()
            self.unregister_comm(comm_id)
    
    @with_output
    def comm_msg(self, stream, ident, msg):
        """Handler for comm_msg messages"""
        content = msg['content']
        comm_id = content['comm_id']
        comm = self.get_comm(comm_id)
        if comm is None:
            # no such comm
            return
        try:
            comm.handle_msg(msg)
        except Exception:
            self.log.error("Exception in comm_msg for %s", comm_id, exc_info=True)
    
    @with_output
    def comm_close(self, stream, ident, msg):
        """Handler for comm_close messages"""
        content = msg['content']
        comm_id = content['comm_id']
        comm = self.get_comm(comm_id)
        if comm is None:
            # no such comm
            self.log.debug("No such comm to close: %s", comm_id)
            return
        del self.comms[comm_id]
        
        try:
            comm.handle_close(msg)
        except Exception:
            self.log.error("Exception handling comm_close for %s", comm_id, exc_info=True)


__all__ = ['CommManager']

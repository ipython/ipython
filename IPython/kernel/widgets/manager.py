"""Base class to manage widgets"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from weakref import ref

from IPython.config import LoggingConfigurable
from IPython.core.prompts import LazyEvaluate
from IPython.core.getipython import get_ipython
from IPython.utils.traitlets import Instance, Unicode, Dict, Any

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def lazy_keys(dikt):
    """Return lazy-evaluated string representation of a dictionary's keys
    
    Key list is only constructed if it will actually be used.
    Used for debug-logging.
    """
    return LazyEvaluate(lambda d: list(d.keys()))

class WidgetManager(LoggingConfigurable):
    """Manager for Widgets in the Kernel"""
    
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
    
    widgets = Dict()
    
    # Public APIs
    
    def register_widget(self, widget):
        """Register a new widget"""
        self.widgets[widget.widget_id] = ref(widget)
        widget.shell = self.shell
        widget.iopub_socket = self.iopub_socket
        widget.create()
        return widget.widget_id
    
    def unregister_widget(self, widget_id):
        """Unregister a widget, and destroy its counterpart"""
        # unlike get_widget, this should raise a KeyError
        widget_ref = self.widgets.pop(widget_id)
        widget = widget_ref()
        if widget is None:
            # already destroyed, nothing to do
            return
        widget.destroy()
    
    def get_widget(self, widget_id):
        """Get a widget with a particular id
        
        Returns the widget if found, otherwise None.
        
        This will not raise an error,
        it will log messages if the widget cannot be found.
        """
        if widget_id not in self.widgets:
            self.log.error("No such widget: %s", widget_id)
            self.log.debug("Current widgets: %s", lazy_keys(self.widgets))
            return
        # call, because we store weakrefs
        widget = self.widgets[widget_id]()
        if widget is None:
            self.log.error("Widget %s has been removed", widget_id)
            del self.widgets[widget_id]
            self.log.debug("Current widgets: %s", lazy_keys(self.widgets))
            return
        return widget
    
    # Message handlers
    
    def widget_update(self, stream, ident, msg):
        """Handler for widget_update messages"""
        content = msg['content']
        widget_id = content['widget_id']
        widget = self.get_widget(widget_id)
        if widget is None:
            # no such widget
            return
        widget.handle_update(content['data'])
    
    def widget_destroy(self, stream, ident, msg):
        """Handler for widget_destroy messages"""
        content = msg['content']
        widget_id = content['widget_id']
        widget = self.get_widget(widget_id)
        if widget is None:
            # no such widget
            return
        widget.handle_destroy(content['data'])
        del self.widgets[widget_id]
    

__all__ = ['WidgetManager']

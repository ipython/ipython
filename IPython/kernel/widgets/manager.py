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

from IPython.config import LoggingConfigurable
from IPython.core.prompts import LazyEvaluate
from IPython.core.getipython import get_ipython

from IPython.utils.importstring import import_item
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
    widget_types = Dict()
    
    # Public APIs
    
    def register_widget_type(self, widget_type, constructor):
        """Register a constructor for a given widget_type
        
        constructor can be a Widget class or an importstring for a Widget class.
        """
        if isinstance(constructor, basestring):
            constructor = import_item(constructor)
        
        self.widget_types[widget_type] = constructor
    
    def register_widget(self, widget):
        """Register a new widget"""
        widget_id = widget.widget_id
        widget.shell = self.shell
        widget.iopub_socket = self.iopub_socket
        self.widgets[widget_id] = widget
        return widget_id
    
    def unregister_widget(self, widget_id):
        """Unregister a widget, and destroy its counterpart"""
        # unlike get_widget, this should raise a KeyError
        widget = self.widgets.pop(widget_id)
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
        widget = self.widgets[widget_id]
        return widget
    
    # Message handlers
    
    def widget_create(self, stream, ident, msg):
        """Handler for widget_update messages"""
        content = msg['content']
        widget_id = content['widget_id']
        widget_type = content['widget_type']
        constructor = self.widget_types.get(widget_type, None)
        if constructor is None:
            self.log.error("No such widget_type registered: %s", widget_type)
            return
        widget = constructor(widget_id=widget_id,
                    shell=self.shell,
                    iopub_socket=self.iopub_socket,
                    _create_data=content['data'],
                    primary=False,
        )
        self.register_widget(widget)
    
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

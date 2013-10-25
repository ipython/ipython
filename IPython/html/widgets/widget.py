"""Base Widget class.  Allows user to create widgets in the backend that render
in the IPython notebook frontend.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from copy import copy
from glob import glob
import uuid
import sys
import os

import IPython
from IPython.kernel.comm import Comm
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import Unicode, Dict, List
from IPython.display import Javascript, display
from IPython.utils.py3compat import string_types

#-----------------------------------------------------------------------------
# Shared
#-----------------------------------------------------------------------------
def init_widget_js():
    path = os.path.split(os.path.abspath( __file__ ))[0]
    for filepath in glob(os.path.join(path, "*.py")):
        filename = os.path.split(filepath)[1]
        name = filename.rsplit('.', 1)[0]
        if not (name == 'widget' or name == '__init__') and name.startswith('widget_'):
            # Remove 'widget_' from the start of the name before compiling the path.
            js_path = '../static/notebook/js/widgets/%s.js' % name[7:]
            display(Javascript(data='$.getScript("%s");' % js_path))  


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class Widget(LoggingConfigurable):

    # Public declarations
    target_name = Unicode('widget', help="""Name of the backbone model 
        registered in the frontend to create and sync this widget with.""")
    default_view_name = Unicode(help="""Default view registered in the frontend
        to use to represent the widget.""")
    
    
    # Private/protected declarations
    _keys = []
    _property_lock = False
    _parent = None
    _children = []
    _css = Dict()
    
    
    def __init__(self, parent=None, **kwargs):
        """Public constructor

        Parameters
        ----------
        parent : Widget instance (optional)
            Widget that this widget instance is child of.  When the widget is
            displayed in the frontend, it's corresponding view will be made
            child of the parent's view if the parent's view exists already.  If
            the parent's view is displayed, it will automatically display this 
            widget's default view as it's child.  The default view can be set
            via the default_view_name property.
        """
        super(Widget, self).__init__(**kwargs)
        
        # Parent/child association
        self._children = []
        if parent is not None:
            parent._children.append(self)
        self._parent = parent
        self.comm = None
        
        # Register after init to allow default values to be specified
        self.on_trait_change(self._handle_property_changed, self.keys)
        
        
    def __del__(self):
        """Object disposal"""
        self.close()
    

    def close(self):
        """Close method.  Closes the widget which closes the underlying comm.
        When the comm is closed, all of the widget views are automatically 
        removed from the frontend."""
        self.comm.close()
        del self.comm
    
    
    # Properties
    def _get_parent(self):
        return self._parent
    parent = property(_get_parent)
    
    
    def _get_children(self):
        return copy(self._children)
    children = property(_get_children)
    
    
    def _get_keys(self):
        keys = ['_css']
        keys.extend(self._keys)
        return keys
    keys = property(_get_keys)
    
    
    # Event handlers
    def _handle_msg(self, msg):
        """Called when a msg is recieved from the frontend"""
        # Handle backbone sync methods CREATE, PATCH, and UPDATE
        sync_method = msg['content']['data']['sync_method']
        sync_data = msg['content']['data']['sync_data']
        self._handle_recieve_state(sync_data) # handles all methods
    
    
    def _handle_recieve_state(self, sync_data):
        """Called when a state is recieved from the frontend."""
        self._property_lock = True
        try:
            
            # Use _keys instead of keys - Don't get retrieve the css from the client side.
            for name in self._keys:
                if name in sync_data:
                    setattr(self, name, sync_data[name])
        finally:
            self._property_lock = False
    
    
    def _handle_property_changed(self, name, old, new):
        """Called when a proeprty has been changed."""
        if not self._property_lock and self.comm is not None:
            # TODO: Validate properties.
            # Send new state to frontend
            self.send_state(key=name)


    def _handle_close(self):
        """Called when the comm is closed by the frontend."""
        self.comm = None
    
    
    # Public methods
    def send_state(self, key=None):
        """Sends the widget state, or a piece of it, to the frontend.

        Parameters
        ----------
        key : unicode (optional)
            A single property's name to sync with the frontend.
        """
        state = {}

        # If a key is provided, just send the state of that key.
        keys = []
        if key is None:
            keys.extend(self.keys)
        else:
            keys.append(key)
        for key in self.keys:
            try:
                state[key] = getattr(self, key)
            except Exception as e:
                pass # Eat errors, nom nom nom
        self.comm.send({"method": "update",
                        "state": state})


    def get_css(self, key, selector=""):
        """Get a CSS property of the widget views (shared among all of the 
        views)

        Parameters
        ----------
        key: unicode
            CSS key
        selector: unicode (optional)
            JQuery selector used when the CSS key/value was set.
        """
        if selector in self._css and key in self._css[selector]:
            return self._css[selector][key]
        else:
            return None


    def set_css(self, key, value, selector=""):
        """Set a CSS property of the widget views (shared among all of the 
        views)

        Parameters
        ----------
        key: unicode
            CSS key
        value
            CSS value
        selector: unicode (optional)
            JQuery selector to use to apply the CSS key/value.
        """
        if selector not in self._css:
            self._css[selector] = {}
            
        # Only update the property if it has changed.
        if not (key in self._css[selector] and value in self._css[selector][key]):
            self._css[selector][key] = value
            self.send_state() # Send new state to client.


    # Support methods
    def _repr_widget_(self, view_name=None):
        """Function that is called when `IPython.display.display` is called on
        the widget.

        Parameters
        ----------
        view_name: unicode (optional)
            View to display in the frontend.  Overrides default_view_name."""
        if not view_name:
            view_name = self.default_view_name
        
        # Create a comm.
        if self.comm is None:
            self.comm = Comm(target_name=self.target_name)
            self.comm.on_msg(self._handle_msg)
            self.comm.on_close(self._handle_close)
        
        # Make sure model is syncronized
        self.send_state()
            
        # Show view.
        if self.parent is None:
            self.comm.send({"method": "display", "view_name": view_name})
        else:
            self.comm.send({"method": "display", 
                            "view_name": view_name,
                            "parent": self.parent.comm.comm_id})
        
        # Now display children if any.
        for child in self.children:
            child._repr_widget_()
        return None

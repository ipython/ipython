
from copy import copy
from glob import glob
import uuid
import sys
import os

import IPython
from IPython.kernel.comm import Comm
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import Unicode, Dict
from IPython.display import Javascript, display
from IPython.utils.py3compat import string_types
from IPython.utils.javascript import display_all_js

def init_widget_js():    
    path = os.path.split(os.path.abspath( __file__ ))[0]
    display_all_js(path)
    for root, dirs, files in os.walk(path):
        for sub_directory in dirs:
            display_all_js(os.path.join(path, sub_directory))


class Widget(LoggingConfigurable):

    ### Public declarations
    target_name = Unicode('widget')
    default_view_name = Unicode()
    
    
    ### Private/protected declarations
    _keys = []
    _property_lock = False
    _parent = None
    _children = []
    _css = Dict()
    
    
    ### Public constructor
    def __init__(self, parent=None, **kwargs):
        super(Widget, self).__init__(**kwargs)
        
        self._children = []
        if parent is not None:
            parent._children.append(self)
        self._parent = parent
        self.comm = None
        
        # Register after init to allow default values to be specified
        self.on_trait_change(self._handle_property_changed, self.keys)
        
        
    def __del__(self):
        self.close()
    
    def close(self):
        self.comm.close()
        del self.comm
    
    
    ### Properties
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
    
    def _get_css(self, key, selector=""):
        if selector in self._css and key in self._css[selector]:
            return self._css[selector][key]
        else:
            return None
    def _set_css(self, value, key, selector=""):
        if selector not in self._css:
            self._css[selector] = {}
            
        # Only update the property if it has changed.
        if not (key in self._css[selector] and value in self._css[selector][key]):
            self._css[selector][key] = value
            self.send_state() # Send new state to client.
            
    css = property(_get_css, _set_css)
    
    
    ### Event handlers
    def _handle_msg(self, msg):
        
        # Handle backbone sync methods
        sync_method = msg['content']['data']['sync_method']
        sync_data = msg['content']['data']['sync_data']
        if sync_method.lower() in ['create', 'update']:
            self._handle_recieve_state(sync_data)
    
    
    def _handle_recieve_state(self, sync_data):
        self._property_lock = True
        try:
            
            # Use _keys instead of keys - Don't get retrieve the css from the client side.
            for name in self._keys:
                if name in sync_data:
                    setattr(self, name, sync_data[name])
        finally:
            self._property_lock = False
    
    
    def _handle_property_changed(self, name, old, new):
        if not self._property_lock:
            # TODO: Validate properties.
            # Send new state to frontend
            self.send_state()


    def _handle_close(self):
        self.comm = None
    
    
    ### Public methods
    def _repr_widget_(self, view_name=None):
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
            self.comm.send({"method": "show", "view_name": view_name})
        else:
            self.comm.send({"method": "show", 
                            "view_name": view_name,
                            "parent": self.parent.comm.comm_id})
        
        # Now show children if any.
        for child in self.children:
            child._repr_widget_()
        return None


    def send_state(self):
        state = {}
        for key in self.keys:
            try:
                state[key] = getattr(self, key)
            except Exception as e:
                pass # Eat errors, nom nom nom
        self.comm.send({"method": "update",
                        "state": state})
    
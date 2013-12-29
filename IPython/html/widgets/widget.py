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
import inspect
import types

import IPython
from IPython.kernel.comm import Comm
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import Unicode, Dict, List, Instance, Bool
from IPython.display import Javascript, display
from IPython.utils.py3compat import string_types

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class BaseWidget(LoggingConfigurable):

    # Shared declarations (Class level)
    _keys = List(Unicode, help="List of keys comprising the state of the model.")
    _children_attr = List(Unicode, help="List of keys of children objects of the model.")
    _children_lists_attr = List(Unicode, help="List of keys containing lists of children objects of the model.")
    widget_construction_callback = None

    def on_widget_constructed(callback):
        """Class method, registers a callback to be called when a widget is
        constructed.  The callback must have the following signature:
        callback(widget)"""
        Widget.widget_construction_callback = callback

    def _handle_widget_constructed(widget):
        """Class method, called when a widget is constructed."""
        if Widget.widget_construction_callback is not None and callable(Widget.widget_construction_callback):
            Widget.widget_construction_callback(widget)

    

    # Public declarations (Instance level)
    target_name = Unicode('widget', help="""Name of the backbone model 
        registered in the frontend to create and sync this widget with.""")
    default_view_name = Unicode(help="""Default view registered in the frontend
        to use to represent the widget.""")

    # Private/protected declarations
    _property_lock = (None, None) # Last updated (key, value) from the front-end.  Prevents echo.
    _displayed = False
    _comm = None
    
    def __init__(self, **kwargs):
        """Public constructor
        """
        self._display_callbacks = []
        self._msg_callbacks = []
        super(BaseWidget, self).__init__(**kwargs)

        # Register after init to allow default values to be specified
        # TODO: register three different handlers, one for each list, and abstract out the common parts
        self.on_trait_change(self._handle_property_changed, self.keys+self._children_attr+self._children_lists_attr)
        Widget._handle_widget_constructed(self)

    def __del__(self):
        """Object disposal"""
        self.close()


    def close(self):
        """Close method.  Closes the widget which closes the underlying comm.
        When the comm is closed, all of the widget views are automatically
        removed from the frontend."""
        self._close_communication()
    
    
    # Properties
    @property
    def keys(self):
        keys = ['_children_attr', '_children_lists_attr']
        keys.extend(self._keys)
        return keys
    
    @property
    def comm(self):
        if self._comm is None:
            self._open_communication()
        return self._comm

    # Event handlers
    def _handle_msg(self, msg):
        """Called when a msg is recieved from the frontend"""
        data = msg['content']['data']
        method = data['method']

        # Handle backbone sync methods CREATE, PATCH, and UPDATE
        if method == 'backbone':
            if 'sync_method' in data and 'sync_data' in data:
                sync_method = data['sync_method']
                sync_data = data['sync_data']
                self._handle_recieve_state(sync_data) # handles all methods

        # Handle a custom msg from the front-end
        elif method == 'custom':
            if 'custom_content' in data:
                self._handle_custom_msg(data['custom_content'])


    def _handle_custom_msg(self, content):
        """Called when a custom msg is recieved."""
        for handler in self._msg_callbacks:
            if callable(handler):
                argspec = inspect.getargspec(handler)
                nargs = len(argspec[0])

                # Bound methods have an additional 'self' argument
                if isinstance(handler, types.MethodType):
                    nargs -= 1

                # Call the callback
                if nargs == 1:
                    handler(content)
                elif nargs == 2:
                    handler(self, content)
                else:
                    raise TypeError('Widget msg callback must ' \
                        'accept 1 or 2 arguments, not %d.' % nargs)


    def _handle_recieve_state(self, sync_data):
        """Called when a state is recieved from the frontend."""
        # Use _keys instead of keys - Don't get retrieve the css from the client side.
        for name in self._keys:
            if name in sync_data:
                try:
                    self._property_lock = (name, sync_data[name])
                    setattr(self, name, sync_data[name])
                finally:
                    self._property_lock = (None, None)


    def _handle_property_changed(self, name, old, new):
        """Called when a proeprty has been changed."""
        # Make sure this isn't information that the front-end just sent us.
        if self._property_lock[0] != name and self._property_lock[1] != new:
            # Send new state to frontend
            self.send_state(key=name)

    def _handle_displayed(self, **kwargs):
        """Called when a view has been displayed for this widget instance

        Parameters
        ----------
        [view_name]: unicode (optional kwarg)
            Name of the view that was displayed."""
        for handler in self._display_callbacks:
            if callable(handler):
                argspec = inspect.getargspec(handler)
                nargs = len(argspec[0])

                # Bound methods have an additional 'self' argument
                if isinstance(handler, types.MethodType):
                    nargs -= 1

                # Call the callback
                if nargs == 0:
                    handler()
                elif nargs == 1:
                    handler(self)
                elif nargs == 2:
                    handler(self, kwargs.get('view_name', None))
                else:
                    handler(self, **kwargs)

    # Public methods
    def send_state(self, key=None):
        """Sends the widget state, or a piece of it, to the frontend.

        Parameters
        ----------
        key : unicode (optional)
            A single property's name to sync with the frontend.
        """
        self._send({"method": "update",
                    "state": self.get_state()})

    def get_state(self, key=None)
        """Gets the widget state, or a piece of it.

        Parameters
        ----------
        key : unicode (optional)
            A single property's name to get.
        """
        state = {}

        # If a key is provided, just send the state of that key.
        if key is None:
            keys = self.keys[:]
            children_attr = self._children_attr[:]
            children_lists_attr = self._children_lists_attr[:]
        else:
            keys = []
            children_attr = []
            children_lists_attr = []
            if key in self._children_attr:
                children_attr.append(key)
            elif key in self._children_lists_attr:
                children_lists_attr.append(key)
            else:
                keys.append(key)
        for k in keys:
            state[k] = getattr(self, k)
        for k in children_attr:
            # automatically create models on the browser side if they aren't already created
            state[k] = getattr(self, k).comm.comm_id
        for k in children_lists_attr:
            # automatically create models on the browser side if they aren't already created
            state[k] = [i.comm.comm_id for i in getattr(self, k)]
        return state


    def send(self, content):
        """Sends a custom msg to the widget model in the front-end.

        Parameters
        ----------
        content : dict
            Content of the message to send.
        """
        self._send({"method": "custom",
                        "custom_content": content})


    def on_msg(self, callback, remove=False):
        """Register a callback for when a custom msg is recieved from the front-end

        Parameters
        ----------
        callback: method handler
            Can have a signature of:
            - callback(content)
            - callback(sender, content)
        remove: bool
            True if the callback should be unregistered."""
        if remove and callback in self._msg_callbacks:
            self._msg_callbacks.remove(callback)
        elif not remove and not callback in self._msg_callbacks:
            self._msg_callbacks.append(callback)


    def on_displayed(self, callback, remove=False):
        """Register a callback to be called when the widget has been displayed

        Parameters
        ----------
        callback: method handler
            Can have a signature of:
            - callback()
            - callback(sender)
            - callback(sender, view_name)
            - callback(sender, **kwargs)
              kwargs from display call passed through without modification.
        remove: bool
            True if the callback should be unregistered."""
        if remove and callback in self._display_callbacks:
            self._display_callbacks.remove(callback)
        elif not remove and not callback in self._display_callbacks:
            self._display_callbacks.append(callback)


    # Support methods
    def _repr_widget_(self, **kwargs):
        """Function that is called when `IPython.display.display` is called on
        the widget.

        Parameters
        ----------
        view_name: unicode (optional)
            View to display in the frontend.  Overrides default_view_name."""
        view_name = kwargs.get('view_name', self.default_view_name)
        
        # Create a communication.
        self._open_communication()
        
        # Make sure model is syncronized
        self.send_state()
            
        # Show view.
        self._send({"method": "display", "view_name": view_name})
        self._displayed = True
        self._handle_displayed(**kwargs)


    def _open_communication(self):
        """Opens a communication with the front-end."""
        # Create a comm.
        if not hasattr(self, '_comm') or self._comm is None:
            self._comm = Comm(target_name=self.target_name)
            self._comm.on_msg(self._handle_msg)
            self._comm.on_close(self._close_communication)


    def _close_communication(self):
        """Closes a communication with the front-end."""
        if hasattr(self, '_comm') and self._comm is not None:
            try:
                self._comm.close()
            finally:
                self._comm = None


    def _send(self, msg):
        """Sends a message to the model in the front-end"""
        if self._comm is not None:
            self._comm.send(msg)
            return True
        else:
            return False        

class Widget(BaseWidget):

    _children = List(Instance('IPython.html.widgets.widget.Widget'))
    _children_lists_attr = List(Unicode, ['_children'])
    visible = Bool(True, help="Whether or not the widget is visible.")

    # Private/protected declarations
    _css = Dict() # Internal CSS property dict

    # Properties
    @property
    def keys(self):
        keys = ['visible', '_css']
        keys.extend(super(Widget, self).keys)
        return keys

    def get_css(self, key, selector=""):
        """Get a CSS property of the widget.  Note, this function does not
        actually request the CSS from the front-end;  Only properties that have
        been set with set_css can be read.

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


    def set_css(self, *args, **kwargs):
        """Set one or more CSS properties of the widget (shared among all of the
        views).  This function has two signatures:
        - set_css(css_dict, [selector=''])
        - set_css(key, value, [selector=''])

        Parameters
        ----------
        css_dict : dict
            CSS key/value pairs to apply
        key: unicode
            CSS key
        value
            CSS value
        selector: unicode (optional)
            JQuery selector to use to apply the CSS key/value.
        """
        selector = kwargs.get('selector', '')

        # Signature 1: set_css(css_dict, [selector=''])
        if len(args) == 1:
            if isinstance(args[0], dict):
                for (key, value) in args[0].items():
                    self.set_css(key, value, selector=selector)
            else:
                raise Exception('css_dict must be a dict.')

        # Signature 2: set_css(key, value, [selector=''])
        elif len(args) == 2 or len(args) == 3:

            # Selector can be a positional arg if it's the 3rd value
            if len(args) == 3:
                selector = args[2]
            if selector not in self._css:
                self._css[selector] = {}

            # Only update the property if it has changed.
            key = args[0]
            value = args[1]
            if not (key in self._css[selector] and value in self._css[selector][key]):
                self._css[selector][key] = value
                self.send_state('_css') # Send new state to client.
        else:
            raise Exception('set_css only accepts 1-3 arguments')


    def add_class(self, class_name, selector=""):
        """Add class[es] to a DOM element

        Parameters
        ----------
        class_name: unicode
            Class name(s) to add to the DOM element(s).  Multiple class names
            must be space separated.
        selector: unicode (optional)
            JQuery selector to select the DOM element(s) that the class(es) will
            be added to.
        """
        self._send({"method": "add_class",
                        "class_list": class_name,
                        "selector": selector})


    def remove_class(self, class_name, selector=""):
        """Remove class[es] from a DOM element

        Parameters
        ----------
        class_name: unicode
            Class name(s) to remove from  the DOM element(s).  Multiple class
            names must be space separated.
        selector: unicode (optional)
            JQuery selector to select the DOM element(s) that the class(es) will
            be removed from.
        """
        self._send({"method": "remove_class",
                        "class_list": class_name,
                        "selector": selector})

"""Base Widget class.  Allows user to create widgets in the back-end that render
in the IPython notebook front-end.
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
from contextlib import contextmanager

from IPython.core.getipython import get_ipython
from IPython.kernel.comm import Comm
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import Unicode, Dict, Instance, Bool, List, Tuple, Int
from IPython.utils.py3compat import string_types

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class CallbackDispatcher(LoggingConfigurable):
    """A structure for registering and running callbacks"""
    callbacks = List()
    
    def __call__(self, *args, **kwargs):
        """Call all of the registered callbacks."""
        value = None
        for callback in self.callbacks:
            try:
                local_value = callback(*args, **kwargs)
            except Exception as e:
                ip = get_ipython()
                if ip is None:
                    self.log.warn("Exception in callback %s: %s", callback, e, exc_info=True)
                else:
                    ip.showtraceback()
            else:
                value = local_value if local_value is not None else value
        return value

    def register_callback(self, callback, remove=False):
        """(Un)Register a callback

        Parameters
        ----------
        callback: method handle
            Method to be registered or unregistered.
        remove=False: bool
            Whether to unregister the callback."""
        
        # (Un)Register the callback.
        if remove and callback in self.callbacks:
            self.callbacks.remove(callback)
        elif not remove and callback not in self.callbacks:
            self.callbacks.append(callback)

def _show_traceback(method):
    """decorator for showing tracebacks in IPython"""
    def m(self, *args, **kwargs):
        try:
            return(method(self, *args, **kwargs))
        except Exception as e:
            ip = get_ipython()
            if ip is None:
                self.log.warn("Exception in widget method %s: %s", method, e, exc_info=True)
            else:
                ip.showtraceback()
    return m

class Widget(LoggingConfigurable):
    #-------------------------------------------------------------------------
    # Class attributes
    #-------------------------------------------------------------------------
    _widget_construction_callback = None
    widgets = {}

    @staticmethod
    def on_widget_constructed(callback):
        """Registers a callback to be called when a widget is constructed.

        The callback must have the following signature:
        callback(widget)"""
        Widget._widget_construction_callback = callback

    @staticmethod
    def _call_widget_constructed(widget):
        """Static method, called when a widget is constructed."""
        if Widget._widget_construction_callback is not None and callable(Widget._widget_construction_callback):
            Widget._widget_construction_callback(widget)

    #-------------------------------------------------------------------------
    # Traits
    #-------------------------------------------------------------------------
    _model_name = Unicode('WidgetModel', help="""Name of the backbone model 
        registered in the front-end to create and sync this widget with.""")
    _view_name = Unicode(help="""Default view registered in the front-end
        to use to represent the widget.""", sync=True)
    _comm = Instance('IPython.kernel.comm.Comm')
    
    msg_throttle = Int(3, sync=True, help="""Maximum number of msgs the 
        front-end can send before receiving an idle msg from the back-end.""")
    
    keys = List()
    def _keys_default(self):
        return [name for name in self.traits(sync=True)]
    
    _property_lock = Tuple((None, None))
    
    _display_callbacks = Instance(CallbackDispatcher, ())
    _msg_callbacks = Instance(CallbackDispatcher, ())
    
    #-------------------------------------------------------------------------
    # (Con/de)structor
    #-------------------------------------------------------------------------
    def __init__(self, **kwargs):
        """Public constructor"""
        super(Widget, self).__init__(**kwargs)

        self.on_trait_change(self._handle_property_changed, self.keys)
        Widget._call_widget_constructed(self)

    def __del__(self):
        """Object disposal"""
        self.close()

    #-------------------------------------------------------------------------
    # Properties
    #-------------------------------------------------------------------------

    @property
    def comm(self):
        """Gets the Comm associated with this widget.

        If a Comm doesn't exist yet, a Comm will be created automagically."""
        if self._comm is None:
            # Create a comm.
            self._comm = Comm(target_name=self._model_name)
            self._comm.on_msg(self._handle_msg)
            self._comm.on_close(self._close)
            Widget.widgets[self.model_id] = self

            # first update
            self.send_state()
        return self._comm
    
    @property
    def model_id(self):
        """Gets the model id of this widget.

        If a Comm doesn't exist yet, a Comm will be created automagically."""
        return self.comm.comm_id

    #-------------------------------------------------------------------------
    # Methods
    #-------------------------------------------------------------------------
    def _close(self):
        """Private close - cleanup objects, registry entries"""
        del Widget.widgets[self.model_id]
        self._comm = None

    def close(self):
        """Close method.

        Closes the widget which closes the underlying comm.
        When the comm is closed, all of the widget views are automatically
        removed from the front-end."""
        if self._comm is not None:
            self._comm.close()
            self._close()

    def send_state(self, key=None):
        """Sends the widget state, or a piece of it, to the front-end.

        Parameters
        ----------
        key : unicode (optional)
            A single property's name to sync with the front-end.
        """
        self._send({
            "method" : "update",
            "state"  : self.get_state()
        })

    def get_state(self, key=None):
        """Gets the widget state, or a piece of it.

        Parameters
        ----------
        key : unicode (optional)
            A single property's name to get.
        """
        keys = self.keys if key is None else [key]
        return {k: self._pack_widgets(getattr(self, k)) for k in keys} 

    def send(self, content):
        """Sends a custom msg to the widget model in the front-end.

        Parameters
        ----------
        content : dict
            Content of the message to send.
        """
        self._send({"method": "custom", "content": content})

    def on_msg(self, callback, remove=False):
        """(Un)Register a custom msg receive callback.

        Parameters
        ----------
        callback: callable
            callback will be passed two arguments when a message arrives::
            
                callback(widget, content)
            
        remove: bool
            True if the callback should be unregistered."""
        self._msg_callbacks.register_callback(callback, remove=remove)

    def on_displayed(self, callback, remove=False):
        """(Un)Register a widget displayed callback.

        Parameters
        ----------
        callback: method handler
            Must have a signature of::
            
                callback(widget, **kwargs)
            
            kwargs from display are passed through without modification.
        remove: bool
            True if the callback should be unregistered."""
        self._display_callbacks.register_callback(callback, remove=remove)

    #-------------------------------------------------------------------------
    # Support methods
    #-------------------------------------------------------------------------
    @contextmanager
    def _lock_property(self, key, value):
        """Lock a property-value pair.

        NOTE: This, in addition to the single lock for all state changes, is 
        flawed.  In the future we may want to look into buffering state changes 
        back to the front-end."""
        self._property_lock = (key, value)
        try:
            yield
        finally:
            self._property_lock = (None, None)

    def _should_send_property(self, key, value):
        """Check the property lock (property_lock)"""
        return key != self._property_lock[0] or \
        value != self._property_lock[1]
    
    # Event handlers
    @_show_traceback
    def _handle_msg(self, msg):
        """Called when a msg is received from the front-end"""
        data = msg['content']['data']
        method = data['method']
        if not method in ['backbone', 'custom']:
            self.log.error('Unknown front-end to back-end widget msg with method "%s"' % method)

        # Handle backbone sync methods CREATE, PATCH, and UPDATE all in one.
        if method == 'backbone' and 'sync_data' in data:
            sync_data = data['sync_data']
            self._handle_receive_state(sync_data) # handles all methods

        # Handle a custom msg from the front-end
        elif method == 'custom':
            if 'content' in data:
                self._handle_custom_msg(data['content'])

    def _handle_receive_state(self, sync_data):
        """Called when a state is received from the front-end."""
        for name in self.keys:
            if name in sync_data:
                value = self._unpack_widgets(sync_data[name])
                with self._lock_property(name, value):
                    setattr(self, name, value)

    def _handle_custom_msg(self, content):
        """Called when a custom msg is received."""
        self._msg_callbacks(self, content)

    def _handle_property_changed(self, name, old, new):
        """Called when a property has been changed."""
        # Make sure this isn't information that the front-end just sent us.
        if self._should_send_property(name, new):
            # Send new state to front-end
            self.send_state(key=name)

    def _handle_displayed(self, **kwargs):
        """Called when a view has been displayed for this widget instance"""
        self._display_callbacks(self, **kwargs)

    def _pack_widgets(self, x):
        """Recursively converts all widget instances to model id strings.

        Children widgets will be stored and transmitted to the front-end by 
        their model ids.  Return value must be JSON-able."""
        if isinstance(x, dict):
            return {k: self._pack_widgets(v) for k, v in x.items()}
        elif isinstance(x, (list, tuple)):
            return [self._pack_widgets(v) for v in x]
        elif isinstance(x, Widget):
            return x.model_id
        else:
            return x # Value must be JSON-able

    def _unpack_widgets(self, x):
        """Recursively converts all model id strings to widget instances.

        Children widgets will be stored and transmitted to the front-end by 
        their model ids."""
        if isinstance(x, dict):
            return {k: self._unpack_widgets(v) for k, v in x.items()}
        elif isinstance(x, (list, tuple)):
            return [self._unpack_widgets(v) for v in x]
        elif isinstance(x, string_types):
            return x if x not in Widget.widgets else Widget.widgets[x]
        else:
            return x

    def _ipython_display_(self, **kwargs):
        """Called when `IPython.display.display` is called on the widget."""
        # Show view.  By sending a display message, the comm is opened and the
        # initial state is sent.
        self._send({"method": "display"})
        self._handle_displayed(**kwargs)

    def _send(self, msg):
        """Sends a message to the model in the front-end."""
        self.comm.send(msg)


class DOMWidget(Widget):
    visible = Bool(True, help="Whether the widget is visible.", sync=True)
    _css = Dict(sync=True) # Internal CSS property dict

    def get_css(self, key, selector=""):
        """Get a CSS property of the widget.

        Note: This function does not actually request the CSS from the 
        front-end;  Only properties that have been set with set_css can be read.

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

    def set_css(self, dict_or_key, value=None, selector=''):
        """Set one or more CSS properties of the widget.

        This function has two signatures:
        - set_css(css_dict, selector='')
        - set_css(key, value, selector='')

        Parameters
        ----------
        css_dict : dict
            CSS key/value pairs to apply
        key: unicode
            CSS key
        value:
            CSS value
        selector: unicode (optional, kwarg only)
            JQuery selector to use to apply the CSS key/value.  If no selector 
            is provided, an empty selector is used.  An empty selector makes the 
            front-end try to apply the css to a default element.  The default
            element is an attribute unique to each view, which is a DOM element
            of the view that should be styled with common CSS (see 
            `$el_to_style` in the Javascript code).
        """
        if not selector in self._css:
            self._css[selector] = {}
        my_css = self._css[selector]
        
        if value is None:
            css_dict = dict_or_key
        else:
            css_dict = {dict_or_key: value}
        
        for (key, value) in css_dict.items():
            if not (key in my_css and value == my_css[key]):
                my_css[key] = value
        self.send_state('_css')

    def add_class(self, class_names, selector=""):
        """Add class[es] to a DOM element.

        Parameters
        ----------
        class_names: unicode or list
            Class name(s) to add to the DOM element(s).
        selector: unicode (optional)
            JQuery selector to select the DOM element(s) that the class(es) will
            be added to.
        """
        class_list = class_names
        if isinstance(class_list, (list, tuple)):
            class_list = ' '.join(class_list)

        self.send({
            "msg_type"   : "add_class",
            "class_list" : class_list,
            "selector"   : selector
        })

    def remove_class(self, class_names, selector=""):
        """Remove class[es] from a DOM element.

        Parameters
        ----------
        class_names: unicode or list
            Class name(s) to remove from  the DOM element(s).
        selector: unicode (optional)
            JQuery selector to select the DOM element(s) that the class(es) will
            be removed from.
        """
        class_list = class_names
        if isinstance(class_list, (list, tuple)):
            class_list = ' '.join(class_list)

        self.send({
            "msg_type"   : "remove_class",
            "class_list" : class_list,
            "selector"   : selector,
        })

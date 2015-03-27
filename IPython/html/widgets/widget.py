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
import collections

from IPython.core.getipython import get_ipython
from IPython.kernel.comm import Comm
from IPython.config import LoggingConfigurable
from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Unicode, Dict, Instance, Bool, List, \
    CaselessStrEnum, Tuple, CUnicode, Int, Set
from IPython.utils.py3compat import string_types
from .trait_types import Color

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


def register(key=None):
    """Returns a decorator registering a widget class in the widget registry. 
    If no key is provided, the class name is used as a key. A key is
    provided for each core IPython widget so that the frontend can use
    this key regardless of the language of the kernel"""
    def wrap(widget):
        l = key if key is not None else widget.__module__ + widget.__name__
        Widget.widget_types[l] = widget
        return widget
    return wrap


def _widget_to_json(x):
    if isinstance(x, dict):
        return {k: _widget_to_json(v) for k, v in x.items()}
    elif isinstance(x, (list, tuple)):
        return [_widget_to_json(v) for v in x]
    elif isinstance(x, Widget):
        return "IPY_MODEL_" + x.model_id
    else:
        return x

def _json_to_widget(x):
    if isinstance(x, dict):
        return {k: _json_to_widget(v) for k, v in x.items()}
    elif isinstance(x, (list, tuple)):
        return [_json_to_widget(v) for v in x]
    elif isinstance(x, string_types) and x.startswith('IPY_MODEL_') and x[10:] in Widget.widgets:
        return Widget.widgets[x[10:]]
    else:
        return x

widget_serialization = {
    'from_json': _json_to_widget,
    'to_json': lambda x: (_widget_to_json(x), {'serialization': ('widget_serialization', 'widgets/js/types')})
}

def _to_binary_list(x):
    import numpy
    return memoryview(numpy.array(x, dtype=float)), {'serialization': ('list_of_numbers', 'widgets/js/types')}

def _from_binary_list(x):
    import numpy
    a = numpy.frombuffer(x.tobytes(), dtype=float)
    return list(a)

list_of_numbers = {
    'from_json': _from_binary_list,
    'to_json': _to_binary_list
}



class Widget(LoggingConfigurable):
    #-------------------------------------------------------------------------
    # Class attributes
    #-------------------------------------------------------------------------
    _widget_construction_callback = None
    widgets = {}
    widget_types = {}

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

    @staticmethod
    def handle_comm_opened(comm, msg):
        """Static method, called when a widget is constructed."""
        widget_class = import_item(msg['content']['data']['widget_class'])
        widget = widget_class(comm=comm)


    #-------------------------------------------------------------------------
    # Traits
    #-------------------------------------------------------------------------
    _model_module = Unicode(None, allow_none=True, help="""A requirejs module name
        in which to find _model_name. If empty, look in the global registry.""")
    _model_name = Unicode('WidgetModel', help="""Name of the backbone model 
        registered in the front-end to create and sync this widget with.""")
    _view_module = Unicode(help="""A requirejs module in which to find _view_name.
        If empty, look in the global registry.""", sync=True)
    _view_name = Unicode(None, allow_none=True, help="""Default view registered in the front-end
        to use to represent the widget.""", sync=True)
    comm = Instance('IPython.kernel.comm.Comm')
    
    msg_throttle = Int(3, sync=True, help="""Maximum number of msgs the 
        front-end can send before receiving an idle msg from the back-end.""")
    
    version = Int(0, sync=True, help="""Widget's version""")
    keys = List()
    def _keys_default(self):
        return [name for name in self.traits(sync=True)]
    
    _property_lock = Tuple((None, None))
    _send_state_lock = Int(0)
    _states_to_send = Set()
    _display_callbacks = Instance(CallbackDispatcher, ())
    _msg_callbacks = Instance(CallbackDispatcher, ())
    
    #-------------------------------------------------------------------------
    # (Con/de)structor
    #-------------------------------------------------------------------------
    def __init__(self, **kwargs):
        """Public constructor"""
        self._model_id = kwargs.pop('model_id', None)
        super(Widget, self).__init__(**kwargs)

        Widget._call_widget_constructed(self)
        self.open()

    def __del__(self):
        """Object disposal"""
        self.close()

    #-------------------------------------------------------------------------
    # Properties
    #-------------------------------------------------------------------------

    def open(self):
        """Open a comm to the frontend if one isn't already open."""
        if self.comm is None:
            args = dict(target_name='ipython.widget',
                        data={'model_name': self._model_name,
                              'model_module': self._model_module})
            if self._model_id is not None:
                args['comm_id'] = self._model_id
            self.comm = Comm(**args)

    def _comm_changed(self, name, new):
        """Called when the comm is changed."""
        if new is None:
            return
        self._model_id = self.model_id
        
        self.comm.on_msg(self._handle_msg)
        Widget.widgets[self.model_id] = self
        
        # first update
        self.send_state()

    @property
    def model_id(self):
        """Gets the model id of this widget.

        If a Comm doesn't exist yet, a Comm will be created automagically."""
        return self.comm.comm_id

    #-------------------------------------------------------------------------
    # Methods
    #-------------------------------------------------------------------------

    def close(self):
        """Close method.

        Closes the underlying comm.
        When the comm is closed, all of the widget views are automatically
        removed from the front-end."""
        if self.comm is not None:
            Widget.widgets.pop(self.model_id, None)
            self.comm.close()
            self.comm = None
    
    def send_state(self, key=None):
        """Sends the widget state, or a piece of it, to the front-end.

        Parameters
        ----------
        key : unicode, or iterable (optional)
            A single property's name or iterable of property names to sync with the front-end.
        """
        state, buffer_keys, buffers, metadata = self.get_state(key=key)
        msg = {"method": "update", "state": state}
        if buffer_keys:
            msg['buffers'] = buffer_keys
        if metadata:
            msg['metadata'] = metadata
        self._send(msg, buffers=buffers)

    def get_state(self, key=None):
        """Gets the widget state, or a piece of it.

        Parameters
        ----------
        key : unicode or iterable (optional)
            A single property's name or iterable of property names to get.

        Returns
        -------
        state : dict of states
        buffer_keys : list of strings
            the values that are stored in buffers
        buffers : list of binary memoryviews
            values to transmit in binary
        metadata : dict
            metadata for each field: {key: metadata}
        """
        if key is None:
            keys = self.keys
        elif isinstance(key, string_types):
            keys = [key]
        elif isinstance(key, collections.Iterable):
            keys = key
        else:
            raise ValueError("key must be a string, an iterable of keys, or None")
        state = {}
        buffers = []
        buffer_keys = []
        metadata = {}
        for k in keys:
            f = self.trait_metadata(k, 'to_json', self._trait_to_json)
            value = getattr(self, k)
            serialized, md = f(value)
            if isinstance(serialized, memoryview):
                buffers.append(serialized)
                buffer_keys.append(k)
            else:
                state[k] = serialized
            if md is not None:
                metadata[k] = md
        return state, buffer_keys, buffers, metadata

    def set_state(self, sync_data):
        """Called when a state is received from the front-end."""
        for name in self.keys:
            if name in sync_data:
                json_value = sync_data[name]
                from_json = self.trait_metadata(name, 'from_json', self._trait_from_json)
                with self._lock_property(name, json_value):
                    setattr(self, name, from_json(json_value))
    
    def send(self, content, buffers=None):
        """Sends a custom msg to the widget model in the front-end.

        Parameters
        ----------
        content : dict
            Content of the message to send.
        buffers : list of binary buffers
            Binary buffers to send with message
        """
        self._send({"method": "custom", "content": content}, buffers=buffers)

    def on_msg(self, callback, remove=False):
        """(Un)Register a custom msg receive callback.

        Parameters
        ----------
        callback: callable
            callback will be passed three arguments when a message arrives::
            
                callback(widget, content, buffers)
            
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

        The value should be the JSON state of the property.

        NOTE: This, in addition to the single lock for all state changes, is 
        flawed.  In the future we may want to look into buffering state changes 
        back to the front-end."""
        self._property_lock = (key, value)
        try:
            yield
        finally:
            self._property_lock = (None, None)

    @contextmanager
    def hold_sync(self):
        """Hold syncing any state until the context manager is released"""
        # We increment a value so that this can be nested.  Syncing will happen when
        # all levels have been released.
        self._send_state_lock += 1
        try:
            yield
        finally:
            self._send_state_lock -=1
            if self._send_state_lock == 0:
                self.send_state(self._states_to_send)
                self._states_to_send.clear()

    def _should_send_property(self, key, value):
        """Check the property lock (property_lock)"""
        to_json = self.trait_metadata(key, 'to_json', self._trait_to_json)
        if (key == self._property_lock[0]
            and to_json(value) == self._property_lock[1]):
            return False
        elif self._send_state_lock > 0:
            self._states_to_send.add(key)
            return False
        else:
            return True
    
    # Event handlers
    @_show_traceback
    def _handle_msg(self, msg):
        """Called when a msg is received from the front-end"""
        data = msg['content']['data']
        method = data['method']

        # Handle backbone sync methods CREATE, PATCH, and UPDATE all in one.
        if method == 'backbone':
            if 'sync_data' in data:
                # get binary buffers too
                sync_data = data['sync_data']
                for i,k in enumerate(data.get('buffer_keys', [])):
                    sync_data[k] = msg['buffers'][i]
                self.set_state(sync_data) # handles all methods

        # Handle a state request.
        elif method == 'request_state':
            self.send_state()

        # Handle a custom msg from the front-end.
        elif method == 'custom':
            if 'content' in data:
                self._handle_custom_msg(data['content'], msg['buffers'])

        # Catch remainder.
        else:
            self.log.error('Unknown front-end to back-end widget msg with method "%s"' % method)

    def _handle_custom_msg(self, content, buffers):
        """Called when a custom msg is received."""
        self._msg_callbacks(self, content, buffers)

    def _notify_trait(self, name, old_value, new_value):
        """Called when a property has been changed."""
        # Trigger default traitlet callback machinery.  This allows any user
        # registered validation to be processed prior to allowing the widget
        # machinery to handle the state.
        LoggingConfigurable._notify_trait(self, name, old_value, new_value)

        # Send the state after the user registered callbacks for trait changes
        # have all fired (allows for user to validate values).
        if self.comm is not None and name in self.keys:
            # Make sure this isn't information that the front-end just sent us.
            if self._should_send_property(name, new_value):
                # Send new state to front-end
                self.send_state(key=name)

    def _handle_displayed(self, **kwargs):
        """Called when a view has been displayed for this widget instance"""
        self._display_callbacks(self, **kwargs)

    def _trait_to_json(self, x):
        """Convert a trait value to json.

        Metadata (the second return value) is not sent
        """
        return x, None

    def _trait_from_json(self, x):
        """Convert json values to objects."""
        return x

    def _ipython_display_(self, **kwargs):
        """Called when `IPython.display.display` is called on the widget."""
        # Show view.
        if self._view_name is not None:
            self._send({"method": "display"})
            self._handle_displayed(**kwargs)

    def _send(self, msg, buffers=None):
        """Sends a message to the model in the front-end."""
        self.comm.send(data=msg, buffers=buffers)


class DOMWidget(Widget):
    visible = Bool(True, allow_none=True, help="Whether the widget is visible.  False collapses the empty space, while None preserves the empty space.", sync=True)
    _css = Tuple(sync=True, help="CSS property list: (selector, key, value)")
    _dom_classes = Tuple(sync=True, help="DOM classes applied to widget.$el.")
    
    width = CUnicode(sync=True)
    height = CUnicode(sync=True)
    # A default padding of 2.5 px makes the widgets look nice when displayed inline.
    padding = CUnicode(sync=True)
    margin = CUnicode(sync=True)

    color = Color(None, allow_none=True, sync=True)
    background_color = Color(None, allow_none=True, sync=True)
    border_color = Color(None, allow_none=True, sync=True)

    border_width = CUnicode(sync=True)
    border_radius = CUnicode(sync=True)
    border_style = CaselessStrEnum(values=[ # http://www.w3schools.com/cssref/pr_border-style.asp
        'none', 
        'hidden', 
        'dotted', 
        'dashed', 
        'solid', 
        'double', 
        'groove', 
        'ridge', 
        'inset', 
        'outset', 
        'initial', 
        'inherit', ''],
        default_value='', sync=True)

    font_style = CaselessStrEnum(values=[ # http://www.w3schools.com/cssref/pr_font_font-style.asp
        'normal', 
        'italic', 
        'oblique', 
        'initial', 
        'inherit', ''], 
        default_value='', sync=True)
    font_weight = CaselessStrEnum(values=[ # http://www.w3schools.com/cssref/pr_font_weight.asp
        'normal', 
        'bold', 
        'bolder', 
        'lighter',
        'initial', 
        'inherit', ''] + list(map(str, range(100,1000,100))),
        default_value='', sync=True)
    font_size = CUnicode(sync=True)
    font_family = Unicode(sync=True)

    def __init__(self, *pargs, **kwargs):
        super(DOMWidget, self).__init__(*pargs, **kwargs)

        def _validate_border(name, old, new):
            if new is not None and new != '':
                if name != 'border_width' and not self.border_width:
                    self.border_width = 1
                if name != 'border_style' and self.border_style == '':
                    self.border_style = 'solid'
        self.on_trait_change(_validate_border, ['border_width', 'border_style', 'border_color'])

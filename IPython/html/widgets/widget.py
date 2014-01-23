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
import inspect
import types

from IPython.kernel.comm import Comm
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import Unicode, Dict, Instance, Bool, List
from IPython.utils.py3compat import string_types

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class CallbackDispatcher(LoggingConfigurable):
    acceptable_nargs = List([], help="""List of integers.
        The number of arguments in the callbacks registered must match one of
        the integers in this list.  If this list is empty or None, it will be
        ignored.""")

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        LoggingConfigurable.__init__(self, *pargs, **kwargs)
        self.callbacks = {}

    def __call__(self, *pargs, **kwargs):
        """Call all of the registered callbacks that have the same number of
        positional arguments."""
        nargs = len(pargs)
        self._validate_nargs(nargs)
        value = None
        if nargs in self.callbacks:
            for callback in self.callbacks[nargs]:
                local_value = callback(*pargs, **kwargs)
                value = local_value if local_value is not None else value
        return value

    def register_callback(self, callback, remove=False):
        """(Un)Register a callback

        Parameters
        ----------
        callback: method handle
            Method to be registered or unregisted.
        remove=False: bool
            Whether or not to unregister the callback."""

        # Validate the number of arguments that the callback accepts.
        nargs = self._get_nargs(callback)
        self._validate_nargs(nargs)

        # Get/create the appropriate list of callbacks.
        if nargs not in self.callbacks:
            self.callbacks[nargs] = []
        callback_list = self.callbacks[nargs]

        # (Un)Register the callback.
        if remove and callback in callback_list:
            callback_list.remove(callback)
        elif not remove and callback not in callback_list:
            callback_list.append(callback)

    def _validate_nargs(self, nargs):
        if self.acceptable_nargs is not None and \
            len(self.acceptable_nargs) > 0 and \
            nargs not in self.acceptable_nargs:

            raise TypeError('Invalid number of positional arguments.  See acceptable_nargs list.')

    def _get_nargs(self, callback):
        """Gets the number of arguments in a callback"""
        if callable(callback):
            argspec = inspect.getargspec(callback)
            if argspec[0] is None:
                nargs = 0
            elif argspec[3] is None:
                nargs = len(argspec[0]) # Only count vargs!
            else:
                nargs = len(argspec[0]) - len(argspec[3]) # Subtract number of defaults.

            # Bound methods have an additional 'self' argument
            if isinstance(callback, types.MethodType):
                nargs -= 1
            return nargs
        else:
            raise TypeError('Callback must be callable.')


class Widget(LoggingConfigurable):
    #-------------------------------------------------------------------------
    # Class attributes
    #-------------------------------------------------------------------------
    widget_construction_callback = None
    widgets = {}

    def on_widget_constructed(callback):
        """Registers a callback to be called when a widget is constructed.  

        The callback must have the following signature:
        callback(widget)"""
        Widget.widget_construction_callback = callback

    def _call_widget_constructed(widget):
        """Class method, called when a widget is constructed."""
        if Widget.widget_construction_callback is not None and callable(Widget.widget_construction_callback):
            Widget.widget_construction_callback(widget)

    #-------------------------------------------------------------------------
    # Traits
    #-------------------------------------------------------------------------
    model_name = Unicode('WidgetModel', help="""Name of the backbone model 
        registered in the front-end to create and sync this widget with.""")
    _view_name = Unicode(help="""Default view registered in the front-end
        to use to represent the widget.""", sync=True)
    _comm = Instance('IPython.kernel.comm.Comm')

    #-------------------------------------------------------------------------
    # (Con/de)structor
    #-------------------------------------------------------------------------    
    def __init__(self, **kwargs):
        """Public constructor"""
        self.closed = False

        self._property_lock = (None, None)
        self._keys = None

        self._display_callbacks = CallbackDispatcher(acceptable_nargs=[0])
        self._msg_callbacks = CallbackDispatcher(acceptable_nargs=[1, 2])

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
    def keys(self):
        """Gets a list of the traitlets that should be synced with the front-end."""
        if self._keys is None:
            self._keys = []
            for trait_name in self.trait_names():
                if self.trait_metadata(trait_name, 'sync'):
                    self._keys.append(trait_name)
        return self._keys

    @property
    def comm(self):
        """Gets the Comm associated with this widget.

        If a Comm doesn't exist yet, a Comm will be created automagically."""
        if self._comm is None:
            # Create a comm.
            self._comm = Comm(target_name=self.model_name)
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
    def close(self):
        """Close method.  

        Closes the widget which closes the underlying comm.
        When the comm is closed, all of the widget views are automatically
        removed from the front-end."""
        if not self.closed:
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
        """(Un)Register a custom msg recieve callback.

        Parameters
        ----------
        callback: method handler
            Can have a signature of:
            - callback(content)         Signature 1
            - callback(sender, content) Signature 2
        remove: bool
            True if the callback should be unregistered."""
        self._msg_callbacks.register_callback(callback, remove=remove)

    def on_displayed(self, callback, remove=False):
        """(Un)Register a widget displayed callback.

        Parameters
        ----------
        callback: method handler
            Can have a signature of:
            - callback(sender, **kwargs)
              kwargs from display call passed through without modification.
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
    
    def _close(self):
        """Unsafe close"""
        del Widget.widgets[self.model_id]
        self._comm = None
        self.closed = True

    # Event handlers
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
        self._msg_callbacks(content) # Signature 1
        self._msg_callbacks(self, content) # Signature 2

    def _handle_property_changed(self, name, old, new):
        """Called when a property has been changed."""
        # Make sure this isn't information that the front-end just sent us.
        if self._should_send_property(name, new):
            # Send new state to front-end
            self.send_state(key=name)

    def _handle_displayed(self, **kwargs):
        """Called when a view has been displayed for this widget instance"""
        self._display_callbacks(**kwargs)

    def _pack_widgets(self, x):
        """Recursively converts all widget instances to model id strings.

        Children widgets will be stored and transmitted to the front-end by 
        their model ids.  Return value must be JSON-able."""
        if isinstance(x, dict):
            return {k: self._pack_widgets(v) for k, v in x.items()}
        elif isinstance(x, list):
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
        elif isinstance(x, list):
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
    visible = Bool(True, help="Whether or not the widget is visible.", sync=True)
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

    def set_css(self, *args, **kwargs):
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
        value
            CSS value
        selector: unicode (optional)
            JQuery selector to use to apply the CSS key/value.  If no selector 
            is provided, an empty selector is used.  An empty selector makes the 
            front-end try to apply the css to a default element.  The default
            element is an attribute unique to each view, which is a DOM element
            of the view that should be styled with common CSS (see 
            `$el_to_style` in the Javascript code).
        """
        selector = kwargs.get('selector', '')
        if not selector in self._css:
            self._css[selector] = {}
            
        # Signature 1: set_css(css_dict, selector='')
        if len(args) == 1:
            if isinstance(args[0], dict):
                for (key, value) in args[0].items():
                    if not (key in self._css[selector] and value == self._css[selector][key]):
                        self._css[selector][key] = value
                self.send_state('_css')
            else:
                raise Exception('css_dict must be a dict.')

        # Signature 2: set_css(key, value, selector='')
        elif len(args) == 2 or len(args) == 3:

            # Selector can be a positional arg if it's the 3rd value
            if len(args) == 3:
                selector = args[2]
            if selector not in self._css:
                self._css[selector] = {}

            # Only update the property if it has changed.
            key = args[0]
            value = args[1]
            if not (key in self._css[selector] and value == self._css[selector][key]):
                self._css[selector][key] = value
                self.send_state('_css') # Send new state to client.
        else:
            raise Exception('set_css only accepts 1-3 arguments')

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
        if isinstance(class_list, list):
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
        if isinstance(class_list, list):
            class_list = ' '.join(class_list)

        self.send({
            "msg_type"   : "remove_class",
            "class_list" : class_list,
            "selector"   : selector,
        })

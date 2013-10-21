import inspect
import types

from base import Widget
from IPython.utils.traitlets import Unicode, Bool, Int

class ButtonWidget(Widget):
    target_name = Unicode('ButtonWidgetModel')
    default_view_name = Unicode('ButtonView')
    _keys = ['clicks', 'description', 'disabled']
    
    clicks = Int(0)
    description = Unicode('') # Description of the button (label).
    disabled = Bool(False) # Enable or disable user changes
    
    _click_handlers = []


    def on_click(self, callback, remove=False):
        if remove:
            self._click_handlers.remove(callback)
        else:
            self._click_handlers.append(callback)


    def _clicks_changed(self, name, old, new):
        if new > old:
            for handler in self._click_handlers:
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
                    else:
                        raise TypeError('ButtonWidget click callback must ' \
                            'accept 0 or 1 arguments.')


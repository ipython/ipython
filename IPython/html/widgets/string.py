from base import Widget
from IPython.utils.traitlets import Unicode, Bool, List

class StringWidget(Widget):
    target_name = Unicode('StringWidgetModel')
    default_view_name = Unicode('TextboxView')
    _keys = ['value', 'disabled']
    
    value = Unicode()
    disabled = Bool(False) # Enable or disable user changes
    
import os

from ..widget import Widget
from IPython.utils.traitlets import Unicode, Bool
from IPython.utils.javascript import display_all_js

class StringWidget(Widget):
    target_name = Unicode('StringWidgetModel')
    default_view_name = Unicode('TextboxView')
    _keys = ['value', 'row_count', 'disabled']
    
    value = Unicode()
    disabled = Bool(False) # Enable or disable user changes
    